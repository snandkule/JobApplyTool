"""Application and queue models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class Application(Base):
    """Job application tracking."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_profiles.id"), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), index=True, default="queued"
    )  # queued, processing, pending_questions, submitted, failed, rejected

    # Platform details
    platform: Mapped[str] = mapped_column(String(50))
    platform_application_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Submission details
    resume_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_letter_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    custom_answers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Tracking
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Response tracking
    response_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    response_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # interview, rejection, offer, other
    response_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    pending_questions: Mapped[list["PendingQuestion"]] = relationship(
        "PendingQuestion", back_populates="application"
    )


class ApplicationQueue(Base):
    """Application queue for batch processing."""

    __tablename__ = "application_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), index=True, default="queued"
    )  # queued, processing, completed, failed

    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="queue_entries")


class PendingQuestion(Base):
    """Pending questions that need user answers."""

    __tablename__ = "pending_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)

    # Question details
    question_text: Mapped[str] = mapped_column(Text)
    field_type: Mapped[str] = mapped_column(
        String(50)
    )  # text, dropdown, number, yes_no, multiline
    field_selector: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Answer
    status: Mapped[str] = mapped_column(
        String(50), index=True, default="pending"
    )  # pending, answered, skipped
    user_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="pending_questions"
    )


class KnowledgeBase(Base):
    """Knowledge base for reusable answers."""

    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_normalized: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    question_patterns: Mapped[str] = mapped_column(Text)  # JSON array
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reuse policy
    reuse_policy: Mapped[str] = mapped_column(
        String(50), default="always_same"
    )  # always_same, context_dependent, always_ask
    context_factors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyStats(Base):
    """Daily application statistics."""

    __tablename__ = "daily_stats"

    date: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    applications_submitted: Mapped[int] = mapped_column(Integer, default=0)
    applications_failed: Mapped[int] = mapped_column(Integer, default=0)
    applications_pending: Mapped[int] = mapped_column(Integer, default=0)
    questions_asked: Mapped[int] = mapped_column(Integer, default=0)
    questions_answered: Mapped[int] = mapped_column(Integer, default=0)
    platforms_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    avg_success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
