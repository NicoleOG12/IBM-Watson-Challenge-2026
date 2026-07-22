"""
cost_controller.py — HTTP endpoint for SQL cost estimation.

Exposes a standalone POST /cost/estimate endpoint so the frontend can
request a cost estimate independently (e.g. before showing the approval dialog),
as well as receiving estimates embedded in standard QueryResponse objects.
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.cost import CostEstimate
from app.services.cost_service import estimate_cost

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Cost"])


class CostEstimateRequest(BaseModel):
    sql: str = Field(..., description="The SQL query to estimate cost for")


@router.post(
    "/cost/estimate",
    response_model=CostEstimate,
    summary="Estimate query cost",
)
async def estimate_query_cost(request: CostEstimateRequest) -> CostEstimate:
    """
    Return a formula-based cost estimate for the provided SQL query.

    The estimate is **purely informational** — it does not validate or execute
    the SQL. The response always includes `is_mock: true`.

    - **sql**: the SQL string to analyse
    """
    logger.info("Cost estimate requested")
    return estimate_cost(request.sql)
