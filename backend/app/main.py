"""
main.py — Application entry point.

Run locally:
    uvicorn app.main:app --reload

Environment variables are loaded from .env (see .env.example).
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.routes import api_router
from app.middleware import RequestLoggingMiddleware

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Orchestration layer for an AI-powered data copilot. "
        "Translates natural language queries into structured data operations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# (Registered in reverse order — last added = outermost = first to run)
# ---------------------------------------------------------------------------

# 1. Request logging (outermost — captures total wall-clock time)
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
