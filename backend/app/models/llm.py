from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class LLMResult(BaseModel):
    """Structured output returned by the LLM service for every NL→SQL request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sql": (
                    "SELECT region, SUM(amount) AS total_sales "
                    "FROM sales "
                    "WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') "
                    "GROUP BY region "
                    "ORDER BY total_sales DESC"
                ),
                "explanation": (
                    "Aggregates the total sales amount grouped by region for the "
                    "previous quarter, ordered from highest to lowest."
                ),
            }
        }
    )

    sql: str = Field(..., description="The generated SELECT SQL statement")
    explanation: str = Field(
        ..., description="Plain-English explanation of what the SQL does"
    )


class LLMRequest(BaseModel):
    """Internal object passed to the LLM service."""

    natural_language_query: str
    user_id: Optional[str] = None
    context: Optional[dict] = None
