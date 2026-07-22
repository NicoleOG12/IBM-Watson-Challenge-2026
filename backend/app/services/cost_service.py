"""
cost_service.py — Formula-based SQL cost estimation for the AI data copilot.

Estimates query cost before execution using a simple heuristic:

    base_bytes  = table_count × 500 MB
    scan_bytes  = base_bytes × 2   if no WHERE clause (full table scan assumed)
                = base_bytes × 0.3 if WHERE clause present (partial scan)
    cost_usd    = scan_bytes / 1 TB × $5.00  (BigQuery standard on-demand rate)

All estimates are clearly flagged as mocks (is_mock=True).
No real query planner or database is consulted.

Public API
----------
    from app.services.cost_service import estimate_cost

    estimate = estimate_cost(sql)
    # estimate is a CostEstimate
"""

import re
import logging

from app.models.cost import CostEstimate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BYTES_PER_TB: int = 1_000_000_000_000          # 1 TB in bytes
_COST_PER_TB_USD: float = 5.00                   # BigQuery standard on-demand rate
_BASE_BYTES_PER_TABLE: int = 500_000_000         # 500 MB per table (baseline assumption)
_FULL_SCAN_MULTIPLIER: float = 2.0               # no WHERE → full scan → 2× base
_FILTERED_SCAN_MULTIPLIER: float = 0.3           # WHERE present → partial scan → 0.3× base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_tables(sql: str) -> int:
    """
    Count distinct table references in FROM and JOIN clauses.

    Returns at least 1 so single-table queries always produce a non-zero estimate.
    """
    pattern = re.compile(r'\b(?:FROM|JOIN)\s+(?:\w+\.)?\w+', re.IGNORECASE)
    matches = pattern.findall(sql)
    return max(len(set(m.lower() for m in matches)), 1)


def _has_where_clause(sql: str) -> bool:
    """Return True if the SQL contains a WHERE clause."""
    return bool(re.search(r'\bWHERE\b', sql, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def estimate_cost(sql: str) -> CostEstimate:
    """
    Produce a formula-based cost estimate for a SQL query.

    The estimate is purely informational — it does NOT block execution.

    Formula:
        base_bytes  = table_count × 500 MB
        scan_bytes  = base_bytes × 2.0  (no WHERE)
                    = base_bytes × 0.3  (WHERE present)
        cost_usd    = scan_bytes / 1 TB × $5.00

    Args:
        sql: The validated SQL string to estimate.

    Returns:
        CostEstimate with bytes_scanned, estimated_cost_usd, table_count,
        has_filter, and is_mock=True.

    Example:
        >>> est = estimate_cost("SELECT * FROM orders WHERE status = 'open'")
        >>> est.has_filter
        True
        >>> est.is_mock
        True
    """
    table_count = _count_tables(sql)
    has_filter = _has_where_clause(sql)

    base_bytes = table_count * _BASE_BYTES_PER_TABLE
    multiplier = _FILTERED_SCAN_MULTIPLIER if has_filter else _FULL_SCAN_MULTIPLIER
    bytes_scanned = int(base_bytes * multiplier)

    estimated_cost_usd = round((bytes_scanned / _BYTES_PER_TB) * _COST_PER_TB_USD, 6)

    logger.debug(
        "Cost estimated",
        extra={
            "table_count": table_count,
            "has_filter": has_filter,
            "bytes_scanned": bytes_scanned,
            "cost_usd": estimated_cost_usd,
        },
    )

    return CostEstimate(
        bytes_scanned=bytes_scanned,
        estimated_cost_usd=estimated_cost_usd,
        table_count=table_count,
        has_filter=has_filter,
        is_mock=True,
    )
