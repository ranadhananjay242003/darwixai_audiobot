"""
Text-to-Speech service.

Currently supports gTTS (Google Text-to-Speech) as the default provider.
Designed for easy swap to other engines (pyttsx3, Coqui, ElevenLabs, etc.).
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import TTSError
from app.core.logging import get_logger

logger = get_logger(__name__)


class TTSService:
    """
    Text-to-Speech synthesis service.

    Supports multiple providers via configuration. Default: gTTS.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def synthesize(self, text: str, language: str = "en", output_dir: str | Path | None = None) -> str:
        """
        Convert text to speech audio file.

        Args:
            text: Text content to synthesize.
            language: BCP-47 language code.
            output_dir: Directory to save output. Uses config default if None.

        Returns:
            Absolute path to the generated audio file.

        Raises:
            TTSError: If synthesis fails.
        """
        if not text or not text.strip():
            raise TTSError("Cannot synthesize empty text")

        provider = self._settings.TTS_PROVIDER
        logger.info(f"TTS synthesis requested: provider={provider}, len={len(text)}")

        try:
            if provider == "gtts":
                return self._synthesize_gtts(text, language, output_dir)
            elif provider == "pyttsx3":
                return self._synthesize_pyttsx3(text, output_dir)
            else:
                raise TTSError(f"Unsupported TTS provider: {provider}")
        except TTSError:
            raise
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}", exc_info=True)
            raise TTSError(f"TTS error: {e}") from e

    def _synthesize_gtts(self, text: str, language: str, output_dir: str | Path | None) -> str:
        """Google TTS synthesis."""
        from gtts import gTTS

        output_path = self._get_output_path(output_dir, extension=".mp3")

        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)

        logger.info(f"gTTS audio saved: {output_path}")
        return output_path

    def _synthesize_pyttsx3(self, text: str, output_dir: str | Path | None) -> str:
        """pyttsx3 local TTS synthesis."""
        import pyttsx3

        output_path = self._get_output_path(output_dir, extension=".wav")

        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, output_path)
        engine.runAndWait()

        logger.info(f"pyttsx3 audio saved: {output_path}")
        return output_path

    def _get_output_path(self, output_dir: str | Path | None, extension: str = ".mp3") -> str:
        """Generate unique output file path."""
        if output_dir is None:
            output_dir = self._settings.output_path
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"tts_{uuid.uuid4().hex[:12]}{extension}"
        return str(output_dir / filename)


# ── Module-level singleton ───────────────────────────────────────────────
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Return the singleton TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
