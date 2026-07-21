"""
query_controller.py — Request/response handling for query endpoints.

Keeps route handler functions thin: validate input (via Pydantic),
delegate to the service layer, and shape the HTTP response.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.query import QueryRequest, QueryResponse, HealthResponse
from app.services.query_service import QueryService
from app.config import get_settings, Settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_query_service() -> QueryService:
    """Dependency injection factory — swap for a mock in tests."""
    return QueryService()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a natural language query",
    tags=["Query"],
)
async def handle_query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    """
    Receive a natural language query from a user and return a structured result.

    - **user_id**: unique identifier of the requesting user
    - **natural_language_query**: the question posed in plain English (or any language)
    """
    try:
        return await service.process_query(request)
    except Exception as exc:
        logger.exception("Unexpected error while processing query", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your query.",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    tags=["Health"],
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Returns the current health status, version, and environment of the service."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
