"""
cost.py — Pydantic model for SQL cost estimation results.
"""

from pydantic import BaseModel, Field


class CostEstimate(BaseModel):
    """
    Result of a formula-based SQL cost estimation.

    All estimates are mocks — no real query planner is invoked.
    The `is_mock` flag is always True to make this explicit to callers.
    """

    bytes_scanned: int = Field(
        ...,
        description="Estimated bytes scanned, based on table count and filter presence",
    )
    estimated_cost_usd: float = Field(
        ...,
        description="Estimated query cost in USD at $5.00 per TB (BigQuery standard rate)",
    )
    table_count: int = Field(
        ...,
        description="Number of distinct tables detected in the SQL",
    )
    has_filter: bool = Field(
        ...,
        description="Whether a WHERE clause was detected (reduces estimated scan size)",
    )
    is_mock: bool = Field(
        default=True,
        description="Always True — this estimate is formula-based, not from a real query planner",
    )
