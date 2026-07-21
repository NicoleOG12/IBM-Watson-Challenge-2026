"""
query_matching_service.py — Keyword-overlap matching against saved queries.

Before calling the LLM, checks whether the user's question closely
resembles an existing saved query (similarity ≥ 50% token overlap).
If a match is found, the saved SQL is reused directly — saving an LLM
call and providing a consistent, validated result.

Algorithm
---------
1. Tokenise both strings: lowercase, split on whitespace + punctuation,
   remove a small set of Portuguese/English stopwords.
2. Compute overlap ratio = |intersection| / |union|  (Jaccard similarity)
3. Return the SavedQuery with the highest ratio above the threshold,
   or None if no saved query meets the threshold.

Public API
----------
    from app.services.query_matching_service import find_matching_query

    match = find_matching_query(question, user_id)
    # returns SavedQuery | None
"""

import logging
import re
from typing import Optional, Set

from app.models.saved_query import SavedQuery
from app.services.saved_queries_service import get_saved_queries
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIMILARITY_THRESHOLD: float = 0.5

# Common stopwords (PT + EN) that carry no discriminating signal
_STOPWORDS: Set[str] = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "por",
    "para", "com", "que", "se", "na", "no", "nas", "nos", "um", "uma",
    "me", "te", "se", "nos", "vos", "the", "a", "an", "of", "for", "in",
    "on", "to", "by", "is", "are", "was", "were", "be", "been", "being",
    "show", "me", "give", "list", "get", "find", "what", "how", "which",
    "qual", "quais", "como", "onde", "quando", "mostre", "liste", "busque",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenise(text: str) -> Set[str]:
    """
    Lower-case, split on non-alphanumeric characters, remove stopwords.

    Returns a set of meaningful tokens.
    """
    tokens = re.split(r'[^a-záéíóúàèìòùâêîôûãõçñüä\w]+', text.lower(), flags=re.UNICODE)
    return {t for t in tokens if t and t not in _STOPWORDS and len(t) > 1}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def find_matching_query(
    question: str,
    user_id: Optional[str] = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> Optional[SavedQuery]:
    """
    Find the best-matching saved query for the given question.

    Searches saved queries belonging to `user_id` (all users if None).
    Returns the SavedQuery with the highest Jaccard similarity above
    `threshold`, or None if no match is found.

    Args:
        question:  The new natural language question to match.
        user_id:   Optional filter — only match against this user's queries.
        threshold: Minimum similarity score (default 0.5).

    Returns:
        The best-matching SavedQuery, or None.

    Example:
        >>> from app.services.saved_queries_service import auto_save
        >>> auto_save("u1", "total sales by region", "SELECT region, SUM(amount) FROM sales GROUP BY 1")
        >>> match = find_matching_query("sales grouped by region", user_id="u1")
        >>> match is not None
        True
    """
    candidates = get_saved_queries(user_id=user_id)
    if not candidates:
        return None

    q_tokens = _tokenise(question)
    best_score = 0.0
    best_match: Optional[SavedQuery] = None

    for saved in candidates:
        score = _jaccard(q_tokens, _tokenise(saved.question))
        if score > best_score:
            best_score = score
            best_match = saved

    if best_score >= threshold and best_match is not None:
        logger.info(
            "Matching saved query found",
            extra={
                "query_id": best_match.id,
                "score": round(best_score, 3),
                "question": question[:60],
            },
        )
        return best_match

    logger.debug(
        "No matching saved query above threshold",
        extra={"best_score": round(best_score, 3), "threshold": threshold},
    )
    return None
