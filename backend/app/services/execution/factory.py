"""
factory.py — Executor factory with automatic fallback.

Selects the appropriate QueryExecutor based on the USE_ATHENA setting:

  USE_ATHENA=False (default)
    → MockExecutor   — zero dependencies, instant, local dev

  USE_ATHENA=True
    → AthenaExecutor — production, real AWS Athena
      If AthenaExecutor fails to initialise (boto3 missing, bad config,
      network unreachable) the factory automatically falls back to
      MockExecutor and logs a warning so the service keeps running.

Usage:
    from app.services.execution.factory import get_executor

    executor = get_executor()
    result   = await executor.execute("SELECT region, SUM(amount) FROM sales GROUP BY region")
"""

import logging

from app.config import get_settings
from app.services.execution.base import QueryExecutor
from app.services.execution.mock_executor import MockExecutor

logger = logging.getLogger(__name__)
settings = get_settings()

# Import AthenaExecutor at module level so it can be patched in tests.
# If boto3 is not installed the attribute is set to None and get_executor()
# will fall back to MockExecutor at runtime.
try:
    from app.services.execution.athena_executor import AthenaExecutor
except ImportError:
    AthenaExecutor = None  # type: ignore[assignment,misc]


def get_executor() -> QueryExecutor:
    """
    Return the appropriate QueryExecutor for the current environment.

    Resolution order:
      1. USE_ATHENA=False   → MockExecutor (always safe)
      2. USE_ATHENA=True    → AthenaExecutor
         - AthenaExecutor is None (boto3 not installed) → falls back to MockExecutor
         - On ImportError   → falls back to MockExecutor (boto3 not installed)
         - On ValueError    → falls back to MockExecutor (bad config)
         - On any Exception → falls back to MockExecutor (connectivity, etc.)

    Returns:
        A QueryExecutor instance ready to call .execute(sql).
    """
    if not settings.USE_ATHENA:
        logger.debug("USE_ATHENA=False — using MockExecutor")
        return MockExecutor()

    # --- Attempt to build AthenaExecutor -----------------------------------
    if AthenaExecutor is None:
        logger.warning(
            "USE_ATHENA=True but boto3 is not installed — "
            "falling back to MockExecutor. Install boto3 for Athena support."
        )
        return MockExecutor()

    try:
        executor = AthenaExecutor()
        logger.info("USE_ATHENA=True — AthenaExecutor active")
        return executor

    except ImportError:
        logger.warning(
            "USE_ATHENA=True but boto3 is not installed — "
            "falling back to MockExecutor. Install boto3 for Athena support."
        )
        return MockExecutor()

    except ValueError as exc:
        logger.warning(
            "USE_ATHENA=True but Athena configuration is incomplete (%s) — "
            "falling back to MockExecutor.",
            exc,
        )
        return MockExecutor()

    except Exception as exc:
        logger.error(
            "USE_ATHENA=True but AthenaExecutor failed to initialise (%s) — "
            "falling back to MockExecutor.",
            exc,
            exc_info=True,
        )
        return MockExecutor()
