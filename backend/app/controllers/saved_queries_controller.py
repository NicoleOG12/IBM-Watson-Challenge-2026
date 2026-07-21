"""
saved_queries_controller.py — HTTP endpoints for the saved/approved queries repository.

Provides three endpoints:
    GET  /queries/saved              — list saved queries (filterable by user_id and tag)
    POST /queries/save               — explicitly save a query with tags and description
    DELETE /queries/saved/{query_id} — remove a saved query by id
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.saved_query import SavedQuery, SaveQueryRequest
from app.services.saved_queries_service import (
    save_query,
    get_saved_queries,
    delete_saved_query,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Saved Queries"])


@router.get(
    "/queries/saved",
    response_model=List[SavedQuery],
    summary="List saved queries",
)
async def list_saved_queries(
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    tag: Optional[str] = Query(default=None, description="Filter by tag (case-insensitive)"),
) -> List[SavedQuery]:
    """
    Return saved queries ordered by creation date descending (newest first).

    - **user_id**: optional filter — only queries belonging to this user
    - **tag**: optional filter — only queries that include this tag
    """
    return get_saved_queries(user_id=user_id, tag=tag)


@router.post(
    "/queries/save",
    response_model=SavedQuery,
    status_code=status.HTTP_201_CREATED,
    summary="Explicitly save a query",
)
async def save_query_endpoint(request: SaveQueryRequest) -> SavedQuery:
    """
    Save a query to the repository with optional tags and description.

    This endpoint is for **explicit** saves triggered by the user (e.g. after
    reviewing the SQL preview). Queries that execute successfully are also
    auto-saved separately by the pipeline with `auto_saved: true`.

    - **user_id**: the user saving the query
    - **question**: the natural language question
    - **sql**: the SQL to save
    - **tags**: optional list of tags for categorisation
    - **description**: optional human-readable description
    """
    saved = save_query(request)
    logger.info(
        "Query saved via endpoint",
        extra={"query_id": saved.id, "user_id": request.user_id},
    )
    return saved


@router.delete(
    "/queries/saved/{query_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved query",
)
async def delete_saved_query_endpoint(query_id: str) -> None:
    """
    Remove a saved query by its ID.

    Returns **204 No Content** on success.
    Returns **404 Not Found** if the query ID does not exist.

    - **query_id**: the ID of the saved query to remove
    """
    deleted = delete_saved_query(query_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved query '{query_id}' not found.",
        )
