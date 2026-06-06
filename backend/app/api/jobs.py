"""Job management API endpoints."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.database.session import SessionLocal
from backend.app.models import ApplicationQueue, Job

router = APIRouter()


class JobResponse(BaseModel):
    id: int
    platform: str
    company: str
    title: str
    location: Optional[str]
    job_url: str
    description: Optional[str]
    requirements: Optional[str]
    salary_range: Optional[str]
    posted_date: Optional[datetime]
    status: str
    match_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    query: str
    platform: Optional[str] = None
    location: Optional[str] = None
    remote: bool = False


class AddToQueueRequest(BaseModel):
    job_id: int
    priority: int = 5


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    """List jobs with filters."""
    db = SessionLocal()
    try:
        query = db.query(Job)

        if status:
            query = query.filter(Job.status == status)

        if platform:
            query = query.filter(Job.platform == platform)

        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
        return jobs
    finally:
        db.close()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """Get job details."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    finally:
        db.close()


@router.post("/search")
async def search_jobs(request: JobSearchRequest):
    """Search for jobs (placeholder - actual scraping done in CLI)."""
    return {
        "message": "Job search initiated",
        "query": request.query,
        "note": "Use CLI 'job-apply jobs search' for actual job scraping",
    }


@router.post("/queue/add")
async def add_to_queue(request: AddToQueueRequest):
    """Add job to application queue."""
    db = SessionLocal()
    try:
        # Check if job exists
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if already in queue
        existing = (
            db.query(ApplicationQueue)
            .filter(
                ApplicationQueue.job_id == request.job_id,
                ApplicationQueue.status == "queued",
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="Job already in queue")

        # Add to queue
        queue_item = ApplicationQueue(
            job_id=request.job_id,
            priority=request.priority,
            match_score=job.match_score,
            status="queued",
        )
        db.add(queue_item)
        db.commit()

        return {"message": "Job added to queue", "queue_id": queue_item.id}
    finally:
        db.close()


@router.get("/queue/list")
async def list_queue(
    status: str = Query("queued"),
    limit: int = Query(50),
):
    """List application queue."""
    db = SessionLocal()
    try:
        items = (
            db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == status)
            .order_by(
                ApplicationQueue.priority.desc(),
                ApplicationQueue.added_at.asc(),
            )
            .limit(limit)
            .all()
        )

        result = []
        for item in items:
            job = db.query(Job).filter(Job.id == item.job_id).first()
            if job:
                result.append({
                    "queue_id": item.id,
                    "job_id": item.job_id,
                    "priority": item.priority,
                    "match_score": item.match_score,
                    "status": item.status,
                    "added_at": item.added_at,
                    "job": {
                        "company": job.company,
                        "title": job.title,
                        "location": job.location,
                        "platform": job.platform,
                    },
                })

        return result
    finally:
        db.close()


@router.delete("/queue/{queue_id}")
async def remove_from_queue(queue_id: int):
    """Remove job from queue."""
    db = SessionLocal()
    try:
        item = db.query(ApplicationQueue).filter(ApplicationQueue.id == queue_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Queue item not found")

        db.delete(item)
        db.commit()

        return {"message": "Job removed from queue"}
    finally:
        db.close()
