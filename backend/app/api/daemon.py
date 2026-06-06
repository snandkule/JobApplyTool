"""Daemon control API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.database.session import SessionLocal
from backend.app.models import DaemonConfig, DaemonLog, DaemonState

router = APIRouter()


class DaemonStatusResponse(BaseModel):
    is_running: bool
    config_id: Optional[int]
    search_criteria: Optional[str]
    max_applications_per_day: Optional[int]
    applications_today: int
    queue_size: int
    last_cycle_at: Optional[str]


class DaemonConfigRequest(BaseModel):
    search_criteria: str
    location: Optional[str] = None
    remote: bool = False
    max_applications_per_day: int = 50
    platforms: List[str] = ["linkedin", "indeed"]
    min_match_score: float = 0.6


@router.get("/status", response_model=DaemonStatusResponse)
async def get_daemon_status():
    """Get daemon status."""
    db = SessionLocal()
    try:
        state = db.query(DaemonState).first()

        if not state:
            return {
                "is_running": False,
                "config_id": None,
                "search_criteria": None,
                "max_applications_per_day": None,
                "applications_today": 0,
                "queue_size": 0,
                "last_cycle_at": None,
            }

        config = None
        if state.config_id:
            config = (
                db.query(DaemonConfig).filter(DaemonConfig.id == state.config_id).first()
            )

        return {
            "is_running": state.is_running,
            "config_id": state.config_id,
            "search_criteria": config.search_criteria if config else None,
            "max_applications_per_day": (
                config.max_applications_per_day if config else None
            ),
            "applications_today": state.applications_today or 0,
            "queue_size": state.queue_size or 0,
            "last_cycle_at": (
                state.last_cycle_at.isoformat() if state.last_cycle_at else None
            ),
        }
    finally:
        db.close()


@router.post("/start")
async def start_daemon(config: DaemonConfigRequest):
    """Start daemon (placeholder - actual daemon runs as separate process)."""
    db = SessionLocal()
    try:
        # Create config
        daemon_config = DaemonConfig(
            search_criteria=config.search_criteria,
            location=config.location,
            remote=config.remote,
            max_applications_per_day=config.max_applications_per_day,
            platforms=",".join(config.platforms),
            min_match_score=config.min_match_score,
            is_active=True,
        )
        db.add(daemon_config)
        db.commit()

        return {
            "message": "Daemon configuration saved",
            "config_id": daemon_config.id,
            "note": "Use CLI 'job-apply daemon start' to actually start daemon process",
        }
    finally:
        db.close()


@router.post("/stop")
async def stop_daemon():
    """Stop daemon (placeholder)."""
    return {
        "message": "Daemon stop requested",
        "note": "Use CLI 'job-apply daemon stop' to actually stop daemon process",
    }


@router.get("/logs")
async def get_daemon_logs(limit: int = 100):
    """Get daemon logs."""
    db = SessionLocal()
    try:
        logs = (
            db.query(DaemonLog)
            .order_by(DaemonLog.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "details": log.details,
            }
            for log in logs
        ]
    finally:
        db.close()


@router.get("/configs")
async def list_configs():
    """List daemon configurations."""
    db = SessionLocal()
    try:
        configs = (
            db.query(DaemonConfig).order_by(DaemonConfig.created_at.desc()).all()
        )

        return [
            {
                "id": config.id,
                "search_criteria": config.search_criteria,
                "location": config.location,
                "remote": config.remote,
                "max_applications_per_day": config.max_applications_per_day,
                "platforms": config.platforms,
                "min_match_score": config.min_match_score,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat(),
            }
            for config in configs
        ]
    finally:
        db.close()
