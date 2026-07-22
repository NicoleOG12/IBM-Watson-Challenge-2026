"""
docs_controller.py — HTTP endpoint for Markdown logbook export.

Exposes GET /docs/export?user_id=X which returns a Markdown-formatted
session logbook for the given user, suitable for copy-paste into
Confluence, Notion, or a daily standup update.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from app.services.docs_service import export_logbook

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Documentation"])


@router.get(
    "/docs/export",
    summary="Export session logbook as Markdown",
    response_class=Response,
    responses={
        200: {
            "content": {"text/markdown": {}},
            "description": "Markdown logbook for the requested user",
        },
        404: {"description": "No history found for this user"},
    },
)
async def export_docs(
    user_id: str = Query(..., description="The user whose session to export"),
) -> Response:
    """
    Return a Markdown-formatted logbook of all recorded interactions for a user.

    Each interaction section includes:
    - The original natural language question
    - The generated SQL (in a fenced code block)
    - Tables referenced
    - Filters applied
    - Row count and execution status

    Returns `text/markdown` content. Returns **404** if the user has no history.

    - **user_id**: the user whose session to export
    """
    markdown = export_logbook(user_id)
    if markdown is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No session history found for user '{user_id}'.",
        )

    logger.info("Logbook export served", extra={"user_id": user_id})
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="logbook-{user_id}.md"'},
    )
