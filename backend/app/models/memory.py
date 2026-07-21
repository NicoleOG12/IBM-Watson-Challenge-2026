from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, timezone


class Interaction(BaseModel):
    """A single recorded query/SQL pair for one user turn."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Show me total sales by region for last quarter",
                "sql": "SELECT region, SUM(amount) AS total_sales FROM sales WHERE ...",
                "timestamp": "2024-01-01T12:00:00",
                "tables_used": ["sales"],
                "filters_applied": ["sale_date >= DATE_TRUNC(...)"],
                "status": "success",
                "row_count": 4,
            }
        }
    )

    query: str = Field(..., description="The original natural language query")
    sql: str = Field(..., description="The SQL generated for this query")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this interaction was recorded",
    )
    tables_used: List[str] = Field(
        default_factory=list,
        description="Tables referenced in the generated SQL (extracted from FROM/JOIN clauses)",
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="Filter predicates extracted from the WHERE clause",
    )
    status: str = Field(
        default="success",
        description="Execution status: 'success' or 'rejected'",
    )
    row_count: int = Field(
        default=0,
        description="Number of rows returned by the execution",
    )


class UserMemory(BaseModel):
    """The full conversation history for a single user."""

    user_id: str = Field(..., description="The user this memory belongs to")
    interactions: List[Interaction] = Field(
        default_factory=list,
        description="Ordered list of past interactions, newest last",
    )

    @property
    def last_sql(self) -> Optional[str]:
        """Return the most recent SQL query, or None if history is empty."""
        return self.interactions[-1].sql if self.interactions else None

    @property
    def last_query(self) -> Optional[str]:
        """Return the most recent natural language query."""
        return self.interactions[-1].query if self.interactions else None
