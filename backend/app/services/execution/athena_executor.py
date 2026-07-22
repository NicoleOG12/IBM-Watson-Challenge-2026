"""
athena_executor.py — AWS Athena query executor.

Uses boto3 to:
  1. Optionally assume an IAM Role via STS (when AWS_ROLE_ARN is set)
  2. Start a query execution via start_query_execution()
  3. Poll GetQueryExecution until status is SUCCEEDED / FAILED / CANCELLED
  4. Fetch paginated results via GetQueryResults()
  5. Parse the header + rows into the standard ExecutionResult format
  6. Populate Athena-specific metadata:
       - execution_time_ms  (from Athena's own statistics)
       - data_scanned_bytes (from Athena statistics)
       - estimated_cost_usd (AWS prices at $5 / TB scanned, 10 MB minimum)

If boto3 is not installed (e.g. in a dev environment) the import is deferred
so MockExecutor still works without it.

Environment variables required (via Settings):
    AWS_REGION       — e.g. "sa-east-1"
    ATHENA_DB        — Glue Data Catalog database name  (default: db_watson)
    ATHENA_OUTPUT    — S3 output location, e.g. "s3://athena-results/query-results/"

Optional:
    AWS_ROLE_ARN     — When set, the executor calls STS AssumeRole to obtain
                       temporary credentials before creating the Athena client.
                       Not needed when running inside Lambda (role is attached
                       automatically by the execution environment).
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


def _base_credentials() -> Dict[str, str]:
    """
    Return static credential kwargs for boto3 when AWS_ACCESS_KEY_ID is set.
    Returns empty dict so boto3 falls back to its default credential chain.
    """
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        return {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
    return {}


def _assume_role_credentials(role_arn: str, region: str) -> Dict[str, str]:
    """
    Call STS AssumeRole and return a dict of temporary credentials.

    Returns a dict with keys:
        aws_access_key_id, aws_secret_access_key, aws_session_token

    Raises:
        Exception — propagated to the caller (factory will fall back to Mock).
    """
    import boto3

    sts = boto3.client("sts", region_name=region, **_base_credentials())
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="AiDataCopilotAthenaSession",
        DurationSeconds=3600,
    )
    creds = response["Credentials"]
    logger.info("STS AssumeRole succeeded for role %s", role_arn)
    return {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }


class AthenaExecutor(QueryExecutor):
    """
    Executes SQL against AWS Athena.

    IAM Role handling
    -----------------
    - Inside Lambda: the execution role (ConsulteFunction02-role-3cnsnkm) is
      attached automatically — boto3 picks up the credentials from the
      Lambda environment without any extra configuration.
    - Outside Lambda (local dev / CI): if AWS_ROLE_ARN is set the constructor
      calls STS AssumeRole to obtain temporary credentials. Otherwise boto3
      falls back to the standard credential chain (env vars, ~/.aws, etc.).

    Constructor raises ImportError if boto3 is not installed, which
    the factory catches to fall back to MockExecutor.

    Args:
        region:   AWS region (defaults to settings.AWS_REGION → "sa-east-1").
        database: Glue database name (defaults to settings.ATHENA_DB → "db_watson").
        output:   S3 output path (defaults to settings.ATHENA_OUTPUT).
        role_arn: IAM Role ARN to assume (defaults to settings.AWS_ROLE_ARN).
    """

    def __init__(
        self,
        region: Optional[str] = None,
        database: Optional[str] = None,
        output: Optional[str] = None,
        role_arn: Optional[str] = None,
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
        self._role_arn = role_arn or settings.AWS_ROLE_ARN

        if not self.output:
            raise ValueError(
                "ATHENA_OUTPUT must be set to an S3 path, "
                "e.g. s3://athena-results/query-results/"
            )

        # Resolve temporary credentials now (fail fast at construction time)
        # so that the factory can fall back to Mock before the first query.
        self._creds: Optional[Dict[str, str]] = None
        if self._role_arn:
            self._creds = _assume_role_credentials(self._role_arn, self.region)

        logger.info(
            "AthenaExecutor initialised — region=%s  database=%s  role=%s",
            self.region,
            self.database,
            self._role_arn or "(default credential chain)",
        )

    def _client(self):
        """
        Return a fresh boto3 Athena client.

        Priority:
          1. STS-assumed role credentials (when AWS_ROLE_ARN was resolved)
          2. Static credentials from AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
          3. boto3 default credential chain (Lambda role, ~/.aws, instance profile)
        """
        import boto3

        if self._creds:
            return boto3.client(
                "athena",
                region_name=self.region,
                aws_access_key_id=self._creds["aws_access_key_id"],
                aws_secret_access_key=self._creds["aws_secret_access_key"],
                aws_session_token=self._creds["aws_session_token"],
            )
        return boto3.client("athena", region_name=self.region, **_base_credentials())

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
        logger.info("AthenaExecutor: started query_id=%s", query_id)

        # ----------------------------------------------------------------
        # 2. Poll until terminal state
        # ----------------------------------------------------------------
        import asyncio

        deadline = time.perf_counter() + _MAX_WAIT_SECONDS
        execution: Dict[str, Any] = {}

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
                    "AthenaExecutor: query %s — query_id=%s reason=%s",
                    state, query_id, reason,
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
            "AthenaExecutor: complete — query_id=%s rows=%d scanned=%d bytes "
            "athena_ms=%d wall_ms=%.1f cost_usd=%.6f",
            query_id, len(rows), scanned_bytes,
            athena_exec_ms, wall_elapsed_ms, cost_usd,
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
