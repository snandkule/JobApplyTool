"""FastAPI main application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import applications, auth, daemon, jobs, profile, questions
from backend.app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI app."""
    # Startup
    print(f"Starting {settings.app_name} API server...")
    yield
    # Shutdown
    print("Shutting down API server...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered job application automation API",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(daemon.router, prefix="/api/daemon", tags=["Daemon"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions & AI"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
