"""
API route definitions.

This module contains ONLY route declarations and request/response handling.
All business logic is delegated to service modules and workers.
"""

import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AudioProcessingError,
    DarwixBaseError,
    TranscriptionNotFoundError,
    TTSError,
)
from app.core.logging import get_logger
from app.db.models import Call, Segment, Transcript
from app.db.session import get_db
from app.schemas.models import (
    CallDetail,
    CallSummary,
    CoachableSegmentInfo,
    ErrorResponse,
    ReplayRequest,
    ReplayResponse,
    SegmentResponse,
    SpeakRequest,
    TranscribeResponse,
)
from app.services.coachable_service import get_coachable_service
from app.services.sentiment_service import get_sentiment_service
from app.services.stt_service import get_stt_service
from app.services.tts_service import get_tts_service
from app.workers.tasks import process_transcription

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


# ── GET /calls ────────────────────────────────────────────────────────────

@router.get(
    "/calls",
    response_model=List[CallSummary],
    summary="List recent calls",
    description="Fetch a list of recent calls for the dashboard.",
)
async def list_calls(limit: int = 20, db: Session = Depends(get_db)):
    """List recent calls."""
    calls = db.query(Call).order_by(Call.created_at.desc()).limit(limit).all()
    return calls


@router.get(
    "/calls/{call_id}",
    response_model=CallDetail,
    summary="Get call details",
    description="Fetch full transcript and analysis for a specific call.",
)
async def get_call_detail(call_id: str, db: Session = Depends(get_db)):
    """Get detailed analysis for a call."""
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail=f"Call not found: {call_id}")
    
    transcript = db.query(Transcript).filter(Transcript.call_id == call_id).first()
    segments = db.query(Segment).filter(Segment.call_id == call_id).order_by(Segment.start_time).all()
    
    return CallDetail(
        call_id=call.call_id,
        status=call.status,
        agent_id=call.agent_id,
        customer_id=call.customer_id,
        created_at=call.created_at,
        transcript=transcript.full_text if transcript else None,
        segments=segments,
    )


# ── POST /transcribe ─────────────────────────────────────────────────────

@router.post(
    "/transcribe",
    # ... previous transcribe endpoint remains basically same ...
    response_model=TranscribeResponse,
    summary="Transcribe a sales-call audio clip",
)
async def transcribe(
    audio: UploadFile = File(..., description="Audio file (WAV or MP3)"),
    call_id: str = Form(default=None, description="Unique call identifier"),
    agent_id: str = Form(default="System", description="Sales agent identifier"),
    customer_id: str = Form(default="Customer", description="Customer identifier"),
    db: Session = Depends(get_db),
):
    """Transcribe audio with diarization, sentiment, and coachable detection."""

    if audio.content_type and audio.content_type not in (
        "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
        "application/octet-stream", "audio/wave",
    ):
        logger.warning(f"Likely unsupported format: {audio.content_type}")

    if not call_id:
        call_id = str(uuid.uuid4())

    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    upload_path = settings.upload_path / f"{call_id}{suffix}"

    try:
        content = await audio.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")

        with open(upload_path, "wb") as f:
            f.write(content)

        logger.info(f"Audio uploaded: {upload_path} ({len(content)} bytes)")
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

    call = Call(
        call_id=call_id,
        agent_id=agent_id,
        customer_id=customer_id,
        audio_filename=str(upload_path),
        status="pending",
    )
    db.add(call)
    db.commit()

    try:
        stt = get_stt_service()
        sentiment = get_sentiment_service() if settings.SENTIMENT_ENABLED else None
        coachable = get_coachable_service()

        result = process_transcription(
            call_id=call_id,
            audio_path=str(upload_path),
            db=db,
            stt_service=stt,
            sentiment_service=sentiment,
            coachable_service=coachable,
            sentiment_enabled=settings.SENTIMENT_ENABLED,
        )

        segments_db = db.query(Segment).filter(Segment.call_id == call_id).order_by(Segment.start_time).all()

        return TranscribeResponse(
            call_id=call_id,
            status="completed",
            transcript=result.full_text,
            segments=[SegmentResponse.from_orm(s) for s in segments_db],
            duration_seconds=result.duration_seconds,
            language=result.language,
        )

    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        call.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /speak ──────────────────────────────────────────────────────────

@router.post("/speak", summary="Synthesize text to speech")
async def speak(request: SpeakRequest):
    """Generate audio from text using TTS."""
    try:
        tts = get_tts_service()
        audio_path = tts.synthesize(text=request.text, language=request.language)
        media_type = "audio/mpeg" if audio_path.endswith(".mp3") else "audio/wav"
        return FileResponse(path=audio_path, media_type=media_type)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail="TTS failed")


# ── POST /replay ─────────────────────────────────────────────────────────

@router.post("/replay", summary="Replay coachable moments from a call")
async def replay(request: ReplayRequest, db: Session = Depends(get_db)):
    """Generate TTS replay of coachable moments for a call."""
    call = db.query(Call).filter(Call.call_id == request.call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    coachable_segments = (
        db.query(Segment)
        .filter(Segment.call_id == request.call_id, Segment.is_coachable == 1)
        .order_by(Segment.start_time)
        .all()
    )

    if not coachable_segments:
        raise HTTPException(status_code=404, detail="No coachable moments found")

    replay_parts = [f"{s.coachable_type}: {s.speaker} said: {s.text}" for s in coachable_segments]
    composite_text = ". ".join(replay_parts)

    try:
        tts = get_tts_service()
        audio_path = tts.synthesize(text=composite_text)
        return FileResponse(path=audio_path, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Replay failed: {e}")
        raise HTTPException(status_code=500, detail="Replay failed")
