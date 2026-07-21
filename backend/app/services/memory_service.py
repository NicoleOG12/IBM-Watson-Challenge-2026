"""
memory_service.py — Conversation memory for the AI data copilot.

Provides per-user interaction history so follow-up questions
(e.g. "What about last month?") can be resolved against previous context.

Storage
-------
MVP: plain in-memory dict keyed by user_id.
    - Zero dependencies, fast, works out of the box.
    - Data is lost on restart — acceptable for a local / demo environment.

Future upgrade path (swap the store only, no API change):
    - Redis: replace _STORE with aioredis hset/hget calls.
    - PostgreSQL: persist rows to a `conversation_history` table.
    - Vector DB: embed queries and retrieve semantically similar history.

Public API
----------
    context = get_context(user_id)            # → dict fed into the LLM prompt
    save_interaction(user_id, query, sql)     # → persists a turn
    get_user_memory(user_id)                  # → full UserMemory object
    clear_memory(user_id)                     # → wipe a user's history
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.memory import Interaction, UserMemory
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# In-memory store  {user_id: UserMemory}
# ---------------------------------------------------------------------------

_STORE: Dict[str, UserMemory] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_context(user_id: str) -> dict:
    """
    Return the conversation context for a user, ready to be injected into
    the LLM prompt.

    The returned dict contains:
      - user_id       : the requesting user
      - history       : list of recent {query, sql, timestamp} dicts
                        (capped at MEMORY_MAX_HISTORY entries, newest last)
      - last_query    : most recent NL query, or None
      - last_sql      : most recent SQL, or None

    This is intentionally a plain dict so it can be passed straight through
    to LLMRequest.context without further transformation.

    Args:
        user_id: The user whose context to retrieve.

    Returns:
        A plain dict suitable for use as LLM prompt context.

    Example:
        >>> save_interaction("u1", "Total sales?", "SELECT SUM(amount) FROM sales")
        >>> ctx = get_context("u1")
        >>> ctx["last_query"]
        'Total sales?'
    """
    memory = _STORE.get(user_id)
    if memory is None:
        return {
            "user_id": user_id,
            "history": [],
            "last_query": None,
            "last_sql": None,
        }

    recent = memory.interactions[-settings.MEMORY_MAX_HISTORY:]
    return {
        "user_id": user_id,
        "history": [
            {
                "query": turn.query,
                "sql": turn.sql,
                "timestamp": turn.timestamp.isoformat(),
            }
            for turn in recent
        ],
        "last_query": memory.last_query,
        "last_sql": memory.last_sql,
    }


# ---------------------------------------------------------------------------
# SQL analysis helpers
# ---------------------------------------------------------------------------

def _extract_tables(sql: str) -> List[str]:
    """
    Extract table names referenced in FROM and JOIN clauses.

    Handles simple cases: FROM table, JOIN table, FROM schema.table.
    Subqueries and CTEs are intentionally skipped (they start with SELECT or WITH).

    Args:
        sql: The SQL string to parse.

    Returns:
        Deduplicated list of table name tokens found after FROM/JOIN keywords.

    Example:
        >>> _extract_tables("SELECT * FROM sales JOIN regions ON sales.region_id = regions.id")
        ['sales', 'regions']
    """
    # Match word after FROM or JOIN, optionally schema-qualified (word.word)
    pattern = re.compile(
        r'\b(?:FROM|JOIN)\s+((?:\w+\.)?\w+)',
        re.IGNORECASE,
    )
    tables = pattern.findall(sql)
    # Deduplicate while preserving order; skip subquery aliases (no parens check needed
    # because the regex anchors on a word boundary — subqueries start with "(SELECT")
    seen: set[str] = set()
    result: List[str] = []
    for t in tables:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            result.append(t)
    return result


def _extract_filters(sql: str) -> List[str]:
    """
    Extract predicate tokens from the WHERE clause of a SQL statement.

    Splits on AND/OR to return individual filter expressions.
    Returns an empty list when no WHERE clause is present.

    Args:
        sql: The SQL string to parse.

    Returns:
        List of individual filter predicate strings (stripped of whitespace).

    Example:
        >>> _extract_filters("SELECT * FROM t WHERE region = 'North' AND amount > 100")
        ["region = 'North'", 'amount > 100']
    """
    # Isolate everything between WHERE and the next clause keyword
    where_match = re.search(
        r'\bWHERE\b(.+?)(?:\b(?:GROUP BY|ORDER BY|HAVING|LIMIT|UNION|EXCEPT|INTERSECT)\b|$)',
        sql,
        re.IGNORECASE | re.DOTALL,
    )
    if not where_match:
        return []

    where_body = where_match.group(1).strip()
    # Split on AND / OR (case-insensitive), keep each predicate
    predicates = re.split(r'\s+(?:AND|OR)\s+', where_body, flags=re.IGNORECASE)
    return [p.strip() for p in predicates if p.strip()]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_interaction(
    user_id: str,
    query: str,
    sql: str,
    *,
    status: str = "success",
    row_count: int = 0,
) -> None:
    """
    Persist a completed query/SQL interaction to the user's memory.

    Automatically extracts tables and filters from the SQL, and trims the
    history to MEMORY_MAX_HISTORY entries so the store never grows unbounded.

    Args:
        user_id:   The user who made the query.
        query:     The natural language query they asked.
        sql:       The SQL that was generated (and validated) in response.
        status:    Execution status — 'success' or 'rejected'. Defaults to 'success'.
        row_count: Number of rows returned. Defaults to 0.

    Example:
        >>> save_interaction("u1", "Show sales by region", "SELECT region, SUM(amount) ...")
        >>> get_context("u1")["last_query"]
        'Show sales by region'
    """
    if user_id not in _STORE:
        _STORE[user_id] = UserMemory(user_id=user_id)

    interaction = Interaction(
        query=query,
        sql=sql,
        timestamp=datetime.now(timezone.utc),
        tables_used=_extract_tables(sql),
        filters_applied=_extract_filters(sql),
        status=status,
        row_count=row_count,
    )
    _STORE[user_id].interactions.append(interaction)

    # Trim to the rolling window
    max_hist = settings.MEMORY_MAX_HISTORY
    if len(_STORE[user_id].interactions) > max_hist:
        _STORE[user_id].interactions = _STORE[user_id].interactions[-max_hist:]

    logger.debug(
        "Interaction saved",
        extra={
            "user_id": user_id,
            "history_len": len(_STORE[user_id].interactions),
            "tables": interaction.tables_used,
            "filters": len(interaction.filters_applied),
        },
    )


def get_user_memory(user_id: str) -> Optional[UserMemory]:
    """
    Return the full UserMemory object for a user, or None if no history exists.

    Useful for debugging or admin endpoints.

    Args:
        user_id: The user whose memory to retrieve.

    Returns:
        UserMemory if the user has history, else None.
    """
    return _STORE.get(user_id)


def clear_memory(user_id: str) -> None:
    """
    Wipe all conversation history for a specific user.

    Args:
        user_id: The user whose memory to clear.
    """
    if user_id in _STORE:
        del _STORE[user_id]
        logger.info("Memory cleared for user", extra={"user_id": user_id})


def all_user_ids() -> List[str]:
    """Return a list of all user IDs that currently have stored memory."""
    return list(_STORE.keys())
