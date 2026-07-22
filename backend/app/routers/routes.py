"""
routes.py — Central FastAPI router.

Import all sub-routers here so that main.py only needs to include one object.
Add new feature routers below as the project grows.
"""

from fastapi import APIRouter

from app.controllers.audit_controller import router as audit_router
from app.controllers.aws_controller import router as aws_router
from app.controllers.copilot_controller import router as copilot_router
from app.controllers.cost_controller import router as cost_router
from app.controllers.docs_controller import router as docs_router
from app.controllers.memory_controller import router as memory_router
from app.controllers.query_controller import router as query_router
from app.controllers.saved_queries_controller import router as saved_queries_router
from app.controllers.sql_controller import router as sql_router

api_router = APIRouter()

api_router.include_router(query_router)
api_router.include_router(audit_router)
api_router.include_router(memory_router)
api_router.include_router(cost_router)
api_router.include_router(sql_router)
api_router.include_router(saved_queries_router)
api_router.include_router(docs_router)
api_router.include_router(copilot_router)
api_router.include_router(aws_router)
