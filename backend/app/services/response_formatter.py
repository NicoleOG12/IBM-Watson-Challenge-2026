"""
response_formatter.py — Canonical API response assembly.

Responsibility: take the three upstream artefacts produced by the pipeline
(LLM result, execution result, insights report) and assemble them into the
stable FormattedResponse shape that the frontend consumes.

Keeping this as a dedicated service means:
  - The response contract is defined in one place.
  - query_service stays focused on orchestration, not serialisation.
  - The formatter can evolve independently (e.g. add chart hints, i18n,
    pagination) without touching any other layer.

Public API
----------
    from app.services.response_formatter import format_response

    formatted = format_response(llm_result, query_result, insights)
    # returns FormattedResponse
"""

import logging
from typing import Any

from app.models.llm import LLMResult
from app.models.execution import QueryResult
from app.models.insight import InsightReport
from app.models.response import DataPayload, FormattedResponse

logger = logging.getLogger(__name__)


def format_response(
    llm_result: LLMResult,
    query_result: QueryResult,
    insights: InsightReport,
) -> FormattedResponse:
    """
    Assemble the canonical API response from the three pipeline artefacts.

    The output always contains all four top-level keys (sql, explanation,
    data, insights) so the frontend can rely on a stable contract.

    Args:
        llm_result:   The LLM-generated SQL and plain-English explanation.
        query_result: Raw execution result — rows, columns, row_count.
        insights:     The InsightReport produced by insights_service.

    Returns:
        FormattedResponse — ready to be serialised as the `result` field
        inside a QueryResponse.

    Example:
        >>> from app.models.llm import LLMResult
        >>> from app.models.execution import QueryResult
        >>> from app.models.insight import InsightReport
        >>> llm  = LLMResult(sql="SELECT 1", explanation="Returns the number 1.")
        >>> qr   = QueryResult(execution_mode="mock")
        >>> ins  = InsightReport(row_count=0, columns_analyzed=[], summary="No data.")
        >>> resp = format_response(llm, qr, ins)
        >>> resp.sql
        'SELECT 1'
    """
    data = DataPayload(
        columns=query_result.columns,
        rows=query_result.rows,
        row_count=query_result.row_count,
        execution_mode=query_result.execution_mode,
    )

    formatted = FormattedResponse(
        sql=llm_result.sql,
        explanation=llm_result.explanation,
        data=data,
        insights=insights.model_dump(),
    )

    logger.debug(
        "Response formatted",
        extra={
            "row_count": query_result.row_count,
            "has_error": bool(query_result.error),
            "insight_count": len(insights.key_insights),
        },
    )

    return formatted


def format_error_response(
    sql: str,
    reason: str,
) -> dict:
    """
    Build a minimal error payload used when SQL validation fails or
    an unrecoverable error occurs before execution.

    Returns a plain dict (not FormattedResponse) so it can be stored
    directly in QueryResponse.result without wrapping extra fields.

    Args:
        sql:    The SQL string that was rejected (may be empty).
        reason: Human-readable explanation of why the query was rejected.

    Returns:
        {"sql": "...", "explanation": "...", "data": None, "insights": None, "error": "..."}
    """
    return {
        "sql": sql,
        "explanation": reason,
        "data": None,
        "insights": None,
        "error": reason,
    }
