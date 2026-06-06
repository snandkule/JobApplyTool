"""Logging service for daemon activities."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from backend.app.config import settings
from backend.app.database.session import SessionLocal
from backend.app.models.daemon_config import DaemonLog


class DaemonLogger:
    """Structured logger for daemon activities."""

    def __init__(self, daemon_config_id: Optional[int] = None):
        """
        Initialize daemon logger.

        Args:
            daemon_config_id: Associated daemon config ID
        """
        self.daemon_config_id = daemon_config_id
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Set up file-based logging."""
        log_dir = settings.data_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / "daemon.log"

        # Configure Python logging
        self.file_logger = logging.getLogger("daemon")
        self.file_logger.setLevel(logging.INFO)

        # File handler with rotation
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # Avoid duplicate handlers
        if not self.file_logger.handlers:
            self.file_logger.addHandler(handler)

    def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log("INFO", message, details)

    def warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log("WARNING", message, details)

    def error(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log("ERROR", message, details)

    def _log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Log message to both file and database.

        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            details: Additional details (will be JSON serialized)
        """
        # File logging
        log_method = getattr(self.file_logger, level.lower())
        log_method(message)

        if details:
            log_method(f"Details: {json.dumps(details, indent=2)}")

        # Database logging
        try:
            db = SessionLocal()
            log_entry = DaemonLog(
                daemon_config_id=self.daemon_config_id,
                level=level,
                message=message,
                details=json.dumps(details) if details else None,
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            # Don't let logging errors crash the daemon
            self.file_logger.error(f"Failed to log to database: {e}")

    def log_discovery_cycle(
        self,
        jobs_found: int,
        new_jobs: int,
        duration_seconds: float,
    ):
        """Log job discovery cycle results."""
        self.info(
            "Discovery cycle completed",
            {
                "jobs_found": jobs_found,
                "new_jobs": new_jobs,
                "duration_seconds": round(duration_seconds, 2),
            },
        )

    def log_application_batch(
        self,
        total: int,
        successful: int,
        failed: int,
        skipped: int,
    ):
        """Log application batch results."""
        self.info(
            "Application batch completed",
            {
                "total_processed": total,
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            },
        )

    def log_rate_limit_hit(self, platform: str, limit_type: str):
        """Log when rate limit is reached."""
        self.warning(
            f"Rate limit reached for {platform}",
            {"platform": platform, "limit_type": limit_type},
        )

    def log_error_with_traceback(self, error: Exception, context: str):
        """Log error with full traceback."""
        import traceback

        self.error(
            f"Error in {context}: {str(error)}",
            {"traceback": traceback.format_exc()},
        )

    @staticmethod
    def get_recent_logs(limit: int = 100, level: Optional[str] = None) -> list:
        """
        Get recent daemon logs.

        Args:
            limit: Maximum number of logs to retrieve
            level: Filter by log level

        Returns:
            List of log dictionaries
        """
        db = SessionLocal()

        try:
            query = db.query(DaemonLog).order_by(DaemonLog.timestamp.desc())

            if level:
                query = query.filter(DaemonLog.level == level)

            logs = query.limit(limit).all()

            return [
                {
                    "id": log.id,
                    "level": log.level,
                    "message": log.message,
                    "details": json.loads(log.details) if log.details else None,
                    "timestamp": log.timestamp.isoformat(),
                }
                for log in logs
            ]

        finally:
            db.close()

    @staticmethod
    def clear_old_logs(days: int = 30):
        """
        Clear logs older than specified days.

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        db = SessionLocal()

        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = (
                db.query(DaemonLog)
                .filter(DaemonLog.timestamp < cutoff)
                .delete()
            )
            db.commit()
            return deleted

        finally:
            db.close()
