"""
API integration tests.

Tests the FastAPI endpoints using TestClient with mocked ML services.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.models import Base, Call, Segment, Transcript
from app.db.session import get_db
from app.main import app


# ── Test DB Setup ────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use StaticPool + check_same_thread=False to avoid SQLite threading issues
# with FastAPI's async TestClient
test_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    """Override DB dependency for tests."""
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


# ── Health Check ─────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_check(self):
        """Health endpoint returns 200 with status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


# ── Transcribe Endpoint ─────────────────────────────────────────────────

class TestTranscribeEndpoint:

    @patch("app.api.routes.get_stt_service")
    @patch("app.api.routes.get_sentiment_service")
    @patch("app.api.routes.get_coachable_service")
    def test_transcribe_success(self, mock_coachable, mock_sentiment, mock_stt, temp_audio_file):
        """Successful transcription returns structured JSON."""
        from app.services.stt_service import TranscriptionResult, TranscriptionSegment

        # Mock STT
        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = TranscriptionResult(
            full_text="Hello, I'm interested in your product.",
            segments=[
                TranscriptionSegment(speaker="speaker_0", start_time=0.0, end_time=3.0, text="Hello, I'm interested in your product."),
            ],
            language="en",
            duration_seconds=3.0,
        )
        mock_stt.return_value = mock_stt_instance

        # Mock Sentiment (disabled path)
        mock_sentiment.return_value = None

        # Mock Coachable
        mock_coachable_instance = MagicMock()
        mock_coachable_instance.detect.return_value = []
        mock_coachable.return_value = mock_coachable_instance

        with open(temp_audio_file, "rb") as f:
            response = client.post(
                "/transcribe",
                files={"audio": ("test.wav", f, "audio/wav")},
                data={"agent_id": "agent_001", "customer_id": "cust_001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "call_id" in data
        assert data["status"] == "completed"
        assert "transcript" in data
        assert "segments" in data

    def test_transcribe_no_file(self):
        """Missing audio file returns 422."""
        response = client.post("/transcribe")
        assert response.status_code == 422


# ── Speak Endpoint ───────────────────────────────────────────────────────

class TestSpeakEndpoint:

    @patch("app.api.routes.get_tts_service")
    def test_speak_success(self, mock_tts, tmp_path):
        """Successful TTS returns audio file."""
        # Create a dummy audio file
        dummy_audio = tmp_path / "test_output.mp3"
        dummy_audio.write_bytes(b"\x00" * 100)

        mock_tts_instance = MagicMock()
        mock_tts_instance.synthesize.return_value = str(dummy_audio)
        mock_tts.return_value = mock_tts_instance

        response = client.post(
            "/speak",
            json={"text": "Hello, this is a test."},
        )

        assert response.status_code == 200
        assert "audio" in response.headers.get("content-type", "")

    def test_speak_empty_text(self):
        """Empty text returns 422 validation error."""
        response = client.post(
            "/speak",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_speak_invalid_json(self):
        """Invalid JSON body returns 422."""
        response = client.post(
            "/speak",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


# ── Replay Endpoint ─────────────────────────────────────────────────────

class TestReplayEndpoint:

    def test_replay_call_not_found(self):
        """Non-existent call returns 404."""
        response = client.post(
            "/replay",
            json={"call_id": "nonexistent_id"},
        )
        assert response.status_code == 404

    @patch("app.api.routes.get_tts_service")
    def test_replay_with_coachable_segments(self, mock_tts, tmp_path):
        """Replay with coachable segments returns audio."""
        # Seed test data
        db = TestSession()
        call = Call(call_id="test_replay_001", status="completed")
        db.add(call)
        db.flush()

        transcript = Transcript(
            call_id="test_replay_001",
            full_text="Test transcript",
        )
        db.add(transcript)

        segment = Segment(
            call_id="test_replay_001",
            speaker="speaker_0",
            start_time=0.0,
            end_time=3.0,
            text="That's too expensive for us",
            is_coachable=1,
            coachable_type="objection",
            sentiment="NEGATIVE",
        )
        db.add(segment)
        db.commit()
        db.close()

        # Mock TTS
        dummy_audio = tmp_path / "replay.mp3"
        dummy_audio.write_bytes(b"\x00" * 100)
        mock_tts_instance = MagicMock()
        mock_tts_instance.synthesize.return_value = str(dummy_audio)
        mock_tts.return_value = mock_tts_instance

        response = client.post(
            "/replay",
            json={"call_id": "test_replay_001"},
        )

        assert response.status_code == 200

    def test_replay_no_coachable_segments(self):
        """Call with no coachable moments returns 404."""
        db = TestSession()
        call = Call(call_id="test_no_coach", status="completed")
        db.add(call)
        db.commit()
        db.close()

        response = client.post(
            "/replay",
            json={"call_id": "test_no_coach"},
        )
        assert response.status_code == 404
