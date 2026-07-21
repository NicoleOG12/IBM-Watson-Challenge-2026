"""
saved_query.py — Pydantic models for the saved/approved queries repository.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class SavedQuery(BaseModel):
    """A stored query that has been validated and is available for reuse."""

    id: str = Field(..., description="Unique identifier for this saved query")
    user_id: str = Field(..., description="User who owns this saved query")
    question: str = Field(..., description="Original natural language question")
    sql: str = Field(..., description="Generated and validated SQL")
    tables_used: List[str] = Field(
        default_factory=list,
        description="Tables referenced in the SQL",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Optional tags for categorisation (e.g. 'sales', 'finance')",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional human-readable description of what this query does",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this query was saved",
    )
    auto_saved: bool = Field(
        default=False,
        description="True when saved automatically on successful execution; False when saved explicitly by the user",
    )


class SaveQueryRequest(BaseModel):
    """Request body for explicitly saving a query via POST /queries/save."""

    user_id: str = Field(..., description="User saving the query")
    question: str = Field(..., description="Natural language question")
    sql: str = Field(..., description="The SQL to save")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    description: Optional[str] = Field(default=None, description="Optional description")


class UpdateSavedQueryRequest(BaseModel):
    """Request body for PATCH /queries/saved/{id} — all fields optional."""

    tags: Optional[List[str]] = Field(default=None, description="New tags list (replaces existing)")
    description: Optional[str] = Field(default=None, description="Updated description")
    sql: Optional[str] = Field(default=None, description="Updated SQL string")
