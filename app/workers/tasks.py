"""
Background task processing stubs.

This module provides the architecture for async task processing.
Currently uses FastAPI BackgroundTasks; designed for migration to Celery.

Production migration path:
    1. Install Celery + Redis/RabbitMQ
    2. Replace function calls with .delay() invocations
    3. Run worker: celery -A app.workers.tasks worker --loglevel=info
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import Call, Segment, Transcript
from app.services.coachable_service import CoachableDetectionService
from app.services.sentiment_service import SentimentResult, SentimentService
from app.services.stt_service import STTService, TranscriptionResult

logger = get_logger(__name__)


def process_transcription(
    call_id: str,
    audio_path: str,
    db: Session,
    stt_service: STTService,
    sentiment_service: Optional[SentimentService] = None,
    coachable_service: Optional[CoachableDetectionService] = None,
    sentiment_enabled: bool = True,
) -> TranscriptionResult:
    """
    Full transcription pipeline: STT → Sentiment → Coachable Detection → DB persist.

    In a Celery-based setup, this function becomes the task body:
        @celery_app.task(bind=True, max_retries=3)
        def process_transcription_task(self, call_id, audio_path):
            ...

    Args:
        call_id: Call identifier.
        audio_path: Path to audio file.
        db: Database session.
        stt_service: Speech-to-text service.
        sentiment_service: Optional sentiment analysis service.
        coachable_service: Optional coachable detection service.
        sentiment_enabled: Whether to run sentiment analysis.

    Returns:
        TranscriptionResult from STT.
    """
    # Update call status
    call = db.query(Call).filter(Call.call_id == call_id).first()
    if call:
        call.status = "processing"
        db.commit()

    try:
        # ── Step 1: Transcribe ───────────────────────────────────────
        result = stt_service.transcribe(audio_path)
        logger.info(f"[{call_id}] Transcription complete: {len(result.segments)} segments")

        # ── Step 2: Sentiment Analysis ───────────────────────────────
        sentiment_results: list[Optional[SentimentResult]] = []
        if sentiment_enabled and sentiment_service and result.segments:
            try:
                texts = [seg.text for seg in result.segments]
                sentiment_results = sentiment_service.analyze_batch(texts)
                logger.info(f"[{call_id}] Sentiment analysis complete")
            except Exception as e:
                logger.warning(f"[{call_id}] Sentiment analysis failed (non-fatal): {e}")
                sentiment_results = [None] * len(result.segments)
        else:
            sentiment_results = [None] * len(result.segments)

        # ── Step 3: Coachable Moment Detection ───────────────────────
        coachable_moments = []
        if coachable_service and result.segments:
            try:
                sentiment_dicts = [
                    {"label": s.label, "score": s.score} if s else None
                    for s in sentiment_results
                ]
                coachable_moments = coachable_service.detect(result.segments, sentiment_dicts)
                logger.info(f"[{call_id}] Coachable moments: {len(coachable_moments)}")
            except Exception as e:
                logger.warning(f"[{call_id}] Coachable detection failed (non-fatal): {e}")

        # ── Step 4: Persist to Database ──────────────────────────────
        _persist_results(
            db=db,
            call_id=call_id,
            result=result,
            sentiment_results=sentiment_results,
            coachable_moments=coachable_moments,
        )

        # Update call status
        if call:
            call.status = "completed"
            db.commit()

        return result

    except Exception as e:
        logger.error(f"[{call_id}] Processing failed: {e}", exc_info=True)
        if call:
            call.status = "failed"
            db.commit()
        raise


def _persist_results(
    db: Session,
    call_id: str,
    result: TranscriptionResult,
    sentiment_results: list[Optional[SentimentResult]],
    coachable_moments: list,
) -> None:
    """Persist transcription results to the database."""
    # Build coachable index for quick lookup
    coachable_index = {m.segment_index: m for m in coachable_moments}

    # Save transcript
    transcript = Transcript(
        call_id=call_id,
        full_text=result.full_text,
        language=result.language,
        duration_seconds=result.duration_seconds,
    )
    db.add(transcript)

    # Save segments
    for i, seg in enumerate(result.segments):
        sentiment = sentiment_results[i] if i < len(sentiment_results) else None
        coachable = coachable_index.get(i)

        segment = Segment(
            call_id=call_id,
            speaker=seg.speaker,
            start_time=seg.start_time,
            end_time=seg.end_time,
            text=seg.text,
            sentiment=sentiment.label if sentiment else None,
            sentiment_score=sentiment.score if sentiment else None,
            is_coachable=1 if coachable else 0,
            coachable_type=coachable.coachable_type if coachable else None,
        )
        db.add(segment)

    db.commit()
    logger.info(f"[{call_id}] Results persisted: transcript + {len(result.segments)} segments")
