"""
athena_executor.py — AWS Athena query executor.

Uses boto3 to:
  1. Start a query execution via start_query_execution()
  2. Poll GetQueryExecution until status is SUCCEEDED / FAILED / CANCELLED
  3. Fetch paginated results via GetQueryResults()
  4. Parse the header + rows into the standard ExecutionResult format
  5. Populate Athena-specific metadata:
       - execution_time_ms  (from Athena's own statistics)
       - data_scanned_bytes (from Athena statistics)
       - estimated_cost_usd (AWS prices at $5 / TB scanned, 10 MB minimum)

If boto3 is not installed (e.g. in a dev environment) the import is deferred
so MockExecutor still works without it.

Environment variables required (via Settings):
    AWS_REGION       — e.g. "us-east-1"
    ATHENA_DB        — Glue Data Catalog database name
    ATHENA_OUTPUT    — S3 output location, e.g. "s3://my-bucket/athena-results/"
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.execution.base import ExecutionResult, QueryExecutor

logger = logging.getLogger(__name__)
settings = get_settings()

# AWS pricing constant: $5.00 per TB scanned (as of 2024)
_ATHENA_PRICE_PER_BYTE = 5.0 / (1024 ** 4)
# Athena charges a minimum of 10 MB per query
_ATHENA_MIN_BYTES_BILLED = 10 * 1024 * 1024

# Polling interval and maximum wait time
_POLL_INTERVAL_SECONDS = 0.5
_MAX_WAIT_SECONDS = 300


def _estimate_cost(scanned_bytes: int) -> float:
    """Estimate query cost in USD based on bytes scanned (10 MB minimum billed)."""
    billed = max(scanned_bytes, _ATHENA_MIN_BYTES_BILLED)
    return billed * _ATHENA_PRICE_PER_BYTE


class AthenaExecutor(QueryExecutor):
    """
    Executes SQL against AWS Athena.

    Constructor raises ImportError if boto3 is not installed, which
    the factory catches to fall back to MockExecutor.

    Args:
        region:   AWS region (defaults to settings.AWS_REGION).
        database: Glue database name (defaults to settings.ATHENA_DB).
        output:   S3 output path (defaults to settings.ATHENA_OUTPUT).
    """

    def __init__(
        self,
        region: Optional[str] = None,
        database: Optional[str] = None,
        output: Optional[str] = None,
    ) -> None:
        try:
            import boto3  # noqa: F401 — validate availability at construction time
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for AthenaExecutor. "
                "Install it with: pip install boto3"
            ) from exc

        self.region = region or settings.AWS_REGION
        self.database = database or settings.ATHENA_DB
        self.output = output or settings.ATHENA_OUTPUT

        if not self.output:
            raise ValueError(
                "ATHENA_OUTPUT must be set to an S3 path, e.g. s3://my-bucket/results/"
            )

        logger.info(
            "AthenaExecutor initialised",
            extra={"region": self.region, "database": self.database},
        )

    def _client(self):
        """Return a fresh boto3 Athena client (lazy — not created at __init__)."""
        import boto3
        return boto3.client("athena", region_name=self.region)

    async def execute(self, sql: str) -> ExecutionResult:
        """
        Execute `sql` against Athena and return a structured ExecutionResult.

        Flow:
            1. start_query_execution()
            2. Poll until SUCCEEDED / FAILED / CANCELLED
            3. get_query_results() (paginated)
            4. Parse header + rows
            5. Populate metadata from Athena statistics

        Returns:
            ExecutionResult with full metadata including data_scanned_bytes
            and estimated_cost_usd.
        """
        wall_start = time.perf_counter()
        client = self._client()

        # ----------------------------------------------------------------
        # 1. Start execution
        # ----------------------------------------------------------------
        try:
            start_resp = client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={"Database": self.database},
                ResultConfiguration={"OutputLocation": self.output},
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - wall_start) * 1000
            logger.error("AthenaExecutor: failed to start query", exc_info=exc)
            return ExecutionResult(
                execution_time_ms=elapsed_ms,
                execution_mode="athena",
                error=f"Failed to start Athena query: {exc}",
            )

        query_id: str = start_resp["QueryExecutionId"]
        logger.info("AthenaExecutor: started", extra={"query_id": query_id})

        # ----------------------------------------------------------------
        # 2. Poll until terminal state
        # ----------------------------------------------------------------
        import asyncio

        deadline = time.perf_counter() + _MAX_WAIT_SECONDS

        while True:
            try:
                status_resp = client.get_query_execution(QueryExecutionId=query_id)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - wall_start) * 1000
                logger.error("AthenaExecutor: polling error", exc_info=exc)
                return ExecutionResult(
                    execution_time_ms=elapsed_ms,
                    execution_mode="athena",
                    error=f"Error polling Athena query status: {exc}",
                )

            execution = status_resp["QueryExecution"]
            state = execution["Status"]["State"]

            if state == "SUCCEEDED":
                break

            if state in ("FAILED", "CANCELLED"):
                reason = (
                    execution["Status"]
                    .get("StateChangeReason", f"Query {state.lower()}")
                )
                elapsed_ms = (time.perf_counter() - wall_start) * 1000
                logger.warning(
                    "AthenaExecutor: query %s", state,
                    extra={"query_id": query_id, "reason": reason},
                )
                return ExecutionResult(
                    execution_time_ms=elapsed_ms,
                    execution_mode="athena",
                    error=f"Athena query {state}: {reason}",
                )

            if time.perf_counter() > deadline:
                elapsed_ms = (time.perf_counter() - wall_start) * 1000
                return ExecutionResult(
                    execution_time_ms=elapsed_ms,
                    execution_mode="athena",
                    error=f"Athena query timed out after {_MAX_WAIT_SECONDS}s",
                )

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        # ----------------------------------------------------------------
        # 3 & 4. Fetch and parse results
        # ----------------------------------------------------------------
        columns: List[str] = []
        rows: List[Dict[str, Any]] = []

        try:
            paginator = client.get_paginator("get_query_results")
            first_page = True

            for page in paginator.paginate(QueryExecutionId=query_id):
                result_rows = page["ResultSet"]["Rows"]

                if first_page and result_rows:
                    # First row of the first page is the column header
                    columns = [
                        col.get("VarCharValue", "")
                        for col in result_rows[0]["Data"]
                    ]
                    result_rows = result_rows[1:]  # skip header
                    first_page = False

                for raw_row in result_rows:
                    values = [cell.get("VarCharValue", "") for cell in raw_row["Data"]]
                    rows.append(dict(zip(columns, values)))

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - wall_start) * 1000
            logger.error("AthenaExecutor: failed to fetch results", exc_info=exc)
            return ExecutionResult(
                execution_time_ms=elapsed_ms,
                execution_mode="athena",
                error=f"Failed to retrieve Athena results: {exc}",
            )

        # ----------------------------------------------------------------
        # 5. Collect Athena statistics
        # ----------------------------------------------------------------
        stats = execution.get("Statistics", {})
        athena_exec_ms = stats.get("TotalExecutionTimeInMillis", 0)
        scanned_bytes = stats.get("DataScannedInBytes", 0)
        cost_usd = _estimate_cost(scanned_bytes)
        wall_elapsed_ms = (time.perf_counter() - wall_start) * 1000

        logger.info(
            "AthenaExecutor: query complete",
            extra={
                "query_id": query_id,
                "rows": len(rows),
                "scanned_bytes": scanned_bytes,
                "athena_ms": athena_exec_ms,
                "wall_ms": round(wall_elapsed_ms, 1),
            },
        )

        return ExecutionResult(
            columns=columns,
            rows=rows,
            execution_time_ms=wall_elapsed_ms,
            rows_returned=len(rows),
            data_scanned_bytes=scanned_bytes,
            estimated_cost_usd=cost_usd,
            execution_mode="athena",
        )
