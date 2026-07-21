"""
base.py — Abstract base class for all SQL executors.

Every executor (Mock, Athena, future BigQuery, Redshift, etc.) must:
  1. Inherit from QueryExecutor
  2. Implement the async execute(sql) method
  3. Return an ExecutionResult

This contract lets the rest of the codebase stay executor-agnostic.
Swapping from Mock → Athena → any other backend requires only a settings
flag change — no changes in query_service.py or anywhere upstream.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionResult:
    """
    Unified result returned by every QueryExecutor implementation.

    Fields align with the expected API output:
      {
        "columns":  [...],
        "rows":     [...],
        "metadata": {
          "execution_time_ms":   1234,
          "rows_returned":       100,
          "data_scanned_bytes":  123456,
          "estimated_cost_usd":  0.0023,
          "execution_mode":      "athena" | "mock"
        }
      }
    """

    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata (all optional — populated by implementations that can measure them)
    execution_time_ms: float = 0.0
    rows_returned: int = 0
    data_scanned_bytes: int = 0
    estimated_cost_usd: float = 0.0
    execution_mode: str = "unknown"

    # Non-None when something went wrong
    error: Optional[str] = None

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @property
    def metadata(self) -> Dict[str, Any]:
        """Convenience property — returns the metadata sub-dict for API responses."""
        return {
            "execution_time_ms": round(self.execution_time_ms, 2),
            "rows_returned": self.rows_returned,
            "data_scanned_bytes": self.data_scanned_bytes,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "execution_mode": self.execution_mode,
        }

    @property
    def ok(self) -> bool:
        """True when execution succeeded with no error."""
        return self.error is None


class QueryExecutor(ABC):
    """
    Abstract base class for SQL query executors.

    Subclasses implement the async execute() method, which accepts a
    validated SELECT SQL string and returns an ExecutionResult.

    The method is async so implementations can use async I/O (e.g. aioboto3,
    asyncpg) without blocking the FastAPI event loop.
    """

    @abstractmethod
    async def execute(self, sql: str) -> ExecutionResult:
        """
        Execute a validated SELECT SQL string.

        Args:
            sql: A validated SELECT SQL statement.

        Returns:
            ExecutionResult with columns, rows, metadata, and optional error.

        This method must not raise — errors should be captured in
        ExecutionResult.error so the caller always gets a structured response.
        """
        ...
