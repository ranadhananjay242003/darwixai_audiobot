"""
SQLAlchemy ORM models for the Darwix AI system.

Tables:
    - calls: Top-level call metadata
    - transcripts: Full transcript text per call
    - segments: Speaker-diarized segments with optional sentiment
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


class Call(Base):
    """Represents a single sales-call submission."""

    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(128), nullable=True)
    customer_id = Column(String(128), nullable=True)
    audio_filename = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, default="pending")  # pending | processing | completed | failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    transcript = relationship("Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="call", cascade="all, delete-orphan", order_by="Segment.start_time")

    def __repr__(self) -> str:
        return f"<Call(call_id={self.call_id}, status={self.status})>"


class Transcript(Base):
    """Full-text transcript associated with a call."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), ForeignKey("calls.call_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_text = Column(Text, nullable=False)
    language = Column(String(10), nullable=True, default="en")
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    call = relationship("Call", back_populates="transcript")

    def __repr__(self) -> str:
        return f"<Transcript(call_id={self.call_id}, len={len(self.full_text) if self.full_text else 0})>"


class Segment(Base):
    """Individual speaker-diarized segment within a call."""

    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(64), ForeignKey("calls.call_id", ondelete="CASCADE"), nullable=False, index=True)
    speaker = Column(String(64), nullable=False, default="unknown")
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    sentiment = Column(String(32), nullable=True)  # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score = Column(Float, nullable=True)
    is_coachable = Column(Integer, nullable=False, default=0)  # 0=False, 1=True (SQLite compat)
    coachable_type = Column(String(64), nullable=True)  # objection | buying_signal | hesitation
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    call = relationship("Call", back_populates="segments")

    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_segments_call_speaker", "call_id", "speaker"),
    )

    def __repr__(self) -> str:
        return f"<Segment(call_id={self.call_id}, speaker={self.speaker}, {self.start_time}-{self.end_time})>"
