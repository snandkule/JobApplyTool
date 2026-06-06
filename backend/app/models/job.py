"""Job models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class Job(Base):
    """Job listing information."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    platform: Mapped[str] = mapped_column(String(50), index=True)  # linkedin, indeed, custom
    url: Mapped[str] = mapped_column(String(1000))

    # Job details
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(index=True, default=False)
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # full-time, part-time, contract
    experience_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # entry, mid, senior, lead, principal

    # Description and requirements
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Matching
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Status
    status: Mapped[str] = mapped_column(
        String(50), index=True, default="discovered"
    )  # discovered, filtered, queued, applied, rejected
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    application_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
    queue_entries: Mapped[list["ApplicationQueue"]] = relationship(
        "ApplicationQueue", back_populates="job"
    )
