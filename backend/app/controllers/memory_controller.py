"""
memory_controller.py — HTTP endpoints for conversation memory.

Allows clients (and admins) to inspect or clear per-user conversation
history without restarting the service.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.models.memory import UserMemory
from app.services.memory_service import get_user_memory, clear_memory, get_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get(
    "/{user_id}",
    response_model=UserMemory,
    summary="Get conversation memory for a user",
)
async def get_memory(user_id: str) -> UserMemory:
    """
    Return the full conversation history stored for **user_id**.

    Raises **404** if no history exists yet for that user.
    """
    memory = get_user_memory(user_id)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No memory found for user '{user_id}'.",
        )
    return memory


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear conversation memory for a user",
)
async def delete_memory(user_id: str) -> None:
    """
    Wipe all stored conversation history for **user_id**.

    Returns **204 No Content** regardless of whether any history existed.
    """
    clear_memory(user_id)
