"""
index.py — Vercel Serverless Function entry point.

This file re-exports the FastAPI `app` instance so that @vercel/python
can discover it. All routing and middleware stay in app/main.py.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app 
