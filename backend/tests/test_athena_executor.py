"""
test_athena_executor.py — Unit tests for the execution sub-package.

Covers:
  - ExecutionResult dataclass (base)
  - MockExecutor correctness
  - AthenaExecutor with a fully mocked boto3 client
  - Factory fallback logic (USE_ATHENA + ImportError + ValueError + crash)
  - execute_query() shim integration (legacy connector + factory path)
  - QueryResult / ExecutionMetadata models

Run with:
    pytest tests/test_athena_executor.py -v
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.execution.base import ExecutionResult, QueryExecutor
from app.services.execution.mock_executor import MockExecutor
from app.services.execution.factory import get_executor
from app.services.execution_service import execute_query, set_connector
from app.models.execution import ExecutionMetadata, QueryResult
import app.services.execution_service as _exec_svc
import app.services.execution.factory as _factory_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _run(coro):
    return await coro


# ---------------------------------------------------------------------------
# 1. ExecutionResult dataclass
# ---------------------------------------------------------------------------

class TestExecutionResult:
    def test_defaults(self):
        er = ExecutionResult()
        assert er.columns == []
        assert er.rows == []
        assert er.execution_time_ms == 0.0
        assert er.rows_returned == 0
        assert er.data_scanned_bytes == 0
        assert er.estimated_cost_usd == 0.0
        assert er.execution_mode == "unknown"
        assert er.error is None

    def test_ok_true_when_no_error(self):
        er = ExecutionResult(execution_mode="mock")
        assert er.ok is True

    def test_ok_false_when_error_set(self):
        er = ExecutionResult(execution_mode="mock", error="oops")
        assert er.ok is False

    def test_metadata_property(self):
        er = ExecutionResult(
            execution_time_ms=123.456,
            rows_returned=5,
            data_scanned_bytes=102400,
            estimated_cost_usd=0.000512,
            execution_mode="athena",
        )
        m = er.metadata
        assert m["execution_time_ms"] == 123.46
        assert m["rows_returned"] == 5
        assert m["data_scanned_bytes"] == 102400
        assert m["execution_mode"] == "athena"
        assert "estimated_cost_usd" in m

    def test_estimated_cost_rounded(self):
        er = ExecutionResult(execution_time_ms=10.0, execution_mode="mock")
        assert isinstance(er.metadata["estimated_cost_usd"], float)


# ---------------------------------------------------------------------------
# 2. MockExecutor
# ---------------------------------------------------------------------------

class TestMockExecutor:
    @pytest.mark.asyncio
    async def test_returns_execution_result(self):
        ex = MockExecutor()
        result = await ex.execute("SELECT * FROM sales")
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execution_mode_is_mock(self):
        result = await MockExecutor().execute("SELECT * FROM sales")
        assert result.execution_mode == "mock-sqlite"

    @pytest.mark.asyncio
    async def test_columns_populated(self):
        result = await MockExecutor().execute("SELECT region, amount FROM sales LIMIT 1")
        assert "region" in result.columns
        assert "amount" in result.columns

    @pytest.mark.asyncio
    async def test_rows_returned(self):
        result = await MockExecutor().execute("SELECT * FROM sales LIMIT 5")
        assert result.rows_returned == 5
        assert len(result.rows) == 5

    @pytest.mark.asyncio
    async def test_execution_time_positive(self):
        result = await MockExecutor().execute("SELECT 1")
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_no_cost_in_mock_mode(self):
        result = await MockExecutor().execute("SELECT * FROM sales")
        assert result.data_scanned_bytes >= 0
        assert result.estimated_cost_usd >= 0.0

    @pytest.mark.asyncio
    async def test_invalid_table_returns_error(self):
        result = await MockExecutor().execute("SELECT * FROM ghost_table")
        assert result.error is not None
        assert result.rows == []

    @pytest.mark.asyncio
    async def test_ok_on_valid_query(self):
        result = await MockExecutor().execute("SELECT * FROM products")
        assert result.ok is True
        assert result.error is None


# ---------------------------------------------------------------------------
# 3. AthenaExecutor — fully mocked boto3
# ---------------------------------------------------------------------------

def _make_athena_client(state="SUCCEEDED", scanned=204800):
    """Build a MagicMock that mimics the boto3 Athena client."""
    client = MagicMock()

    client.start_query_execution.return_value = {"QueryExecutionId": "qe-test-123"}

    client.get_query_execution.return_value = {
        "QueryExecution": {
            "Status": {"State": state, "StateChangeReason": "test reason"},
            "Statistics": {
                "TotalExecutionTimeInMillis": 850,
                "DataScannedInBytes": scanned,
            },
        }
    }

    # Paginator returns one page: header row + two data rows
    mock_page = {
        "ResultSet": {
            "Rows": [
                {"Data": [{"VarCharValue": "region"}, {"VarCharValue": "total_sales"}]},
                {"Data": [{"VarCharValue": "North"}, {"VarCharValue": "18450.75"}]},
                {"Data": [{"VarCharValue": "East"},  {"VarCharValue": "15230.00"}]},
            ]
        }
    }

    paginator_mock = MagicMock()
    paginator_mock.paginate.return_value = iter([mock_page])
    client.get_paginator.return_value = paginator_mock

    return client


class TestAthenaExecutor:
    def _executor(self, client):
        """Build an AthenaExecutor with a pre-seeded mock boto3 client."""
        from app.services.execution.athena_executor import AthenaExecutor

        ex = AthenaExecutor.__new__(AthenaExecutor)
        ex.region = "us-east-1"
        ex.database = "test_db"
        ex.output = "s3://bucket/output/"
        ex._client = lambda: client
        return ex

    @pytest.mark.asyncio
    async def test_returns_execution_result(self):
        from app.services.execution.athena_executor import AthenaExecutor
        ex = self._executor(_make_athena_client())
        result = await ex.execute("SELECT region, SUM(amount) FROM sales GROUP BY region")
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execution_mode_is_athena(self):
        ex = self._executor(_make_athena_client())
        result = await ex.execute("SELECT 1")
        assert result.execution_mode == "athena"

    @pytest.mark.asyncio
    async def test_columns_parsed(self):
        ex = self._executor(_make_athena_client())
        result = await ex.execute("SELECT region, total_sales FROM sales")
        assert result.columns == ["region", "total_sales"]

    @pytest.mark.asyncio
    async def test_rows_parsed(self):
        ex = self._executor(_make_athena_client())
        result = await ex.execute("SELECT region, total_sales FROM sales")
        assert len(result.rows) == 2
        assert result.rows[0] == {"region": "North", "total_sales": "18450.75"}

    @pytest.mark.asyncio
    async def test_rows_returned_count(self):
        ex = self._executor(_make_athena_client())
        result = await ex.execute("SELECT 1")
        assert result.rows_returned == 2

    @pytest.mark.asyncio
    async def test_data_scanned_bytes_populated(self):
        ex = self._executor(_make_athena_client(scanned=204800))
        result = await ex.execute("SELECT 1")
        assert result.data_scanned_bytes == 204800

    @pytest.mark.asyncio
    async def test_estimated_cost_positive(self):
        ex = self._executor(_make_athena_client(scanned=10 * 1024 * 1024))  # 10 MB minimum
        result = await ex.execute("SELECT 1")
        assert result.estimated_cost_usd > 0

    @pytest.mark.asyncio
    async def test_failed_state_returns_error(self):
        ex = self._executor(_make_athena_client(state="FAILED"))
        result = await ex.execute("SELECT 1")
        assert result.error is not None
        assert "FAILED" in result.error

    @pytest.mark.asyncio
    async def test_cancelled_state_returns_error(self):
        ex = self._executor(_make_athena_client(state="CANCELLED"))
        result = await ex.execute("SELECT 1")
        assert result.error is not None
        assert "CANCELLED" in result.error

    @pytest.mark.asyncio
    async def test_start_failure_returns_error(self):
        client = MagicMock()
        client.start_query_execution.side_effect = RuntimeError("network error")
        ex = self._executor(client)
        result = await ex.execute("SELECT 1")
        assert result.error is not None
        assert "network error" in result.error

    def test_missing_output_raises_value_error(self):
        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            from app.services.execution.athena_executor import AthenaExecutor
            import app.services.execution.athena_executor as _mod
            original = _mod.settings.ATHENA_OUTPUT
            _mod.settings.ATHENA_OUTPUT = ""
            try:
                with pytest.raises(ValueError, match="ATHENA_OUTPUT"):
                    AthenaExecutor()
            finally:
                _mod.settings.ATHENA_OUTPUT = original

    def test_missing_boto3_raises_import_error(self):
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises((ImportError, TypeError)):
                from app.services.execution.athena_executor import AthenaExecutor
                AthenaExecutor(output="s3://x/y/")


# ---------------------------------------------------------------------------
# 4. Factory
# ---------------------------------------------------------------------------

class TestFactory:
    def test_use_athena_false_returns_mock(self, monkeypatch):
        monkeypatch.setattr(_factory_mod.settings, "USE_ATHENA", False)
        ex = get_executor()
        assert isinstance(ex, MockExecutor)

    def test_use_athena_true_import_error_falls_back(self, monkeypatch):
        monkeypatch.setattr(_factory_mod.settings, "USE_ATHENA", True)
        with patch("app.services.execution.factory.AthenaExecutor", side_effect=ImportError("no boto3")):
            ex = get_executor()
        assert isinstance(ex, MockExecutor)

    def test_use_athena_true_value_error_falls_back(self, monkeypatch):
        monkeypatch.setattr(_factory_mod.settings, "USE_ATHENA", True)
        with patch("app.services.execution.factory.AthenaExecutor", side_effect=ValueError("bad config")):
            ex = get_executor()
        assert isinstance(ex, MockExecutor)

    def test_use_athena_true_generic_error_falls_back(self, monkeypatch):
        monkeypatch.setattr(_factory_mod.settings, "USE_ATHENA", True)
        with patch("app.services.execution.factory.AthenaExecutor", side_effect=RuntimeError("boom")):
            ex = get_executor()
        assert isinstance(ex, MockExecutor)

    def test_use_athena_true_success_returns_athena(self, monkeypatch):
        monkeypatch.setattr(_factory_mod.settings, "USE_ATHENA", True)
        fake_athena = MagicMock(spec=MockExecutor)
        with patch("app.services.execution.factory.AthenaExecutor", return_value=fake_athena):
            ex = get_executor()
        assert ex is fake_athena


# ---------------------------------------------------------------------------
# 5. execute_query shim (integration)
# ---------------------------------------------------------------------------

class TestExecuteQueryShim:
    @pytest.mark.asyncio
    async def test_factory_path_returns_query_result(self, monkeypatch):
        monkeypatch.setattr(_exec_svc, "_custom_connector", None)
        result = await execute_query("SELECT * FROM sales LIMIT 3")
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_metadata_populated(self, monkeypatch):
        monkeypatch.setattr(_exec_svc, "_custom_connector", None)
        result = await execute_query("SELECT * FROM sales LIMIT 1")
        assert result.metadata is not None
        assert result.metadata.execution_mode in ("mock", "mock-sqlite", "athena")

    @pytest.mark.asyncio
    async def test_legacy_connector_used_when_set(self, monkeypatch):
        async def fake_connector(sql: str):
            return [{"x": "1"}], ["x"]

        monkeypatch.setattr(_exec_svc, "_custom_connector", fake_connector)
        result = await execute_query("SELECT x FROM fake")
        assert result.rows == [{"x": "1"}]
        assert result.execution_mode == "live"

    @pytest.mark.asyncio
    async def test_legacy_connector_error_returns_error_result(self, monkeypatch):
        async def broken_connector(sql: str):
            raise ConnectionError("DB is down")

        monkeypatch.setattr(_exec_svc, "_custom_connector", broken_connector)
        result = await execute_query("SELECT 1")
        assert result.error is not None
        assert "DB is down" in result.error


# ---------------------------------------------------------------------------
# 6. ExecutionMetadata model
# ---------------------------------------------------------------------------

class TestExecutionMetadata:
    def test_defaults(self):
        m = ExecutionMetadata(execution_mode="mock")
        assert m.execution_time_ms == 0.0
        assert m.rows_returned == 0
        assert m.data_scanned_bytes == 0
        assert m.estimated_cost_usd == 0.0

    def test_all_fields(self):
        m = ExecutionMetadata(
            execution_time_ms=100.5,
            rows_returned=10,
            data_scanned_bytes=204800,
            estimated_cost_usd=0.001,
            execution_mode="athena",
        )
        assert m.execution_time_ms == 100.5
        assert m.execution_mode == "athena"
