"""
anomaly.py — Pydantic model for per-request anomaly detection rule overrides.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AnomalyRules(BaseModel):
    """
    Optional per-request overrides for anomaly detection thresholds.

    When provided in a QueryRequest, these values take precedence over the
    global defaults defined in config.py (ANOMALY_VARIATION_THRESHOLD and
    ANOMALY_IQR_MULTIPLIER).

    Leave any field as None to fall back to the global default.
    """

    variation_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Coefficient of variation (%) above which a column is flagged as "
            "highly variable. Overrides ANOMALY_VARIATION_THRESHOLD from config."
        ),
    )
    iqr_multiplier: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "IQR fence multiplier for outlier detection (standard = 1.5). "
            "Overrides ANOMALY_IQR_MULTIPLIER from config."
        ),
    )
