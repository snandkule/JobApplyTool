"""Batch processor for automated job applications."""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional

from backend.app.automation.browser import BrowserManager
from backend.app.automation.platforms.indeed import IndeedApplicator
from backend.app.automation.platforms.linkedin import LinkedInApplicator
from backend.app.config import settings
from backend.app.database.session import SessionLocal
from backend.app.models import Application, ApplicationQueue, DailyStats, Job


class BatchProcessor:
    """Process job applications in batches with rate limiting."""

    def __init__(self):
        """Initialize batch processor."""
        self.browser_manager = BrowserManager()
        self.linkedin_applicator = None
        self.indeed_applicator = None
        self._rate_limiters = {
            "linkedin": RateLimiter(
                max_per_hour=settings.linkedin_max_per_hour,
                max_per_day=settings.linkedin_max_per_day,
                delay_min=settings.linkedin_delay_min,
                delay_max=settings.linkedin_delay_max,
            ),
            "indeed": RateLimiter(
                max_per_hour=settings.indeed_max_per_hour,
                max_per_day=settings.indeed_max_per_day,
                delay_min=settings.indeed_delay_min,
                delay_max=settings.indeed_delay_max,
            ),
        }

    async def initialize(self):
        """Initialize browser and applicators."""
        await self.browser_manager.start()
        self.linkedin_applicator = LinkedInApplicator(self.browser_manager)
        self.indeed_applicator = IndeedApplicator(self.browser_manager)

    async def process_queue(
        self,
        user_profile_id: int,
        max_applications: int = 10,
        platforms: Optional[List[str]] = None,
    ) -> dict:
        """
        Process application queue in batch.

        Args:
            user_profile_id: User profile ID
            max_applications: Maximum applications to process
            platforms: List of platforms to process (None = all)

        Returns:
            Summary dictionary with results
        """
        await self.initialize()

        db = SessionLocal()
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        try:
            # Get queued jobs
            query = db.query(ApplicationQueue).filter(
                ApplicationQueue.status == "queued"
            ).order_by(ApplicationQueue.priority.desc(), ApplicationQueue.added_at)

            if platforms:
                # Join with Job to filter by platform
                query = query.join(Job).filter(Job.platform.in_(platforms))

            queue_items = query.limit(max_applications).all()

            for item in queue_items:
                job = db.query(Job).filter(Job.id == item.job_id).first()

                if not job:
                    continue

                # Check rate limits
                rate_limiter = self._rate_limiters.get(job.platform)
                if rate_limiter and not rate_limiter.can_proceed():
                    results["skipped"] += 1
                    results["details"].append({
                        "job_id": job.id,
                        "status": "skipped",
                        "reason": "Rate limit reached",
                    })
                    continue

                # Update queue item status
                item.status = "processing"
                db.commit()

                # AI preprocessing: generate cover letter if needed
                app_record = db.query(Application).filter(
                    Application.job_id == job.id,
                    Application.user_id == user_profile_id
                ).first()

                if app_record and not app_record.cover_letter_text:
                    try:
                        from backend.app.ai.ai_service import AIService
                        ai = AIService()
                        cover_letter = ai.generate_cover_letter(
                            job_id=job.id,
                            user_profile_id=user_profile_id,
                        )
                        app_record.cover_letter_text = cover_letter
                        db.commit()
                    except Exception as e:
                        print(f"AI cover letter generation failed for job {job.id}: {e}")

                # Apply to job
                try:
                    if job.platform == "linkedin":
                        result = await self.linkedin_applicator.apply_to_job(
                            job.id, user_profile_id
                        )
                    elif job.platform == "indeed":
                        result = await self.indeed_applicator.apply_to_job(
                            job.id, user_profile_id
                        )
                    else:
                        result = {"success": False, "error": "Unsupported platform"}

                    results["total_processed"] += 1

                    if result["success"]:
                        results["successful"] += 1
                        item.status = "completed"

                        # Record in rate limiter
                        if rate_limiter:
                            rate_limiter.record_application()
                    else:
                        results["failed"] += 1
                        item.status = "failed"

                    results["details"].append({
                        "job_id": job.id,
                        "job_title": job.title,
                        "company": job.company,
                        "platform": job.platform,
                        "status": "success" if result["success"] else "failed",
                        "message": result.get("message", result.get("error", "")),
                    })

                    item.processed_at = datetime.utcnow()
                    db.commit()

                    # Delay between applications
                    if rate_limiter:
                        await asyncio.sleep(rate_limiter.get_delay())

                except Exception as e:
                    results["failed"] += 1
                    results["total_processed"] += 1
                    item.status = "failed"
                    db.commit()

                    results["details"].append({
                        "job_id": job.id,
                        "status": "failed",
                        "error": str(e),
                    })

            # Update daily stats
            self._update_daily_stats(db, results)

            return results

        finally:
            db.close()
            await self.browser_manager.close()

    async def apply_to_single_job(
        self,
        job_id: int,
        user_profile_id: int,
        resume_id: Optional[int] = None,
    ) -> dict:
        """
        Apply to a single job (not from queue).

        Args:
            job_id: Job database ID
            user_profile_id: User profile ID
            resume_id: Optional resume ID

        Returns:
            Application result
        """
        await self.initialize()

        db = SessionLocal()

        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return {"success": False, "error": "Job not found"}

            # Check rate limits
            rate_limiter = self._rate_limiters.get(job.platform)
            if rate_limiter and not rate_limiter.can_proceed():
                return {
                    "success": False,
                    "error": "Rate limit reached for this platform",
                }

            # Apply based on platform
            if job.platform == "linkedin":
                result = await self.linkedin_applicator.apply_to_job(
                    job_id, user_profile_id, resume_id
                )
            elif job.platform == "indeed":
                result = await self.indeed_applicator.apply_to_job(
                    job_id, user_profile_id, resume_id
                )
            else:
                result = {"success": False, "error": "Unsupported platform"}

            # Record successful application
            if result["success"] and rate_limiter:
                rate_limiter.record_application()

            return result

        finally:
            db.close()
            await self.browser_manager.close()

    def _update_daily_stats(self, db, results: dict):
        """Update daily statistics."""
        today = datetime.utcnow().date()

        stats = db.query(DailyStats).filter(DailyStats.date == today).first()

        if not stats:
            stats = DailyStats(date=today)
            db.add(stats)

        stats.applications_submitted += results["successful"]
        stats.applications_failed += results["failed"]

        if results["total_processed"] > 0:
            stats.avg_success_rate = results["successful"] / results["total_processed"]

        db.commit()


