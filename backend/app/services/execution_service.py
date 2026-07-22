"""
execution_service.py — Public SQL execution entry point.

This module is the stable API boundary consumed by QueryService and tests.
Internally it delegates to the execution sub-package:

  app/services/execution/
    base.py            — QueryExecutor ABC + ExecutionResult dataclass
    mock_executor.py   — SQLite in-memory executor (USE_ATHENA=False)
    athena_executor.py — AWS Athena executor       (USE_ATHENA=True)
    factory.py         — get_executor() with automatic MockExecutor fallback

Migration from the previous flat connector model
-------------------------------------------------
The old `set_connector(fn)` API is preserved for backward compatibility.
If a custom connector is registered it takes precedence over the factory,
exactly as before.
"""

import logging
from typing import Any, Callable, Awaitable, List, Optional

from app.config import get_settings
from app.models.execution import ExecutionMetadata, QueryResult
from app.services.execution.base import ExecutionResult
from app.services.execution.factory import get_executor

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Backward-compatible custom connector registry
# ---------------------------------------------------------------------------

ConnectorFn = Callable[[str], Awaitable[tuple[list[dict], list[str]]]]
_custom_connector: Optional[ConnectorFn] = None


def set_connector(fn: ConnectorFn) -> None:
    """
    Register a legacy async connector to replace the executor factory.

    Kept for backward compatibility. For new integrations, implement
    a QueryExecutor subclass and configure USE_ATHENA / the factory instead.

    Example:
        async def pg_connector(sql: str):
            rows = await conn.fetch(sql)
            return [dict(r) for r in rows], list(rows[0].keys())

        set_connector(pg_connector)
    """
    global _custom_connector
    _custom_connector = fn
    logger.info("Custom connector registered: %s", fn.__name__)


# ---------------------------------------------------------------------------
# Internal helper — translate ExecutionResult → QueryResult
# ---------------------------------------------------------------------------

def _to_query_result(er: ExecutionResult) -> QueryResult:
    """Map an ExecutionResult dataclass to the Pydantic QueryResult model."""
    metadata = ExecutionMetadata(
        execution_time_ms=round(er.execution_time_ms, 2),
        rows_returned=er.rows_returned,
        data_scanned_bytes=er.data_scanned_bytes,
        estimated_cost_usd=round(er.estimated_cost_usd, 6),
        execution_mode=er.execution_mode,
    )
    return QueryResult(
        rows=er.rows,
        row_count=len(er.rows),
        columns=er.columns,
        execution_mode=er.execution_mode,
        metadata=metadata,
        error=er.error,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def execute_query(sql: str) -> QueryResult:
    """
    Execute a validated SQL SELECT statement and return a QueryResult.

    Resolution order:
      1. Legacy custom connector (if set via set_connector())
      2. Factory executor — MockExecutor or AthenaExecutor depending on USE_ATHENA

    Returns a QueryResult; never raises (errors are captured in result.error).

    Args:
        sql: A validated SELECT SQL string.
    """
    # --- Legacy connector path (backward compat) ----------------------------
    if _custom_connector is not None:
        logger.info("execute_query: using registered custom connector")
        try:
            rows, columns = await _custom_connector(sql)
            return QueryResult(
                rows=rows,
                row_count=len(rows),
                columns=columns,
                execution_mode="live",
                metadata=ExecutionMetadata(
                    rows_returned=len(rows),
                    execution_mode="live",
                ),
            )
        except Exception as exc:
            logger.error("Custom connector error", exc_info=exc)
            return QueryResult(
                rows=[],
                row_count=0,
                columns=[],
                execution_mode="live",
                error=f"Connector error: {exc}",
            )

    # --- Factory executor path ----------------------------------------------
    executor = get_executor()
    er: ExecutionResult = await executor.execute(sql)
    return _to_query_result(er)
