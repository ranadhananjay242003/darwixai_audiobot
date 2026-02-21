"""
Pytest configuration and shared fixtures.
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a fresh database session per test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing."""
    # Create a minimal WAV file (44-byte header + silence)
    wav_header = bytearray(44)
    wav_header[0:4] = b"RIFF"
    wav_header[8:12] = b"WAVE"
    wav_header[12:16] = b"fmt "
    wav_header[16:20] = (16).to_bytes(4, "little")  # chunk size
    wav_header[20:22] = (1).to_bytes(2, "little")   # PCM
    wav_header[22:24] = (1).to_bytes(2, "little")   # mono
    wav_header[24:28] = (16000).to_bytes(4, "little")  # sample rate
    wav_header[28:32] = (32000).to_bytes(4, "little")  # byte rate
    wav_header[32:34] = (2).to_bytes(2, "little")     # block align
    wav_header[34:36] = (16).to_bytes(2, "little")    # bits per sample
    wav_header[36:40] = b"data"

    # Add 1 second of silence (16000 samples * 2 bytes)
    silence = bytes(32000)
    data_size = len(silence)
    wav_header[40:44] = data_size.to_bytes(4, "little")
    file_size = len(wav_header) + data_size - 8
    wav_header[4:8] = file_size.to_bytes(4, "little")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(bytes(wav_header) + silence)
        path = f.name

    yield path
    os.unlink(path)
