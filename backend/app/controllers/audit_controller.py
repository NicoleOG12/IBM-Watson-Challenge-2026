"""
audit_controller.py — HTTP endpoints for the audit log.

Exposes the in-memory audit store over REST so operators and dashboards
can inspect query history without touching the filesystem.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query, Depends

from app.models.audit import AuditLog
from app.services.audit_service import get_logs
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=List[AuditLog],
    summary="List audit log entries",
)
async def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return (newest first)"),
    _settings: Settings = Depends(get_settings),
) -> List[AuditLog]:
    """
    Return recent audit log entries from the in-memory store.

    - Optionally filter by **user_id**.
    - Results are ordered newest-first.
    - Maximum **limit** is 500 per request.
    """
    return get_logs(user_id=user_id, limit=limit)
