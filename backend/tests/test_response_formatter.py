"""
test_response_formatter.py — Unit tests for app/services/response_formatter.py

Run with:
    pytest tests/test_response_formatter.py -v
"""

import pytest
from app.models.llm import LLMResult
from app.models.execution import QueryResult
from app.models.insight import InsightReport, Insight
from app.models.response import FormattedResponse, DataPayload
from app.services.response_formatter import format_response, format_error_response


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _make_llm(sql="SELECT * FROM sales", explanation="Returns all sales.") -> LLMResult:
    return LLMResult(sql=sql, explanation=explanation)


def _make_qr(
    rows=None, columns=None, row_count=0, execution_mode="mock", error=None
) -> QueryResult:
    return QueryResult(
        rows=rows or [],
        columns=columns or [],
        row_count=row_count,
        execution_mode=execution_mode,
        error=error,
    )


def _make_insights(
    row_count=2,
    summary="2 record(s) analysed. No anomalies detected.",
    key_insights=None,
    trends=None,
    anomalies=None,
) -> InsightReport:
    return InsightReport(
        row_count=row_count,
        columns_analyzed=["region", "total_sales"],
        key_insights=key_insights or [],
        trends=trends or [],
        anomalies=anomalies or [],
        summary=summary,
    )


ROWS = [
    {"region": "North", "total_sales": "18450.75"},
    {"region": "East",  "total_sales": "15230.00"},
]
COLUMNS = ["region", "total_sales"]


# ---------------------------------------------------------------------------
# 1. Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_formatted_response(self):
        result = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        assert isinstance(result, FormattedResponse)

    def test_model_dump_is_dict(self):
        result = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        d = result.model_dump()
        assert isinstance(d, dict)


# ---------------------------------------------------------------------------
# 2. Top-level keys always present
# ---------------------------------------------------------------------------

class TestTopLevelKeys:
    def test_sql_present(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        assert hasattr(r, "sql")

    def test_explanation_present(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        assert hasattr(r, "explanation")

    def test_data_present(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        assert hasattr(r, "data")

    def test_insights_present(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        assert hasattr(r, "insights")

    def test_model_dump_has_four_keys(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "No data."))
        d = r.model_dump()
        for key in ("sql", "explanation", "data", "insights"):
            assert key in d, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 3. SQL and explanation pass-through
# ---------------------------------------------------------------------------

class TestSqlAndExplanation:
    def test_sql_value(self):
        r = format_response(_make_llm(sql="SELECT 1"), _make_qr(), _make_insights(0, "x"))
        assert r.sql == "SELECT 1"

    def test_explanation_value(self):
        r = format_response(
            _make_llm(explanation="Returns the number 1."),
            _make_qr(),
            _make_insights(0, "x"),
        )
        assert r.explanation == "Returns the number 1."

    def test_sql_empty_string_allowed(self):
        r = format_response(_make_llm(sql=""), _make_qr(), _make_insights(0, "x"))
        assert r.sql == ""


# ---------------------------------------------------------------------------
# 4. DataPayload correctness
# ---------------------------------------------------------------------------

class TestDataPayload:
    def test_data_is_data_payload(self):
        qr = _make_qr(rows=ROWS, columns=COLUMNS, row_count=2)
        r = format_response(_make_llm(), qr, _make_insights())
        assert isinstance(r.data, DataPayload)

    def test_rows_passed_through(self):
        qr = _make_qr(rows=ROWS, columns=COLUMNS, row_count=2)
        r = format_response(_make_llm(), qr, _make_insights())
        assert r.data.rows == ROWS

    def test_columns_passed_through(self):
        qr = _make_qr(rows=ROWS, columns=COLUMNS, row_count=2)
        r = format_response(_make_llm(), qr, _make_insights())
        assert r.data.columns == COLUMNS

    def test_row_count_passed_through(self):
        qr = _make_qr(rows=ROWS, columns=COLUMNS, row_count=2)
        r = format_response(_make_llm(), qr, _make_insights())
        assert r.data.row_count == 2

    def test_execution_mode_passed_through(self):
        qr = _make_qr(execution_mode="live")
        r = format_response(_make_llm(), qr, _make_insights(0, "x"))
        assert r.data.execution_mode == "live"

    def test_empty_rows(self):
        qr = _make_qr()
        r = format_response(_make_llm(), qr, _make_insights(0, "No data."))
        assert r.data.rows == []
        assert r.data.row_count == 0


# ---------------------------------------------------------------------------
# 5. Insights pass-through
# ---------------------------------------------------------------------------

class TestInsightsPayload:
    def test_insights_is_dict(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights())
        assert isinstance(r.insights, dict)

    def test_insights_has_summary(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(summary="Test summary."))
        assert r.insights["summary"] == "Test summary."

    def test_insights_has_key_insights_list(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights())
        assert "key_insights" in r.insights
        assert isinstance(r.insights["key_insights"], list)

    def test_insights_has_trends_list(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights())
        assert "trends" in r.insights

    def test_insights_has_anomalies_list(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights())
        assert "anomalies" in r.insights

    def test_insight_objects_serialised(self):
        insight = Insight(category="key_insight", message="North is top.", value="18450", column="total_sales")
        ins = _make_insights(key_insights=[insight])
        r = format_response(_make_llm(), _make_qr(), ins)
        assert r.insights["key_insights"][0]["message"] == "North is top."


# ---------------------------------------------------------------------------
# 6. model_dump() shape matches spec
# ---------------------------------------------------------------------------

class TestModelDumpShape:
    def test_dump_sql(self):
        r = format_response(_make_llm(sql="SELECT region FROM sales"), _make_qr(), _make_insights(0, "x"))
        assert r.model_dump()["sql"] == "SELECT region FROM sales"

    def test_dump_data_is_dict(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "x"))
        assert isinstance(r.model_dump()["data"], dict)

    def test_dump_data_contains_rows(self):
        qr = _make_qr(rows=ROWS, columns=COLUMNS, row_count=2)
        r = format_response(_make_llm(), qr, _make_insights())
        d = r.model_dump()
        assert d["data"]["rows"] == ROWS

    def test_dump_insights_is_dict(self):
        r = format_response(_make_llm(), _make_qr(), _make_insights(0, "x"))
        assert isinstance(r.model_dump()["insights"], dict)


# ---------------------------------------------------------------------------
# 7. format_error_response
# ---------------------------------------------------------------------------

class TestFormatErrorResponse:
    def test_returns_dict(self):
        result = format_error_response("", "SQL was rejected.")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = format_error_response("SELECT 1", "Some error.")
        for key in ("sql", "explanation", "data", "insights", "error"):
            assert key in result

    def test_sql_passed_through(self):
        result = format_error_response("DROP TABLE x", "Forbidden verb.")
        assert result["sql"] == "DROP TABLE x"

    def test_error_equals_reason(self):
        result = format_error_response("", "Bad query.")
        assert result["error"] == "Bad query."

    def test_data_is_none(self):
        result = format_error_response("", "err")
        assert result["data"] is None

    def test_insights_is_none(self):
        result = format_error_response("", "err")
        assert result["insights"] is None

    def test_explanation_equals_reason(self):
        result = format_error_response("", "Rejected due to security policy.")
        assert result["explanation"] == "Rejected due to security policy."
