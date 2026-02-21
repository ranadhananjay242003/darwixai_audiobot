"""
Speech-to-Text service using OpenAI Whisper.

Provides transcription with timestamp-based pseudo-diarization.
Designed as a pluggable service: swap to a cloud STT by implementing
the same interface.
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import AudioProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TranscriptionSegment:
    """Represents a single transcribed segment."""
    speaker: str
    start_time: float
    end_time: float
    text: str


@dataclass
class TranscriptionResult:
    """Complete transcription output."""
    full_text: str
    segments: list[TranscriptionSegment]
    language: Optional[str] = None
    duration_seconds: Optional[float] = None


class STTService:
    """
    Speech-to-Text service backed by Whisper.

    Lazily loads the model on first use to avoid startup cost
    and allow the service to be importable without GPU.
    """

    def __init__(self) -> None:
        self._model = None
        self._settings = get_settings()

    def _load_model(self):
        """Lazy-load Whisper model."""
        if self._model is not None:
            return

        try:
            import whisper  # noqa: local import for lazy loading

            model_size = self._settings.WHISPER_MODEL_SIZE
            logger.info(f"Loading Whisper model: {model_size}")
            self._model = whisper.load_model(model_size)
            logger.info(f"Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise AudioProcessingError(f"STT model initialization failed: {e}") from e

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        """
        Transcribe audio file with pseudo-diarization.

        Args:
            audio_path: Path to audio file (WAV/MP3).

        Returns:
            TranscriptionResult with full text and speaker segments.

        Raises:
            AudioProcessingError: If transcription fails.
        """
        self._load_model()
        audio_path = str(audio_path)

        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        try:
            logger.info(f"Starting transcription: {audio_path}")

            result = self._model.transcribe(
                audio_path,
                language=None,  # auto-detect
                verbose=False,
                word_timestamps=False,
            )

            full_text = result.get("text", "").strip()
            language = result.get("language", "en")
            raw_segments = result.get("segments", [])

            # Build diarized segments using timestamp-based speaker assignment
            segments = self._assign_speakers(raw_segments)

            # Estimate total duration
            duration = segments[-1].end_time if segments else 0.0

            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"{duration:.1f}s, language={language}"
            )

            return TranscriptionResult(
                full_text=full_text,
                segments=segments,
                language=language,
                duration_seconds=duration,
            )

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise AudioProcessingError(f"Transcription error: {e}") from e

    def _assign_speakers(self, raw_segments: list[dict]) -> list[TranscriptionSegment]:
        """
        Pseudo-diarization: alternate speakers based on silence gaps.

        In production, integrate pyannote-audio or a dedicated diarization
        model for real speaker separation. This heuristic alternates speakers
        when there is a gap > 1.5 seconds between segments.
        """
        if not raw_segments:
            return []

        SILENCE_GAP_THRESHOLD = 1.5  # seconds
        segments: list[TranscriptionSegment] = []
        current_speaker_idx = 0

        for i, seg in enumerate(raw_segments):
            text = seg.get("text", "").strip()
            if not text:
                continue

            start = float(seg.get("start", 0))
            end = float(seg.get("end", 0))

            # Detect speaker change via gap
            if i > 0:
                prev_end = float(raw_segments[i - 1].get("end", 0))
                if start - prev_end > SILENCE_GAP_THRESHOLD:
                    current_speaker_idx = 1 - current_speaker_idx  # toggle 0 <-> 1

            segments.append(
                TranscriptionSegment(
                    speaker=f"speaker_{current_speaker_idx}",
                    start_time=round(start, 2),
                    end_time=round(end, 2),
                    text=text,
                )
            )

        return segments

    def transcribe_bytes(self, audio_bytes: bytes, suffix: str = ".wav") -> TranscriptionResult:
        """
        Transcribe from raw bytes (convenience for API layer).

        Args:
            audio_bytes: Raw audio file content.
            suffix: File extension hint.

        Returns:
            TranscriptionResult
        """
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe(tmp_path)
        finally:
            os.unlink(tmp_path)


# ── Module-level singleton ───────────────────────────────────────────────
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Return the singleton STT service instance."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
