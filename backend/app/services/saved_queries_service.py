"""
saved_queries_service.py — Repository for approved/saved SQL queries.

Queries are added to this store in two ways:
    1. Auto-saved on every successful execution (auto_saved=True).
    2. Explicitly saved by the user via POST /queries/save (auto_saved=False),
       allowing the user to add tags and a description.

Storage
-------
MVP: plain in-memory dict keyed by query id (UUID).
    - Zero dependencies, fast, works out of the box.
    - Data is lost on restart — acceptable for a local / demo environment.

Public API
----------
    auto_save(user_id, question, sql, tables_used)  # → saves on successful execution
    save_query(request)                              # → explicit save with tags/description
    get_saved_queries(user_id, tag)                  # → list, filterable by user and tag
    delete_saved_query(query_id)                     # → remove by id
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.saved_query import SavedQuery, SaveQueryRequest, UpdateSavedQueryRequest
from app.services.memory_service import _extract_tables

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store  {query_id: SavedQuery}
# ---------------------------------------------------------------------------

_SAVED: Dict[str, SavedQuery] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def auto_save(
    user_id: str,
    question: str,
    sql: str,
    tables_used: Optional[List[str]] = None,
) -> SavedQuery:
    """
    Automatically save a query after a successful execution.

    Called by query_service.py at Step 9 — no user action required.
    The `auto_saved` flag is set to True so callers can distinguish these
    from explicitly saved queries.

    Args:
        user_id:     The user who ran the query.
        question:    The original natural language question.
        sql:         The validated SQL that was executed.
        tables_used: Pre-extracted tables list; extracted from SQL if None.

    Returns:
        The newly created SavedQuery.
    """
    query_id = str(uuid.uuid4())
    saved = SavedQuery(
        id=query_id,
        user_id=user_id,
        question=question,
        sql=sql,
        tables_used=tables_used if tables_used is not None else _extract_tables(sql),
        tags=[],
        description=None,
        auto_saved=True,
    )
    _SAVED[query_id] = saved
    logger.debug(
        "Query auto-saved",
        extra={"query_id": query_id, "user_id": user_id},
    )
    return saved


def save_query(request: SaveQueryRequest) -> SavedQuery:
    """
    Explicitly save a query with optional tags and description.

    Called via POST /queries/save. Sets auto_saved=False to distinguish
    from automatically saved entries.

    Args:
        request: SaveQueryRequest with user_id, question, sql, tags, description.

    Returns:
        The newly created SavedQuery.
    """
    query_id = str(uuid.uuid4())
    saved = SavedQuery(
        id=query_id,
        user_id=request.user_id,
        question=request.question,
        sql=request.sql,
        tables_used=_extract_tables(request.sql),
        tags=request.tags,
        description=request.description,
        auto_saved=False,
    )
    _SAVED[query_id] = saved
    logger.info(
        "Query explicitly saved",
        extra={"query_id": query_id, "user_id": request.user_id, "tags": request.tags},
    )
    return saved


def get_saved_queries(
    user_id: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[SavedQuery]:
    """
    Retrieve saved queries, optionally filtered by user_id and/or tag.

    Results are ordered by created_at descending (newest first).

    Args:
        user_id: If provided, only return queries belonging to this user.
        tag:     If provided, only return queries that include this tag
                 (case-insensitive match).

    Returns:
        List of matching SavedQuery objects.
    """
    results = list(_SAVED.values())

    if user_id is not None:
        results = [q for q in results if q.user_id == user_id]

    if tag is not None:
        tag_lower = tag.lower()
        results = [q for q in results if any(t.lower() == tag_lower for t in q.tags)]

    results.sort(key=lambda q: q.created_at, reverse=True)
    return results


def update_saved_query(
    query_id: str,
    request: UpdateSavedQueryRequest,
) -> Optional[SavedQuery]:
    """
    Update fields of an existing saved query.

    Only fields explicitly set in `request` are updated;
    None values leave the existing field unchanged.

    Args:
        query_id: The ID of the saved query to update.
        request:  UpdateSavedQueryRequest with optional tags, description, sql.

    Returns:
        The updated SavedQuery, or None if query_id was not found.
    """
    if query_id not in _SAVED:
        return None

    saved = _SAVED[query_id]

    updated = saved.model_copy(update={
        k: v for k, v in {
            "tags":        request.tags,
            "description": request.description,
            "sql":         request.sql,
        }.items() if v is not None
    })

    # Re-extract tables if SQL changed
    if request.sql is not None:
        updated = updated.model_copy(update={"tables_used": _extract_tables(request.sql)})

    _SAVED[query_id] = updated
    logger.info("Saved query updated", extra={"query_id": query_id})
    return updated


def delete_saved_query(query_id: str) -> bool:
    """
    Remove a saved query by its id.

    Args:
        query_id: The id of the query to delete.

    Returns:
        True if the query was found and deleted, False if not found.
    """
    if query_id in _SAVED:
        del _SAVED[query_id]
        logger.info("Saved query deleted", extra={"query_id": query_id})
        return True
    return False
