"""
audit_service.py — Audit log persistence layer.

Stores audit records in two sinks:

  1. In-memory list (_AUDIT_LOG)
     Fast, zero-dependency, queryable at runtime via get_logs().
     Lost on restart — fine for MVP / demo.

  2. JSON-lines file (AUDIT_LOG_FILE, default: logs/audit.log)
     Each line is a complete JSON object, one per request.
     Append-only, survives restarts, easy to tail or ingest.

Future upgrade path (swap sink, no API change):
  - DynamoDB: call table.put_item(Item=log.to_dynamo()) in _write_log()
  - PostgreSQL: INSERT INTO audit_logs VALUES (...)
  - CloudWatch / Datadog: ship the JSON line via the SDK

Public API
----------
    record_query(user_id, query, sql, status, execution_time_ms, row_count, error)
    get_logs(user_id=None, limit=100)
    clear_logs()                   # test helper
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.models.audit import AuditLog
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_AUDIT_LOG: List[AuditLog] = []


# ---------------------------------------------------------------------------
# File sink helper
# ---------------------------------------------------------------------------

def _write_log(entry: AuditLog) -> None:
    """Append a JSON-lines entry to the audit log file, if enabled."""
    if not settings.AUDIT_ENABLED:
        return

    # Resolve the log path: prefer the configured value, but fall back to
    # /tmp/<filename> when the configured directory is not writable (e.g. Vercel).
    log_path = Path(settings.AUDIT_LOG_FILE)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Filesystem is read-only (Vercel / Lambda) — redirect to /tmp
        log_path = Path("/tmp") / log_path.name

    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(entry.model_dump_json() + "\n")
    except OSError as exc:
        # Never let a log write crash the request pipeline
        logger.error("Failed to write audit log to file", exc_info=exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_query(
    user_id: str,
    natural_language_query: str,
    generated_sql: str,
    status: str,
    execution_time_ms: float,
    row_count: int = 0,
    error: Optional[str] = None,
) -> AuditLog:
    """
    Create and persist an AuditLog entry for a completed query pipeline run.

    Args:
        user_id:                 The requesting user.
        natural_language_query:  The original NL question.
        generated_sql:           The SQL produced by the LLM.
        status:                  'success' | 'rejected' | 'error'
        execution_time_ms:       Wall-clock time for the full pipeline (ms).
        row_count:               Number of rows returned by SQL execution.
        error:                   Optional error or rejection reason string.

    Returns:
        The persisted AuditLog instance.

    Example log entry
    -----------------
    {
        "log_id": "a1b2c3d4-...",
        "timestamp": "2024-01-01T12:00:00.123456+00:00",
        "user_id": "user-123",
        "natural_language_query": "Show me total sales by region for last quarter",
        "generated_sql": "SELECT region, SUM(amount) AS total FROM sales GROUP BY region",
        "status": "success",
        "execution_time_ms": 142.7,
        "row_count": 4,
        "environment": "development",
        "error": null
    }
    """
    entry = AuditLog(
        user_id=user_id,
        natural_language_query=natural_language_query,
        generated_sql=generated_sql,
        status=status,
        execution_time_ms=round(execution_time_ms, 2),
        row_count=row_count,
        environment=settings.ENVIRONMENT,
        error=error,
    )

    _AUDIT_LOG.append(entry)
    _write_log(entry)

    logger.info(
        "AUDIT | %s | user=%s | status=%s | rows=%d | time=%.1fms%s",
        entry.log_id,
        user_id,
        status,
        row_count,
        execution_time_ms,
        f" | error={error}" if error else "",
    )

    return entry


def get_logs(
    user_id: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """
    Return audit log entries from the in-memory store.

    Args:
        user_id: Filter to a specific user. None returns all users.
        limit:   Maximum number of entries to return (newest first).

    Returns:
        List of AuditLog entries, newest first.
    """
    logs = _AUDIT_LOG if user_id is None else [e for e in _AUDIT_LOG if e.user_id == user_id]
    return list(reversed(logs))[:limit]


def clear_logs() -> None:
    """Clear the in-memory audit log. Primarily used in tests."""
    _AUDIT_LOG.clear()
