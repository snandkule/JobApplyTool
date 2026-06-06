"""Authentication API endpoints (placeholder)."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login(platform: str):
    """
    Platform login (placeholder).

    Actual authentication happens via CLI with browser automation.
    """
    return {
        "message": f"Login to {platform} via CLI",
        "command": f"job-apply auth {platform}",
    }


@router.get("/status")
async def auth_status():
    """Check authentication status."""
    return {
        "linkedin": "unknown",
        "indeed": "unknown",
        "note": "Session status tracked in browser automation",
    }
