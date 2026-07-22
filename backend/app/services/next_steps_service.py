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
    "What was the total financial impact of this result?",
    "What are the trends over time for this data?",
    "Compare these results with the previous period.",
]


def _rule_based_suggestions(question: str) -> List[str]:
    """Return 3 generic but relevant follow-up suggestions."""
    q = question.lower()
    if any(k in q for k in ["revenue", "sales", "vend", "receita"]):
        return [
            "Which regions contributed the most to this result?",
            "Compare with the same period last year.",
            "Which products had the highest growth in the same period?",
        ]
    if any(k in q for k in ["customer", "client", "churn"]):
        return [
            "What is the average order value for these customers?",
            "Which segments show the highest churn risk?",
            "How has this metric evolved over the last 3 months?",
        ]
    return _FALLBACK_TEMPLATES[:]


# ---------------------------------------------------------------------------
# Watsonx API call
# ---------------------------------------------------------------------------

async def _call_ica_for_next_steps(prompt: str) -> List[str]:
    """
    Call the ICA chat-models endpoint to generate next steps.
    Returns a list of 3 strings, or raises on failure.
    """
    url = f"{settings.ICA_BASE_URL}/chat-models/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.ICA_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ICA_MODEL_ID,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    raw_text: str = response.json()["choices"][0]["message"]["content"].strip()

    # Extract JSON array from the response
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
    if settings.ICA_MOCK:
        logger.debug("ICA_MOCK=True — returning rule-based next steps")
        return _rule_based_suggestions(question)

    sample = rows_sample[:3]
    prompt = _PROMPT_TEMPLATE.format(
        question=question,
        summary=insights.summary,
        sample=json.dumps(sample, default=str, ensure_ascii=False),
    )

    try:
        suggestions = await _call_ica_for_next_steps(prompt)
        logger.info("Next steps generated via ICA", extra={"count": len(suggestions)})
        return suggestions
    except Exception as exc:
        logger.warning(
            "Next steps ICA call failed — falling back to rule-based",
            exc_info=exc,
        )
        return _rule_based_suggestions(question)
