"""Daemon configuration models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.session import Base


class DaemonConfig(Base):
    """Daemon configuration and preferences."""

    __tablename__ = "daemon_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Search criteria
    keywords: Mapped[str] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False)
    platforms: Mapped[str] = mapped_column(String(255), default="linkedin,indeed")  # Comma-separated

    # Limits
    max_applications_per_day: Mapped[int] = mapped_column(Integer, default=50)
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)

    # Filters
    min_match_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    experience_levels: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DaemonLog(Base):
    """Daemon activity log."""

    __tablename__ = "daemon_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    daemon_config_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    level: Mapped[str] = mapped_column(String(20), index=True)  # INFO, WARNING, ERROR
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class DaemonState(Base):
    """Current daemon state (singleton)."""

    __tablename__ = "daemon_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Process info
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Active config
    active_config_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Stats
    total_jobs_discovered: Mapped[int] = mapped_column(Integer, default=0)
    total_applications_today: Mapped[int] = mapped_column(Integer, default=0)
    last_discovery_run: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Heartbeat
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
