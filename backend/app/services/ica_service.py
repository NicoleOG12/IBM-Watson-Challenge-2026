"""
ica_service.py — IBM Consulting Advantage (ICA) integration for NL → SQL generation.

Flow:
    1. Build a schema-aware system prompt + user message
    2. POST to the ICA chat-completions endpoint for the configured assistant
    3. Parse the JSON response → LLMResult(sql, explanation)

The ICA API is OpenAI-compatible, so requests follow the standard
chat-completions shape:
    POST /ica/v1/assistants/{assistant_id}/chat/completions
    Authorization: Bearer {ICA_KEY}

Set ICA_MOCK=True in .env (the default) to use deterministic mock responses
with no API call — identical behaviour to WATSONX_MOCK.

Set ICA_MOCK=False and supply ICA_KEY + ICA_ASSISTANT_ID to use the real API.
"""

import json
import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.models.llm import LLMRequest, LLMResult
from app.models.schema import SchemaContext
from app.services.watsonx_service import (
    _is_destructive_intent,
    _is_safe_sql,
    _mock_response,
    build_prompt,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# ICA chat-completions API call
# ---------------------------------------------------------------------------

async def _call_ica_api(prompt: str) -> str:
    """
    POST a chat-completions request to ICA and return the model's
    raw message content string.

    Endpoint: POST /chat-models/chat/completions
    The model is selected via the "model" field using ICA_MODEL_ID.
    The system message carries the full NL→SQL prompt (schema-aware or
    fallback); the user message triggers execution.

    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    url = f"{settings.ICA_BASE_URL}/chat-models/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.ICA_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ICA_MODEL_ID,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate the SQL query now."},
        ],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    # OpenAI-compatible envelope: choices[0].message.content
    return data["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_ica_output(raw_text: str, original_query: str) -> LLMResult:
    """
    Parse the raw ICA response into an LLMResult.

    The model is instructed (via system prompt) to return a JSON object with
    exactly two keys: "sql" and "explanation". Falls back to a safe error
    result if parsing fails.
    """
    # Strip optional markdown code fences the model may wrap around the JSON
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
        sql = data.get("sql", "").strip()
        explanation = data.get("explanation", "").strip()

        if not _is_safe_sql(sql):
            logger.warning(
                "ICA returned a forbidden SQL verb — rejecting",
                extra={"sql": sql},
            )
            return LLMResult(
                sql="",
                explanation=(
                    "The generated query contained disallowed operations "
                    "(DELETE / UPDATE / DROP, etc.) and was rejected for safety."
                ),
            )

        return LLMResult(sql=sql, explanation=explanation)

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error(
            "Failed to parse ICA output",
            exc_info=exc,
            extra={"raw": raw_text},
        )
        return LLMResult(
            sql="",
            explanation=(
                "The model returned an unstructured response that could not be parsed. "
                f"Original query: '{original_query}'"
            ),
        )


# ---------------------------------------------------------------------------
# Public entry point — same signature as watsonx_service.generate_sql
# ---------------------------------------------------------------------------

async def generate_sql(
    llm_request: LLMRequest,
    schema: Optional[SchemaContext] = None,
) -> LLMResult:
    """
    Main entry point called by QueryService.

    If ICA_MOCK=True (default for local dev), delegates to the shared
    mock_response helper — identical mock behaviour as the watsonx service.

    Otherwise:
      1. Blocks destructive intent before any API call.
      2. Builds a schema-aware (or fallback) prompt.
      3. Calls the ICA chat-completions endpoint.
      4. Parses and validates the response.

    Args:
        llm_request: The LLM request with the natural language query.
        schema:      Optional SchemaContext for schema-aware prompting.
    """
    if settings.ICA_MOCK:
        logger.info("ICA_MOCK=True — returning mock LLM response")
        return _mock_response(llm_request.natural_language_query)

    # Guard: refuse destructive intent before sending to the real LLM
    if _is_destructive_intent(llm_request.natural_language_query):
        logger.info(
            "Destructive intent detected — refusing before ICA call",
            extra={"query": llm_request.natural_language_query},
        )
        return LLMResult(
            sql="",
            explanation=(
                "I can only run read-only analytical queries. "
                "Data modification and DDL operations (DELETE, DROP, INSERT, "
                "UPDATE, ALTER, TRUNCATE, etc.) are not permitted."
            ),
        )

    if not settings.ICA_KEY:
        logger.error("ICA_KEY is not configured — cannot call ICA API")
        return LLMResult(
            sql="",
            explanation="ICA API key is not configured. Set ICA_KEY in your .env file.",
        )

    prompt = build_prompt(llm_request, schema=schema)
    logger.debug(
        "Sending prompt to ICA",
        extra={
            "model_id": settings.ICA_MODEL_ID,
            "schema_aware": schema is not None,
        },
    )

    try:
        raw_text = await _call_ica_api(prompt)
        return _parse_ica_output(raw_text, llm_request.natural_language_query)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "ICA API returned an error",
            exc_info=exc,
            extra={"status_code": exc.response.status_code},
        )
        raise
