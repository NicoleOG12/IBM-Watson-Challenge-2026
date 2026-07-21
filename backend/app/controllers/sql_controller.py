"""
sql_controller.py — Standalone SQL validation endpoint.

Exposes the existing sql_validator logic as a dedicated HTTP endpoint so the
frontend can validate SQL before presenting it to the user for approval,
without triggering a full query execution.
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.security.sql_validator import validate_sql

logger = logging.getLogger(__name__)
router = APIRouter(tags=["SQL"])


class SqlValidateRequest(BaseModel):
    sql: str = Field(..., description="The SQL string to validate")


class SqlValidateResponse(BaseModel):
    valid: bool = Field(..., description="Whether the SQL passed all validation checks")
    reason: str = Field(..., description="Human-readable explanation of the validation result")


@router.post(
    "/sql/validate",
    response_model=SqlValidateResponse,
    summary="Validate a SQL query",
)
async def validate_sql_endpoint(request: SqlValidateRequest) -> SqlValidateResponse:
    """
    Validate a SQL string against the security ruleset.

    Checks performed:
    - Non-empty
    - No multiple statements (semicolon injection)
    - No forbidden injection patterns
    - No forbidden verbs (DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, etc.)
    - Must start with SELECT or WITH ... SELECT

    Returns `valid: true` and an empty `reason` on success, or
    `valid: false` with a descriptive `reason` on failure.

    - **sql**: the SQL string to validate
    """
    result = validate_sql(request.sql)
    logger.info(
        "SQL validation requested",
        extra={"valid": result.valid, "reason": result.reason or "ok"},
    )
    return SqlValidateResponse(valid=result.valid, reason=result.reason)
