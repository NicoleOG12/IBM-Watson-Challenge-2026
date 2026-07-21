"""
watsonx_service.py — IBM watsonx.ai integration for NL → SQL generation.

Flow:
    1. Build a schema-aware prompt (via schema_service) + user query
    2. Call the watsonx.ai Inference REST endpoint (or return a mock)
    3. Parse the JSON response envelope → LLMResult(sql, explanation)

Prompt engineering enforces:
    - Only SELECT statements are allowed
    - No DELETE / UPDATE / DROP / INSERT / ALTER / TRUNCATE / EXEC
    - Only analytical / read-only queries

Set WATSONX_MOCK=True in .env to bypass the API and get a deterministic
mock response — useful during local development and CI.
"""

import json
import logging
import re
from typing import Optional

import httpx

from app.config import get_settings
from app.models.llm import LLMRequest, LLMResult
from app.models.schema import SchemaContext

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Fallback prompt template (used when no schema is available)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_FALLBACK = """\
You are an expert SQL analyst assistant integrated into an AI-powered data copilot.
Your ONLY job is to translate a natural language question into a valid SQL SELECT query.

STRICT RULES — you MUST follow all of them:
1. Output ONLY a valid SQL SELECT statement. No other SQL verbs are permitted.
2. NEVER generate DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, CREATE, EXEC,
   GRANT, REVOKE, MERGE, or any other data-modification or DDL statement.
3. If the user's question implies a data change, politely explain that you can
   only run analytical (read-only) queries and set sql to an empty string.
4. Always include an explanation field that describes in plain English what
   the SQL does.
5. Return your response as valid JSON with exactly these two keys:
   { "sql": "<SELECT statement>", "explanation": "<plain English explanation>" }
6. Do not include markdown code fences, comments, or any text outside the JSON object.

EXAMPLE INPUT:
  Show me total sales by region for last quarter.

EXAMPLE OUTPUT:
  {
    "sql": "SELECT region, SUM(amount) AS total_sales FROM sales WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') GROUP BY region ORDER BY total_sales DESC",
    "explanation": "Aggregates total sales by region for the previous quarter, ordered from highest to lowest."
  }

Translate the following question into a SQL SELECT query following the rules above.

Question: {query}
"""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_FORBIDDEN_PATTERN = re.compile(
    r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|"
    r"GRANT|REVOKE|MERGE|REPLACE)\b",
    re.IGNORECASE,
)


def _is_safe_sql(sql: str) -> bool:
    """Return True only if the SQL contains no forbidden verbs."""
    return not bool(_FORBIDDEN_PATTERN.search(sql))


# ---------------------------------------------------------------------------
# Mock response
# ---------------------------------------------------------------------------

def _mock_response(query: str) -> LLMResult:
    """
    Returns a deterministic mock LLMResult.
    Used when WATSONX_MOCK=True or when the API is unreachable.
    """
    mock_sql = (
        "SELECT region, SUM(amount) AS total_sales "
        "FROM sales "
        "WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') "
        "GROUP BY region "
        "ORDER BY total_sales DESC"
    )
    return LLMResult(
        sql=mock_sql,
        explanation=(
            "[MOCK] Aggregates total sales by region for the previous quarter, "
            f"in response to: '{query}'"
        ),
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(llm_request: LLMRequest, schema: Optional[SchemaContext] = None) -> str:
    """
    Build the prompt sent to the watsonx.ai endpoint.

    If a SchemaContext is provided, delegates to build_context_prompt() for
    schema-aware prompting (higher SQL accuracy).
    Falls back to the generic system prompt when no schema is available.

    Args:
        llm_request: The LLM request containing the natural language query.
        schema:      Optional schema context loaded from schema.json.

    Returns:
        A single prompt string ready to be sent to the LLM.
    """
    if schema is not None:
        from app.services.schema_service import build_context_prompt
        return build_context_prompt(schema, llm_request.natural_language_query)
    return _SYSTEM_PROMPT_FALLBACK.format(query=llm_request.natural_language_query)


# ---------------------------------------------------------------------------
# Real API call
# ---------------------------------------------------------------------------

async def _call_watsonx_api(prompt: str) -> str:
    """
    POST to the watsonx.ai text-generation endpoint and return the raw
    generated text string.

    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    url = f"{settings.WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {settings.WATSONX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model_id": settings.WATSONX_MODEL_ID,
        "project_id": settings.WATSONX_PROJECT_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": settings.WATSONX_MAX_NEW_TOKENS,
            "temperature": settings.WATSONX_TEMPERATURE,
            "stop_sequences": ["}"],
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    # watsonx response envelope: results[0].generated_text
    generated_text: str = data["results"][0]["generated_text"]
    # The stop_sequence "}" is consumed — re-append it so we get valid JSON
    return generated_text.strip() + "}"


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_llm_output(raw_text: str, original_query: str) -> LLMResult:
    """
    Parse the raw model output into an LLMResult.
    Falls back to a safe error result if parsing fails.
    """
    try:
        data = json.loads(raw_text)
        sql = data.get("sql", "").strip()
        explanation = data.get("explanation", "").strip()

        if not _is_safe_sql(sql):
            logger.warning("LLM returned a forbidden SQL verb — rejecting", extra={"sql": sql})
            return LLMResult(
                sql="",
                explanation=(
                    "The generated query contained disallowed operations "
                    "(DELETE / UPDATE / DROP, etc.) and was rejected for safety."
                ),
            )

        return LLMResult(sql=sql, explanation=explanation)

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to parse LLM output", exc_info=exc, extra={"raw": raw_text})
        return LLMResult(
            sql="",
            explanation=(
                "The model returned an unstructured response that could not be parsed. "
                f"Original query: '{original_query}'"
            ),
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_sql(
    llm_request: LLMRequest,
    schema: Optional[SchemaContext] = None,
) -> LLMResult:
    """
    Main entry point called by QueryService.

    If WATSONX_MOCK is True (default for local dev), returns a mock result.
    Otherwise calls the real watsonx.ai API and parses the response.

    Args:
        llm_request: The LLM request with the natural language query.
        schema:      Optional SchemaContext for schema-aware prompting.
    """
    if settings.WATSONX_MOCK:
        logger.info("WATSONX_MOCK=True — returning mock LLM response")
        return _mock_response(llm_request.natural_language_query)

    prompt = build_prompt(llm_request, schema=schema)
    logger.debug(
        "Sending prompt to watsonx",
        extra={"model": settings.WATSONX_MODEL_ID, "schema_aware": schema is not None},
    )

    try:
        raw_text = await _call_watsonx_api(prompt)
        return _parse_llm_output(raw_text, llm_request.natural_language_query)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "watsonx API returned an error",
            exc_info=exc,
            extra={"status_code": exc.response.status_code},
        )
        raise
