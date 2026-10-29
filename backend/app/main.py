"""
CVlect AI — FastAPI Application Main Entry Point
Configures CORS, registers modular API routers, manages database lifecycle,
and serves health check / documentation endpoints.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import (
    auth,
    resumes,
    jobs,
    matching,
    applications,
    analytics,
    assistant,
    saved_jobs,
)
from app.utils import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("=" * 60)
    logger.info("Starting CVlect AI Backend Service...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"NVIDIA NIM configured: {settings.has_nvidia_api}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info("=" * 60)

    # Initialize database tables
    try:
        init_db()
        logger.info("Database schema verified and tables initialized.")
        try:
            from app.database import SessionLocal
            from app.models.models import User
            from sample_data.seed_db import seed_database
            with SessionLocal() as db:
                if db.query(User).first() is None:
                    logger.info("Fresh database detected. Seeding sample candidates and jobs...")
                    seed_database()
                    logger.info("Sample database populated successfully.")
        except Exception as seed_err:
            logger.debug(f"Auto-seeding check bypassed: {seed_err}")
    except Exception as e:
        logger.error(f"Database initialization failure: {e}")

    yield

    logger.info("CVlect AI Backend Service shutting down.")


app = FastAPI(
    title="CVlect AI — Intelligent Recruitment Platform API",
    description=(
        "Next-generation talent acquisition backend featuring deep learning ranking, "
        "dense semantic representations, multi-factor explainable matching, and NVIDIA NIM LLM assistance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(applications.router)
app.include_router(analytics.router)
app.include_router(assistant.router)
app.include_router(saved_jobs.router)


@app.get("/api/health", tags=["System"])
def health_check():
    """System health check and runtime status."""
    return {
        "status": "healthy",
        "service": "CVlect AI Backend",
        "version": "1.0.0",
        "nvidia_nim_configured": settings.has_nvidia_api,
        "database": "connected",
        "docs_url": "/docs",
    }


@app.get("/", tags=["System"])
def root():
    """Root platform metadata."""
    return {
        "platform": "CVlect AI",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
    }
