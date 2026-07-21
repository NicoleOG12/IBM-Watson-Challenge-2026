"""
test_execution_service.py — Unit tests for the execution layer.

Run with:
    pytest tests/test_execution_service.py -v
"""

import sqlite3
import pytest

import app.services.execution_service as svc
from app.services.execution_service import execute_query, set_connector
from app.services.execution.mock_executor import MockExecutor
from app.models.execution import QueryResult


# ---------------------------------------------------------------------------
# Helper: call the mock executor's internal SQLite DB directly
# (previously _execute_mock was a module-level function; now it lives in
# MockExecutor._build_db + a direct cursor call — mirrored here)
# ---------------------------------------------------------------------------

def _execute_mock(sql: str):
    """Thin wrapper that runs SQL on the in-memory SQLite DB and returns (rows, cols)."""
    ex = MockExecutor()
    conn = ex._build_db()
    try:
        cursor = conn.execute(sql)
        cols = [d[0] for d in cursor.description or []]
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
        return rows, cols
    finally:
        conn.close()


async def _run(sql: str) -> QueryResult:
    return await execute_query(sql)


# ---------------------------------------------------------------------------
# 1. Mock dataset presence
# ---------------------------------------------------------------------------

class TestMockData:
    def test_mock_tables_exist(self):
        from data.mock_data import MOCK_TABLES
        assert set(MOCK_TABLES.keys()) == {"sales", "products", "customers", "orders"}

    def test_sales_has_rows(self):
        from data.mock_data import MOCK_TABLES
        assert len(MOCK_TABLES["sales"]) > 0

    def test_sales_row_has_expected_columns(self):
        from data.mock_data import MOCK_TABLES
        row = MOCK_TABLES["sales"][0]
        assert "region" in row
        assert "amount" in row
        assert "sale_date" in row

    def test_products_row_has_expected_columns(self):
        from data.mock_data import MOCK_TABLES
        row = MOCK_TABLES["products"][0]
        assert "name" in row
        assert "category" in row
        assert "unit_price" in row

    def test_customers_row_has_expected_columns(self):
        from data.mock_data import MOCK_TABLES
        row = MOCK_TABLES["customers"][0]
        assert "name" in row
        assert "region" in row
        assert "segment" in row

    def test_orders_row_has_expected_columns(self):
        from data.mock_data import MOCK_TABLES
        row = MOCK_TABLES["orders"][0]
        assert "status" in row
        assert "total_amount" in row


# ---------------------------------------------------------------------------
# 2. MockExecutor SQLite execution
# ---------------------------------------------------------------------------

class TestExecuteMock:
    def test_select_all_sales(self):
        rows, cols = _execute_mock("SELECT * FROM sales")
        assert len(rows) == 50
        assert "region" in cols

    def test_select_columns(self):
        rows, cols = _execute_mock("SELECT region, amount FROM sales")
        assert cols == ["region", "amount"]
        assert "region" in rows[0]
        assert "amount" in rows[0]

    def test_select_with_where(self):
        rows, cols = _execute_mock("SELECT * FROM sales WHERE region = 'North'")
        assert all(r["region"] == "North" for r in rows)

    def test_select_count(self):
        rows, cols = _execute_mock("SELECT COUNT(*) AS total FROM sales")
        assert cols == ["total"]
        assert int(rows[0]["total"]) == 50

    def test_select_products(self):
        rows, cols = _execute_mock("SELECT * FROM products")
        assert len(rows) == 20

    def test_select_customers(self):
        rows, cols = _execute_mock("SELECT * FROM customers")
        assert len(rows) == 15

    def test_select_orders(self):
        rows, cols = _execute_mock("SELECT * FROM orders")
        assert len(rows) == 30

    def test_select_with_limit(self):
        rows, cols = _execute_mock("SELECT * FROM sales LIMIT 5")
        assert len(rows) == 5

    def test_select_order_by(self):
        rows, cols = _execute_mock("SELECT region, amount FROM sales ORDER BY amount DESC LIMIT 3")
        amounts = [float(r["amount"]) for r in rows]
        assert amounts == sorted(amounts, reverse=True)

    def test_invalid_sql_raises(self):
        with pytest.raises(sqlite3.OperationalError):
            _execute_mock("SELECT * FROM nonexistent_table")


