"""
mock_executor.py — In-memory SQLite executor for local development.

Seeds an in-memory SQLite database from MOCK_TABLES (data/mock_data.py)
and runs standard SQL against it using Python's built-in sqlite3 module.

No external dependencies. No network calls. Deterministic output.
Used automatically when USE_ATHENA=False (the default).
"""

import logging
import sqlite3
import time
from typing import Any, Dict, List

from app.services.execution.base import ExecutionResult, QueryExecutor

logger = logging.getLogger(__name__)


class MockExecutor(QueryExecutor):
    """
    Executes SQL against an in-memory SQLite database seeded from MOCK_TABLES.

    A fresh SQLite connection is created for every execute() call so tests
    remain fully isolated. For higher-throughput scenarios the connection
    can be cached as a class attribute.
    """

    def _build_db(self) -> sqlite3.Connection:
        """
        Seed and return an in-memory SQLite connection populated with
        all tables from data.mock_data.MOCK_TABLES.
        """
        from data.mock_data import MOCK_TABLES

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        for table_name, rows in MOCK_TABLES.items():
            if not rows:
                continue
            cols = list(rows[0].keys())
            col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs})')
            placeholders = ", ".join("?" for _ in cols)
            conn.executemany(
                f'INSERT INTO "{table_name}" VALUES ({placeholders})',
                [tuple(str(row[c]) for c in cols) for row in rows],
            )

        conn.commit()
        return conn

    async def execute(self, sql: str) -> ExecutionResult:
        """
        Execute `sql` against the in-memory mock dataset.

        Returns:
            ExecutionResult with columns, rows, execution_time_ms,
            and rows_returned populated. data_scanned_bytes and
            estimated_cost_usd are always 0 (not applicable for mock).
        """
        start = time.perf_counter()
        conn = self._build_db()

        try:
            cursor = conn.execute(sql)
            columns: List[str] = [desc[0] for desc in cursor.description or []]
            raw_rows = cursor.fetchall()
            rows: List[Dict[str, Any]] = [dict(zip(columns, row)) for row in raw_rows]
            elapsed_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "MockExecutor: query succeeded",
                extra={"rows": len(rows), "time_ms": round(elapsed_ms, 1)},
            )

            # Populate realistic metadata using the cost formula
            from app.services.cost_service import estimate_cost
            cost_est = estimate_cost(sql)

            return ExecutionResult(
                columns=columns,
                rows=rows,
                execution_time_ms=elapsed_ms,
                rows_returned=len(rows),
                data_scanned_bytes=cost_est.bytes_scanned,
                estimated_cost_usd=cost_est.estimated_cost_usd,
                execution_mode="mock-sqlite",
            )

        except sqlite3.OperationalError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("MockExecutor: SQL error", exc_info=exc)
            return ExecutionResult(
                execution_time_ms=elapsed_ms,
                execution_mode="mock",
                error=f"SQL execution error: {exc}",
            )

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("MockExecutor: unexpected error", exc_info=exc)
            return ExecutionResult(
                execution_time_ms=elapsed_ms,
                execution_mode="mock",
                error=f"Unexpected error: {exc}",
            )

        finally:
            conn.close()
