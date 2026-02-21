"""
Unit tests for the STT service.

Uses mocking to avoid loading the actual Whisper model during CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.stt_service import STTService, TranscriptionResult, TranscriptionSegment


class TestSTTService:
    """Tests for STTService."""

    def setup_method(self):
        """Reset singleton for each test."""
        self.service = STTService()

    def test_assign_speakers_empty(self):
        """Empty segment list returns empty result."""
        result = self.service._assign_speakers([])
        assert result == []

    def test_assign_speakers_single_segment(self):
        """Single segment gets speaker_0."""
        raw = [{"start": 0.0, "end": 2.0, "text": "Hello there"}]
        result = self.service._assign_speakers(raw)

        assert len(result) == 1
        assert result[0].speaker == "speaker_0"
        assert result[0].text == "Hello there"
        assert result[0].start_time == 0.0
        assert result[0].end_time == 2.0

    def test_assign_speakers_alternation_on_gap(self):
        """Speaker alternates when gap > 1.5s."""
        raw = [
            {"start": 0.0, "end": 2.0, "text": "First speaker"},
            {"start": 4.0, "end": 6.0, "text": "Second speaker"},  # 2s gap
            {"start": 6.2, "end": 8.0, "text": "Still second speaker"},  # 0.2s gap
            {"start": 10.0, "end": 12.0, "text": "First speaker again"},  # 2s gap
        ]
        result = self.service._assign_speakers(raw)

        assert len(result) == 4
        assert result[0].speaker == "speaker_0"
        assert result[1].speaker == "speaker_1"  # toggled
        assert result[2].speaker == "speaker_1"  # no toggle (small gap)
        assert result[3].speaker == "speaker_0"  # toggled back

    def test_assign_speakers_skips_empty_text(self):
        """Empty text segments are filtered out."""
        raw = [
            {"start": 0.0, "end": 1.0, "text": "Valid"},
            {"start": 1.0, "end": 2.0, "text": ""},
            {"start": 2.0, "end": 3.0, "text": "   "},
            {"start": 3.0, "end": 4.0, "text": "Also valid"},
        ]
        result = self.service._assign_speakers(raw)

        assert len(result) == 2
        assert result[0].text == "Valid"
        assert result[1].text == "Also valid"

    def test_transcribe_success(self, temp_audio_file):
        """Successful transcription returns structured result."""
        # Directly set the mock model on the service instance
        # (whisper is imported locally inside _load_model, so we mock the model object)
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello, how can I help you today?",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "Hello, how can I help you today?"},
            ],
        }
        self.service._model = mock_model

        result = self.service.transcribe(temp_audio_file)

        assert isinstance(result, TranscriptionResult)
        assert result.full_text == "Hello, how can I help you today?"
        assert result.language == "en"
        assert len(result.segments) == 1

    def test_transcribe_file_not_found(self):
        """Non-existent file raises AudioProcessingError."""
        from app.core.exceptions import AudioProcessingError

        self.service._model = MagicMock()  # skip model loading

        with pytest.raises(AudioProcessingError, match="not found"):
            self.service.transcribe("/nonexistent/audio.wav")

    def test_transcribe_bytes(self):
        """transcribe_bytes writes temp file and processes it."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test audio",
            "language": "en",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Test audio"}],
        }
        self.service._model = mock_model

        # Create minimal audio bytes
        audio_bytes = b"RIFF" + b"\x00" * 40

        # This will fail on actual Whisper but our mock doesn't care
        result = self.service.transcribe_bytes(audio_bytes)
        assert result.full_text == "Test audio"
