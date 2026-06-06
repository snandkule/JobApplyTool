"""Application configuration settings."""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Job Apply Tool"
    app_version: str = "0.1.0"
    debug: bool = False

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    resumes_dir: Path = data_dir / "resumes"
    cover_letters_dir: Path = data_dir / "cover_letters"
    screenshots_dir: Path = data_dir / "screenshots"

    # Database
    database_url: str = Field(
        default="sqlite:///./data/job_apply.db",
        description="Database connection URL",
    )

    # Rate Limits
    linkedin_max_per_hour: int = 10
    linkedin_max_per_day: int = 50
    linkedin_delay_min: int = 120  # seconds
    linkedin_delay_max: int = 300  # seconds

    indeed_max_per_hour: int = 20
    indeed_max_per_day: int = 100
    indeed_delay_min: int = 60  # seconds
    indeed_delay_max: int = 180  # seconds

    # AI Configuration
    claude_cli_path: str = "claude"  # Path to Claude Code CLI executable

    # Browser Configuration
    browser_headless: bool = True
    browser_timeout: int = 30000  # milliseconds

    # Security
    encryption_key: Optional[str] = Field(
        default=None,
        description="Encryption key for storing credentials",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        for directory in [
            self.data_dir,
            self.resumes_dir,
            self.cover_letters_dir,
            self.screenshots_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
