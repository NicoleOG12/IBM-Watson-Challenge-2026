"""
main.py — Vercel Services entry point for the FastAPI backend.

The Vercel Services runtime looks for `main.py` at the root of the
service directory (`backend/`). This file simply re-exports the
FastAPI `app` object from the real application package.
"""

from app.main import app  # noqa: F401