# ---------------------------------------------------------------------------
# 3. execute_query (async, mock mode via factory)
# ---------------------------------------------------------------------------

class TestExecuteQuery:
    @pytest.mark.asyncio
    async def test_returns_query_result(self):
        result = await _run("SELECT * FROM sales LIMIT 10")
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execution_mode_is_mock(self):
        result = await _run("SELECT * FROM sales")
        assert result.execution_mode == "mock-sqlite"

    @pytest.mark.asyncio
    async def test_row_count_matches_rows(self):
        result = await _run("SELECT * FROM sales LIMIT 7")
        assert result.row_count == len(result.rows)
        assert result.row_count == 7

    @pytest.mark.asyncio
    async def test_columns_populated(self):
        result = await _run("SELECT region, amount FROM sales LIMIT 1")
        assert "region" in result.columns
        assert "amount" in result.columns

    @pytest.mark.asyncio
    async def test_no_error_on_valid_sql(self):
        result = await _run("SELECT * FROM products")
        assert result.error is None

    @pytest.mark.asyncio
    async def test_error_on_invalid_table(self):
        result = await _run("SELECT * FROM ghost_table")
        assert result.error is not None
        assert "ghost_table" in result.error.lower() or "sql execution error" in result.error.lower()
        assert result.rows == []
        assert result.row_count == 0

    @pytest.mark.asyncio
    async def test_group_by_aggregation(self):
        result = await _run(
            "SELECT region, COUNT(*) AS cnt FROM sales GROUP BY region ORDER BY cnt DESC"
        )
        assert result.row_count > 0
        assert "region" in result.columns
        assert "cnt" in result.columns

    @pytest.mark.asyncio
    async def test_all_sales_rows_returned(self):
        result = await _run("SELECT * FROM sales")
        assert result.row_count == 50

    @pytest.mark.asyncio
    async def test_empty_result_is_valid(self):
        result = await _run("SELECT * FROM sales WHERE region = 'MarsBase'")
        assert result.error is None
        assert result.rows == []
        assert result.row_count == 0

    @pytest.mark.asyncio
    async def test_metadata_populated(self):
        result = await _run("SELECT * FROM sales LIMIT 1")
        assert result.metadata is not None
        assert result.metadata.execution_mode == "mock-sqlite"
        assert result.metadata.execution_time_ms >= 0


# ---------------------------------------------------------------------------
# 4. Pluggable legacy connector
# ---------------------------------------------------------------------------

class TestPluggableConnector:
    @pytest.mark.asyncio
    async def test_custom_connector_called(self, monkeypatch):
        """set_connector() should take precedence over the factory."""
        called_with = []

        async def fake_connector(sql: str):
            called_with.append(sql)
            return [{"id": "1"}], ["id"]

        monkeypatch.setattr(svc, "_custom_connector", fake_connector)
        result = await svc.execute_query("SELECT id FROM sales")

        assert called_with == ["SELECT id FROM sales"]
        assert result.execution_mode == "live"
        assert result.rows == [{"id": "1"}]

    @pytest.mark.asyncio
    async def test_no_connector_falls_back_to_factory(self, monkeypatch):
        """With no custom connector and USE_ATHENA=False the factory returns MockExecutor."""
        monkeypatch.setattr(svc, "_custom_connector", None)
        result = await svc.execute_query("SELECT * FROM sales LIMIT 1")
        assert result.execution_mode == "mock-sqlite"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_connector_error_returns_error_result(self, monkeypatch):
        async def broken_connector(sql: str):
            raise ConnectionError("DB is down")

        monkeypatch.setattr(svc, "_custom_connector", broken_connector)
        result = await svc.execute_query("SELECT 1")
        assert result.error is not None
        assert "DB is down" in result.error
        assert result.rows == []


# ---------------------------------------------------------------------------
# 5. QueryResult model
# ---------------------------------------------------------------------------

class TestQueryResultModel:
    def test_defaults(self):
        r = QueryResult(execution_mode="mock")
        assert r.rows == []
        assert r.row_count == 0
        assert r.columns == []
        assert r.error is None

    def test_error_field(self):
        r = QueryResult(execution_mode="mock", error="oops")
        assert r.error == "oops"
