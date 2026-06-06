"""Application management API endpoints."""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from backend.app.database.session import SessionLocal
from backend.app.models import Application, DailyStats, Job

router = APIRouter()


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    user_id: int
    status: str
    platform: str
    submitted_at: Optional[datetime]
    cover_letter_text: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class ApplicationStatsResponse(BaseModel):
    total_applications: int
    submitted: int
    pending_questions: int
    failed: int
    success_rate: float
    applications_today: int
    applications_this_week: int


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List applications with filters."""
    db = SessionLocal()
    try:
        query = db.query(Application)

        if status:
            query = query.filter(Application.status == status)

        if platform:
            query = query.filter(Application.platform == platform)

        applications = (
            query.order_by(Application.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for app in applications:
            app_dict = {
                "id": app.id,
                "job_id": app.job_id,
                "user_id": app.user_id,
                "status": app.status,
                "platform": app.platform,
                "submitted_at": app.submitted_at,
                "cover_letter_text": app.cover_letter_text,
                "error_message": app.error_message,
                "created_at": app.created_at,
            }

            # Add job details
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                app_dict["job"] = {
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "job_url": job.job_url,
                }

            result.append(app_dict)

        return result
    finally:
        db.close()


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: int):
    """Get application details."""
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Application not found")

        app_dict = {
            "id": app.id,
            "job_id": app.job_id,
            "user_id": app.user_id,
            "status": app.status,
            "platform": app.platform,
            "submitted_at": app.submitted_at,
            "cover_letter_text": app.cover_letter_text,
            "error_message": app.error_message,
            "created_at": app.created_at,
        }

        # Add job details
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if job:
            app_dict["job"] = {
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "description": job.description,
                "job_url": job.job_url,
            }

        return app_dict
    finally:
        db.close()


@router.get("/stats/overview", response_model=ApplicationStatsResponse)
async def get_stats():
    """Get application statistics."""
    db = SessionLocal()
    try:
        total = db.query(Application).count()
        submitted = (
            db.query(Application).filter(Application.status == "submitted").count()
        )
        pending_questions = (
            db.query(Application)
            .filter(Application.status == "pending_questions")
            .count()
        )
        failed = db.query(Application).filter(Application.status == "failed").count()

        success_rate = (submitted / total * 100) if total > 0 else 0

        # Today's applications
        today = datetime.utcnow().date()
        applications_today = (
            db.query(Application)
            .filter(func.date(Application.created_at) == today)
            .count()
        )

        # This week's applications
        week_ago = datetime.utcnow() - timedelta(days=7)
        applications_this_week = (
            db.query(Application).filter(Application.created_at >= week_ago).count()
        )

        return {
            "total_applications": total,
            "submitted": submitted,
            "pending_questions": pending_questions,
            "failed": failed,
            "success_rate": round(success_rate, 1),
            "applications_today": applications_today,
            "applications_this_week": applications_this_week,
        }
    finally:
        db.close()


@router.get("/stats/daily")
async def get_daily_stats(days: int = Query(30, le=90)):
    """Get daily statistics."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)

        stats = (
            db.query(DailyStats)
            .filter(DailyStats.date >= cutoff_date)
            .order_by(DailyStats.date.asc())
            .all()
        )

        return [
            {
                "date": stat.date.isoformat(),
                "applications_submitted": stat.applications_submitted,
                "applications_failed": stat.applications_failed,
                "avg_success_rate": stat.avg_success_rate or 0,
            }
            for stat in stats
        ]
    finally:
        db.close()


@router.get("/stats/by-platform")
async def get_platform_stats():
    """Get statistics by platform."""
    db = SessionLocal()
    try:
        platforms = (
            db.query(
                Application.platform,
                func.count(Application.id).label("total"),
                func.sum(
                    func.case((Application.status == "submitted", 1), else_=0)
                ).label("submitted"),
            )
            .group_by(Application.platform)
            .all()
        )

        return [
            {
                "platform": p[0],
                "total": p[1],
                "submitted": p[2],
                "success_rate": round((p[2] / p[1] * 100) if p[1] > 0 else 0, 1),
            }
            for p in platforms
        ]
    finally:
        db.close()
