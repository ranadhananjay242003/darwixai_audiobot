"""
Pydantic request/response models for API validation.

Enforces strict input validation and provides typed response contracts.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Segment Schemas ──────────────────────────────────────────────────────

class SegmentResponse(BaseModel):
    """Single speaker-diarized segment in the transcript."""
    speaker: str = Field(..., description="Speaker identifier (e.g., speaker_0, speaker_1)")
    start_time: float = Field(..., ge=0, description="Segment start time in seconds")
    end_time: float = Field(..., ge=0, description="Segment end time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    sentiment: Optional[str] = Field(None, description="Sentiment label: POSITIVE, NEGATIVE, NEUTRAL")
    sentiment_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score for sentiment")
    is_coachable: bool = Field(False, description="Whether this segment is a coachable moment")
    coachable_type: Optional[str] = Field(None, description="Type: objection, buying_signal, hesitation")

    class Config:
        from_attributes = True


# ── Call List Schemas ───────────────────────────────────────────────────

class CallSummary(BaseModel):
    """Summarised call metadata for dashboard list."""
    call_id: str
    status: str
    created_at: datetime
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class CallDetail(BaseModel):
    """Detailed call analysis including segments and transcript."""
    call_id: str
    status: str
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: datetime
    transcript: Optional[str] = None
    segments: list[SegmentResponse] = []
    
    class Config:
        from_attributes = True


# ── Transcribe Schemas ───────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    """Response payload for /transcribe endpoint."""
    call_id: str
    status: str = "completed"
    transcript: str = Field(..., description="Full transcribed text")
    segments: list[SegmentResponse] = Field(default_factory=list)
    duration_seconds: Optional[float] = None
    language: Optional[str] = None

    class Config:
        from_attributes = True


# ── Speak (TTS) Schemas ─────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    """Request payload for /speak endpoint."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize to speech")
    language: str = Field("en", description="BCP-47 language code")


# ── Replay Schemas ───────────────────────────────────────────────────────

class ReplayRequest(BaseModel):
    """Request payload for /replay endpoint."""
    call_id: str = Field(..., min_length=1, description="ID of the call to replay coachable segments from")


class CoachableSegmentInfo(BaseModel):
    """Coachable moment metadata returned alongside replay."""
    speaker: str
    start_time: float
    end_time: float
    text: str
    coachable_type: Optional[str] = None
    sentiment: Optional[str] = None


class ReplayResponse(BaseModel):
    """Response metadata for /replay endpoint (audio returned separately)."""
    call_id: str
    coachable_segments: list[CoachableSegmentInfo]
    audio_generated: bool = True


# ── Health / Error Schemas ───────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standardised error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
