"""Enhanced queue manager with prioritization and health monitoring."""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func

from backend.app.database.session import SessionLocal
from backend.app.models import ApplicationQueue, Job


class QueueManager:
    """Manage application queue with intelligent prioritization."""

    def __init__(self):
        """Initialize queue manager."""
        self.db = SessionLocal()

    def add_to_queue(
        self,
        job_id: int,
        match_score: Optional[float] = None,
        priority: int = 0,
    ) -> bool:
        """
        Add job to application queue.

        Args:
            job_id: Job database ID
            match_score: AI match score (0-1)
            priority: Manual priority (higher = sooner)

        Returns:
            True if added, False if already exists
        """
        try:
            # Check if already queued
            existing = (
                self.db.query(ApplicationQueue)
                .filter(ApplicationQueue.job_id == job_id)
                .first()
            )

            if existing:
                return False

            queue_item = ApplicationQueue(
                job_id=job_id,
                match_score=match_score,
                priority=priority,
                status="queued",
            )

            self.db.add(queue_item)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    def get_next_batch(
        self,
        batch_size: int = 10,
        platforms: Optional[List[str]] = None,
    ) -> List[ApplicationQueue]:
        """
        Get next batch of jobs to process with intelligent prioritization.

        Prioritization logic:
        1. Manual priority (highest first)
        2. Match score (highest first)
        3. Age (older first)
        4. Platform distribution (balanced)

        Args:
            batch_size: Number of jobs to retrieve
            platforms: Filter by specific platforms

        Returns:
            List of queue items
        """
        query = (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .join(Job)
        )

        if platforms:
            query = query.filter(Job.platform.in_(platforms))

        # Order by priority, match score, age
        query = query.order_by(
            ApplicationQueue.priority.desc(),
            ApplicationQueue.match_score.desc().nullslast(),
            ApplicationQueue.added_at.asc(),
        )

        items = query.limit(batch_size * 2).all()  # Get 2x for distribution

        # Balance platform distribution
        if len(items) > batch_size:
            items = self._balance_platform_distribution(items, batch_size)

        return items[:batch_size]

    def _balance_platform_distribution(
        self, items: List[ApplicationQueue], target_size: int
    ) -> List[ApplicationQueue]:
        """
        Balance jobs across platforms to avoid rate limiting one platform.

        Args:
            items: Available queue items
            target_size: Desired batch size

        Returns:
            Balanced list of queue items
        """
        # Get job platform for each item
        platform_buckets = {}

        for item in items:
            job = self.db.query(Job).filter(Job.id == item.job_id).first()
            if job:
                platform = job.platform
                if platform not in platform_buckets:
                    platform_buckets[platform] = []
                platform_buckets[platform].append(item)

        # Round-robin selection
        result = []
        platforms = list(platform_buckets.keys())
        idx = 0

        while len(result) < target_size and any(platform_buckets.values()):
            platform = platforms[idx % len(platforms)]

            if platform_buckets[platform]:
                result.append(platform_buckets[platform].pop(0))

            idx += 1

            # Remove empty buckets
            if platform in platform_buckets and not platform_buckets[platform]:
                del platform_buckets[platform]
                platforms.remove(platform)

        return result

    def update_status(
        self,
        queue_id: int,
        status: str,
        processed_at: Optional[datetime] = None,
    ):
        """
        Update queue item status.

        Args:
            queue_id: Queue item ID
            status: New status
            processed_at: Processing timestamp
        """
        item = (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.id == queue_id)
            .first()
        )

        if item:
            item.status = status
            if processed_at:
                item.processed_at = processed_at
            self.db.commit()

    def get_queue_health(self) -> dict:
        """
        Get queue health metrics.

        Returns:
            Dictionary with health metrics
        """
        total_queued = (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .count()
        )

        processing = (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "processing")
            .count()
        )

        completed_today = (
            self.db.query(ApplicationQueue)
            .filter(
                ApplicationQueue.status == "completed",
                ApplicationQueue.processed_at
                >= datetime.utcnow() - timedelta(days=1),
            )
            .count()
        )

        failed_today = (
            self.db.query(ApplicationQueue)
            .filter(
                ApplicationQueue.status == "failed",
                ApplicationQueue.processed_at
                >= datetime.utcnow() - timedelta(days=1),
            )
            .count()
        )

        # Oldest queued job
        oldest = (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .order_by(ApplicationQueue.added_at.asc())
            .first()
        )

        oldest_age_hours = None
        if oldest:
            age = datetime.utcnow() - oldest.added_at
            oldest_age_hours = age.total_seconds() / 3600

        # Platform distribution
        platform_dist = (
            self.db.query(Job.platform, func.count(ApplicationQueue.id))
            .join(ApplicationQueue)
            .filter(ApplicationQueue.status == "queued")
            .group_by(Job.platform)
            .all()
        )

        return {
            "total_queued": total_queued,
            "processing": processing,
            "completed_today": completed_today,
            "failed_today": failed_today,
            "oldest_age_hours": round(oldest_age_hours, 1) if oldest_age_hours else None,
            "platform_distribution": {platform: count for platform, count in platform_dist},
            "health_status": self._calculate_health_status(
                total_queued, oldest_age_hours, failed_today, completed_today
            ),
        }

    def _calculate_health_status(
        self,
        total_queued: int,
        oldest_age_hours: Optional[float],
        failed_today: int,
        completed_today: int,
    ) -> str:
        """Calculate overall queue health status."""
        # Too many queued
        if total_queued > 500:
            return "OVERLOADED"

        # Jobs getting stale
        if oldest_age_hours and oldest_age_hours > 48:
            return "STALE"

        # High failure rate
        if completed_today > 0:
            failure_rate = failed_today / (failed_today + completed_today)
            if failure_rate > 0.5:
                return "HIGH_FAILURES"

        # Everything normal
        if total_queued > 0:
            return "HEALTHY"

        return "EMPTY"

    def cleanup_old_items(self, days: int = 30):
        """
        Remove completed/failed items older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of items deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db.query(ApplicationQueue)
            .filter(
                ApplicationQueue.status.in_(["completed", "failed"]),
                ApplicationQueue.processed_at < cutoff,
            )
            .delete()
        )

        self.db.commit()
        return deleted

    def prioritize_jobs(self, job_ids: List[int], priority: int):
        """
        Set priority for specific jobs.

        Args:
            job_ids: List of job IDs to prioritize
            priority: Priority value (higher = sooner)
        """
        (
            self.db.query(ApplicationQueue)
            .filter(ApplicationQueue.job_id.in_(job_ids))
            .update({"priority": priority}, synchronize_session=False)
        )
        self.db.commit()

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