class RateLimiter:
    """Rate limiter for platform applications."""

    def __init__(
        self,
        max_per_hour: int,
        max_per_day: int,
        delay_min: int,
        delay_max: int,
    ):
        """
        Initialize rate limiter.

        Args:
            max_per_hour: Maximum applications per hour
            max_per_day: Maximum applications per day
            delay_min: Minimum delay between applications (seconds)
            delay_max: Maximum delay between applications (seconds)
        """
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.delay_min = delay_min
        self.delay_max = delay_max
        self._hourly_applications = []
        self._daily_applications = []

    def can_proceed(self) -> bool:
        """Check if we can make another application."""
        now = datetime.utcnow()

        # Clean old entries
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        self._hourly_applications = [
            ts for ts in self._hourly_applications if ts > hour_ago
        ]
        self._daily_applications = [
            ts for ts in self._daily_applications if ts > day_ago
        ]

        # Check limits
        if len(self._hourly_applications) >= self.max_per_hour:
            return False

        if len(self._daily_applications) >= self.max_per_day:
            return False

        return True

    def record_application(self):
        """Record that an application was made."""
        now = datetime.utcnow()
        self._hourly_applications.append(now)
        self._daily_applications.append(now)

    def get_delay(self) -> int:
        """Get random delay for next application."""
        return random.randint(self.delay_min, self.delay_max)
