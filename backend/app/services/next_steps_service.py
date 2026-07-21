"""
next_steps_service.py — LLM-powered follow-up question generation.

After a query executes successfully, calls watsonx.ai with the original
question + a brief results summary to generate 3 follow-up suggestions
that help the user explore the data further.

Falls back to rule-based suggestions when WATSONX_MOCK=True or when
the API call fails, so the feature always returns something useful.

Public API
----------
    from app.services.next_steps_service import generate_next_steps

    suggestions = await generate_next_steps(question, insight_summary, rows_sample)
    # returns list[str]  (always 3 items)
"""

import json
import logging
import re
from typing import Any, Dict, List

import httpx

from app.config import get_settings
from app.models.insight import InsightReport

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
You are a data analyst assistant. A user just ran a database query and saw the results below.

Original question: {question}

Results summary: {summary}

Sample data (first 3 rows): {sample}

Generate exactly 3 short follow-up questions the user could ask next to explore this data further.
The questions should be in the same language as the original question.
Return ONLY a JSON array of 3 strings, like: ["question 1", "question 2", "question 3"]
Do not include any other text, explanation, or markdown.
"""

# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------

_FALLBACK_TEMPLATES = [
    "Qual foi o impacto financeiro total deste resultado?",
    "Quais são as tendências ao longo do tempo para estes dados?",
    "Compare estes resultados com o período anterior.",
]


def _rule_based_suggestions(question: str) -> List[str]:
    """Return 3 generic but relevant follow-up suggestions."""
    q = question.lower()
    if any(k in q for k in ["vend", "revenue", "receita", "sales"]):
        return [
            "Quais regiões contribuíram mais para este resultado?",
            "Compare com o mesmo período do ano anterior.",
            "Quais produtos tiveram maior crescimento no mesmo período?",
        ]
    if any(k in q for k in ["client", "customer", "churn"]):
        return [
            "Qual é o ticket médio destes clientes?",
            "Quais segmentos apresentam maior risco de churn?",
            "Como evoluiu este indicador nos últimos 3 meses?",
        ]
    return _FALLBACK_TEMPLATES[:]


# ---------------------------------------------------------------------------
# Watsonx API call
# ---------------------------------------------------------------------------

async def _call_watsonx_for_next_steps(prompt: str) -> List[str]:
    """
    Call the watsonx.ai text generation endpoint to generate next steps.
    Returns a list of strings, or raises on failure.
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
            "max_new_tokens": 256,
            "temperature": 0.3,
            "stop_sequences": ["]"],
        },
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    raw_text: str = data["results"][0]["generated_text"].strip() + "]"

    # Extract JSON array from the raw text
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON array in response: {raw_text!r}")

    suggestions: List[str] = json.loads(match.group(0))
    if not isinstance(suggestions, list) or len(suggestions) < 1:
        raise ValueError(f"Unexpected suggestions format: {suggestions}")

    # Ensure exactly 3
    suggestions = suggestions[:3]
    while len(suggestions) < 3:
        suggestions.append(_FALLBACK_TEMPLATES[len(suggestions)])

    return suggestions


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_next_steps(
    question: str,
    insights: InsightReport,
    rows_sample: List[Dict[str, Any]],
) -> List[str]:
    """
    Generate 3 follow-up question suggestions for the user.

    Uses watsonx.ai when WATSONX_MOCK=False; returns rule-based
    suggestions when mocking or when the API call fails.

    Args:
        question:    The original natural language question.
        insights:    The InsightReport from the execution (summary used in prompt).
        rows_sample: First few rows of the result (at most 3 used).

    Returns:
        List of exactly 3 follow-up question strings.
    """
    if settings.WATSONX_MOCK:
        logger.debug("WATSONX_MOCK=True — returning rule-based next steps")
        return _rule_based_suggestions(question)

    sample = rows_sample[:3]
    prompt = _PROMPT_TEMPLATE.format(
        question=question,
        summary=insights.summary,
        sample=json.dumps(sample, default=str, ensure_ascii=False),
    )

    try:
        suggestions = await _call_watsonx_for_next_steps(prompt)
        logger.info("Next steps generated via LLM", extra={"count": len(suggestions)})
        return suggestions
    except Exception as exc:
        logger.warning(
            "Next steps LLM call failed — falling back to rule-based",
            exc_info=exc,
        )
        return _rule_based_suggestions(question)
