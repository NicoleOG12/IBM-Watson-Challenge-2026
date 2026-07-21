"""
query_service.py — Business logic layer for query orchestration.

Pipeline:
    1. Sanitise input
    2. Retrieve user context from memory_service (conversation history)
    3. Load schema context (schema_service)
    4. Translate NL → SQL via IBM watsonx.ai (schema-aware, history-aware)
    5. Validate generated SQL (security layer)
    6. Estimate query cost (informational, does not block execution)
    7. Execute SQL (mock SQLite or live connector via execution_service)
    8. Analyse results and generate insights (insights_service)
    9. Format response via response_formatter
   10. Save interaction to memory + auto-save approved query
   11. Emit audit record
   12. Return structured QueryResponse
"""

import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.query import QueryRequest, QueryResponse
from app.models.llm import LLMRequest, LLMResult
from app.models.schema import SchemaContext
from app.models.execution import QueryResult
from app.models.insight import InsightReport
from app.models.response import FormattedResponse
from app.models.cost import CostEstimate
from app.models.saved_query import SavedQuery
from app.services.watsonx_service import generate_sql
from app.services.schema_service import load_schema
from app.services.execution_service import execute_query
from app.services.insights_service import analyze_results
from app.services.response_formatter import format_response, format_error_response
from app.services.memory_service import get_context, save_interaction
from app.services.audit_service import record_query
from app.services.cost_service import estimate_cost
from app.services.saved_queries_service import auto_save
from app.services.query_matching_service import find_matching_query
from app.services.next_steps_service import generate_next_steps
from app.security.sql_validator import validate_sql
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryService:
    """
    Orchestrates a natural-language query through the processing pipeline.
    Step 2 loads conversation memory; Step 4 uses schema+history-aware prompting.
    """

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        query_id = str(uuid.uuid4())
        _start = time.perf_counter()
        logger.info(
            "Processing query",
            extra={"query_id": query_id, "user_id": request.user_id},
        )

        # Step 1: Sanitise
        sanitised_query = self._sanitise(request.natural_language_query)

        # Step 2: Load conversation context from memory
        context = self._retrieve_context(request.user_id)

        # Step 3: Load schema context
        schema = self._load_schema_context()

        # Step 3.5: Check saved queries for a keyword match (skip LLM if found)
        matched: Optional[SavedQuery] = find_matching_query(
            sanitised_query, user_id=request.user_id
        )
        if matched:
            logger.info(
                "Reusing matched saved query",
                extra={"query_id": query_id, "saved_id": matched.id},
            )
            llm_result = LLMResult(
                sql=matched.sql,
                explanation=f"Reusing saved query: '{matched.question}'",
            )
        else:
            matched = None

        # Step 4: NL → SQL via watsonx (schema-aware, skipped when match found)
        if not matched:
            llm_result: LLMResult = await self._translate_to_sql(
                sanitised_query, request.user_id, context, schema
            )

        # Step 5: Validate generated SQL
        validation = validate_sql(llm_result.sql)
        if not validation.valid:
            elapsed_ms = (time.perf_counter() - _start) * 1000
            logger.warning(
                "SQL validation failed",
                extra={"query_id": query_id, "reason": validation.reason},
            )
            record_query(
                user_id=request.user_id,
                natural_language_query=sanitised_query,
                generated_sql=llm_result.sql,
                status="rejected",
                execution_time_ms=elapsed_ms,
                error=validation.reason,
            )
            return QueryResponse(
                query_id=query_id,
                user_id=request.user_id,
                natural_language_query=request.natural_language_query,
                result=format_error_response(llm_result.sql, validation.reason),
                status="rejected",
                timestamp=datetime.now(timezone.utc),
            )

        # Step 6: Estimate cost (informational — does not block execution)
        cost: CostEstimate = estimate_cost(llm_result.sql)

        # Step 7: Execute SQL
        query_result: QueryResult = await self._execute_query(llm_result.sql)

        # Step 8: Analyse results (with configurable thresholds)
        variation_threshold = (
            request.anomaly_rules.variation_threshold
            if request.anomaly_rules and request.anomaly_rules.variation_threshold is not None
            else settings.ANOMALY_VARIATION_THRESHOLD
        )
        iqr_multiplier = (
            request.anomaly_rules.iqr_multiplier
            if request.anomaly_rules and request.anomaly_rules.iqr_multiplier is not None
            else settings.ANOMALY_IQR_MULTIPLIER
        )
        insights: InsightReport = self._analyse(
            query_result,
            variation_threshold=variation_threshold,
            iqr_multiplier=iqr_multiplier,
        )

        # Step 9: Generate next steps
        next_steps = await generate_next_steps(
            question=sanitised_query,
            insights=insights,
            rows_sample=query_result.rows[:3],
        )

        # Step 10: Format response
        formatted: FormattedResponse = self._format_result(query_result, llm_result, insights)

        # Step 11: Persist interaction to memory + auto-save approved query
        save_interaction(
            request.user_id,
            sanitised_query,
            llm_result.sql,
            status="success",
            row_count=query_result.row_count,
        )
        auto_save(
            user_id=request.user_id,
            question=sanitised_query,
            sql=llm_result.sql,
        )

        # Step 12: Emit audit record
        elapsed_ms = (time.perf_counter() - _start) * 1000
        record_query(
            user_id=request.user_id,
            natural_language_query=sanitised_query,
            generated_sql=llm_result.sql,
            status="success",
            execution_time_ms=elapsed_ms,
            row_count=query_result.row_count,
        )

        return QueryResponse(
            query_id=query_id,
            user_id=request.user_id,
            natural_language_query=request.natural_language_query,
            result=formatted.model_dump(),
            cost_estimate=cost,
            next_steps=next_steps,
            matched_query=matched,
            status="success",
            timestamp=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sanitise(self, query: str) -> str:
        """Strip leading/trailing whitespace; extend with injection guards as needed."""
        return query.strip()

    def _retrieve_context(self, user_id: str) -> dict:
        """
        Load the user's conversation history from memory_service.
        Returns a context dict injected into the LLM prompt.
        """
        return get_context(user_id)

    def _load_schema_context(self) -> Optional[SchemaContext]:
        """
        Load schema metadata from data/schema.json.
        Returns None (gracefully) if the file is missing, so the pipeline
        degrades to schema-less prompting rather than crashing.
        """
        try:
            return load_schema()
        except FileNotFoundError:
            logger.warning("schema.json not found — falling back to schema-less prompting")
            return None

    async def _translate_to_sql(
        self, query: str, user_id: str, context: dict, schema: Optional[SchemaContext]
    ) -> LLMResult:
        """
        Calls the watsonx service with schema-aware prompting.
        Returns an LLMResult with `sql` and `explanation` fields.
        """
        llm_request = LLMRequest(
            natural_language_query=query,
            user_id=user_id,
            context=context,
        )
        return await generate_sql(llm_request, schema=schema)

    async def _execute_query(self, sql: str) -> QueryResult:
        """
        Execute the validated SQL via the execution service.
        Returns a QueryResult with rows, columns, and row_count.
        """
        return await execute_query(sql)

    def _analyse(
        self,
        query_result: QueryResult,
        variation_threshold: float = 30.0,
        iqr_multiplier: float = 1.5,
    ) -> InsightReport:
        """Run the insights service over the execution result with configurable thresholds."""
        return analyze_results(
            query_result.rows,
            query_result.columns,
            variation_threshold=variation_threshold,
            iqr_multiplier=iqr_multiplier,
        )

    def _format_result(
        self,
        query_result: QueryResult,
        llm_result: LLMResult,
        insights: InsightReport,
    ) -> FormattedResponse:
        """Delegate to response_formatter to assemble the canonical response shape."""
        return format_response(llm_result, query_result, insights)
