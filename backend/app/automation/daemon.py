"""Daemon process for continuous job discovery and application."""
import asyncio
import os
import signal
import time
from datetime import datetime
from typing import Optional

from backend.app.automation.batch_processor import BatchProcessor
from backend.app.automation.browser import BrowserManager
from backend.app.automation.queue_manager import QueueManager
from backend.app.automation.scrapers.indeed_scraper import IndeedScraper
from backend.app.automation.scrapers.linkedin_scraper import LinkedInScraper
from backend.app.database.session import SessionLocal
from backend.app.models import DaemonConfig, DaemonState, UserProfile
from backend.app.services.logger import DaemonLogger


class JobApplicationDaemon:
    """Continuous background daemon for job discovery and applications."""

    def __init__(self, config_id: int):
        """
        Initialize daemon with configuration.

        Args:
            config_id: DaemonConfig database ID
        """
        self.config_id = config_id
        self.config = None
        self.logger = DaemonLogger(config_id)
        self.queue_manager = QueueManager()
        self.running = False
        self.should_stop = False

        # Load configuration
        self._load_config()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _load_config(self):
        """Load daemon configuration from database."""
        db = SessionLocal()
        try:
            self.config = (
                db.query(DaemonConfig)
                .filter(DaemonConfig.id == self.config_id)
                .first()
            )

            if not self.config:
                raise ValueError(f"Daemon config {self.config_id} not found")

        finally:
            db.close()

    def _signal_handler(self, signum, frame):
        """Handle termination signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.should_stop = True

    async def start(self):
        """Start the daemon main loop."""
        self.logger.info(
            f"Starting daemon for config: {self.config.name}",
            {
                "keywords": self.config.keywords,
                "platforms": self.config.platforms,
                "max_daily": self.config.max_applications_per_day,
            },
        )

        self.running = True
        self._update_state(is_running=True, pid=os.getpid())

        try:
            while not self.should_stop:
                # Run one cycle
                await self._run_cycle()

                # Heartbeat
                self._update_heartbeat()

                # Wait before next cycle
                wait_seconds = self.config.check_interval_minutes * 60
                self.logger.info(
                    f"Cycle complete. Waiting {self.config.check_interval_minutes} minutes..."
                )

                # Sleep in small chunks to respond to stop signal quickly
                for _ in range(wait_seconds):
                    if self.should_stop:
                        break
                    await asyncio.sleep(1)

        except Exception as e:
            self.logger.log_error_with_traceback(e, "daemon main loop")
            raise

        finally:
            self.running = False
            self._update_state(is_running=False, pid=None)
            self.logger.info("Daemon stopped")

    async def _run_cycle(self):
        """Run one complete discovery and application cycle."""
        cycle_start = time.time()

        self.logger.info("Starting discovery cycle...")

        try:
            # Step 1: Discover new jobs
            jobs_discovered = await self._discover_jobs()

            # Step 2: Process application queue
            await self._process_applications()

            # Step 3: Queue health check
            health = self.queue_manager.get_queue_health()
            self.logger.info("Queue health check", health)

            duration = time.time() - cycle_start
            self.logger.info(
                f"Cycle completed in {duration:.1f}s",
                {"jobs_discovered": jobs_discovered, "duration": duration},
            )

        except Exception as e:
            self.logger.log_error_with_traceback(e, "daemon cycle")

    async def _discover_jobs(self) -> int:
        """
        Discover new jobs and add to queue.

        Returns:
            Number of new jobs discovered
        """
        browser = BrowserManager()
        await browser.start(headless=True)

        total_new_jobs = 0
        platforms = self.config.platforms.split(",")

        try:
            for platform in platforms:
                platform = platform.strip()

                if platform == "linkedin":
                    scraper = LinkedInScraper(browser)
                    await browser.create_context("linkedin")
                elif platform == "indeed":
                    scraper = IndeedScraper(browser)
                    await browser.create_context("indeed")
                else:
                    continue

                # Search jobs
                jobs = await scraper.search_jobs(
                    keywords=self.config.keywords,
                    location=self.config.location or "",
                    remote=self.config.remote_only,
                )

                # Save to database
                new_count = await scraper.save_jobs_to_db(jobs)

                # Add to queue
                for job_data in jobs:
                    # Get job from database
                    db = SessionLocal()
                    try:
                        from backend.app.models import Job

                        job = (
                            db.query(Job)
                            .filter(
                                Job.external_id == job_data["external_id"],
                                Job.platform == job_data["platform"],
                            )
                            .first()
                        )

                        if job:
                            # Add to queue if not already there
                            self.queue_manager.add_to_queue(
                                job_id=job.id,
                                match_score=job.match_score,
                            )

                    finally:
                        db.close()

                total_new_jobs += new_count
                self.logger.info(
                    f"Discovered {len(jobs)} jobs on {platform}, {new_count} new"
                )

        finally:
            await browser.close()

        self._update_state(
            total_jobs_discovered_delta=total_new_jobs,
            last_discovery_run=datetime.utcnow(),
        )

        return total_new_jobs

    async def _process_applications(self):
        """Process queued applications."""
        # Get user profile
        db = SessionLocal()
        profile = db.query(UserProfile).first()
        db.close()

        if not profile:
            self.logger.warning("No user profile found, skipping applications")
            return

        # Check daily limit
        state = self._get_state()
        if state.total_applications_today >= self.config.max_applications_per_day:
            self.logger.info(
                f"Daily limit reached ({self.config.max_applications_per_day})"
            )
            return

        # Calculate how many we can process
        remaining = self.config.max_applications_per_day - state.total_applications_today
        batch_size = min(10, remaining)

        if batch_size == 0:
            return

        self.logger.info(f"Processing batch of {batch_size} applications...")

        # Process batch
        processor = BatchProcessor()
        results = await processor.process_queue(
            user_profile_id=profile.id,
            max_applications=batch_size,
            platforms=self.config.platforms.split(","),
        )

        # Update state
        self._update_state(
            total_applications_today_delta=results["successful"]
        )

        self.logger.log_application_batch(
            total=results["total_processed"],
            successful=results["successful"],
            failed=results["failed"],
            skipped=results["skipped"],
        )

    def _update_state(
        self,
        is_running: Optional[bool] = None,
        pid: Optional[int] = None,
        total_jobs_discovered_delta: int = 0,
        total_applications_today_delta: int = 0,
        last_discovery_run: Optional[datetime] = None,
    ):
        """Update daemon state in database."""
        db = SessionLocal()

        try:
            state = db.query(DaemonState).first()

            if not state:
                state = DaemonState(id=1)
                db.add(state)

            if is_running is not None:
                state.is_running = is_running

                if is_running:
                    state.started_at = datetime.utcnow()
                    state.active_config_id = self.config_id

            if pid is not None:
                state.pid = pid

            state.total_jobs_discovered += total_jobs_discovered_delta
            state.total_applications_today += total_applications_today_delta

            if last_discovery_run:
                state.last_discovery_run = last_discovery_run

            db.commit()

        finally:
            db.close()

    def _update_heartbeat(self):
        """Update daemon heartbeat timestamp."""
        db = SessionLocal()

        try:
            state = db.query(DaemonState).first()
            if state:
                state.last_heartbeat = datetime.utcnow()
                db.commit()

        finally:
            db.close()

    def _get_state(self) -> DaemonState:
        """Get current daemon state."""
        db = SessionLocal()

        try:
            state = db.query(DaemonState).first()
            if not state:
                state = DaemonState(id=1)
                db.add(state)
                db.commit()

            return state

        finally:
            db.close()

    def stop(self):
        """Request daemon to stop."""
        self.should_stop = True


def run_daemon(config_id: int):
    """
    Run daemon with given configuration.

    Args:
        config_id: DaemonConfig ID
    """
    daemon = JobApplicationDaemon(config_id)

    # Use asyncio to run
    asyncio.run(daemon.start())
