from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional


class ExecutionMetadataPayload(BaseModel):
    """Execution metadata surfaced in the API response for the frontend."""
    execution_time_ms: float = 0.0
    bytes_processed:   int   = 0
    engine:            str   = "mock-sqlite"
    row_count:         int   = 0


class DataPayload(BaseModel):
    """The raw query execution result embedded in the formatted response."""

    columns:        List[str]                          = Field(default_factory=list)
    rows:           List[Dict[str, Any]]               = Field(default_factory=list)
    row_count:      int                                = 0
    execution_mode: str                                = "mock"
    metadata:       Optional[ExecutionMetadataPayload] = None


class FormattedResponse(BaseModel):
    """
    The canonical API response shape consumed by the frontend.

    All four top-level keys are always present so the client can rely on
    a stable contract, regardless of whether the query returned rows.

    Shape:
        {
            "sql":         "SELECT ...",
            "explanation": "Plain-English description of what the SQL does.",
            "data":        { "columns": [...], "rows": [...], "row_count": N, "execution_mode": "mock" },
            "insights":    { "summary": "...", "key_insights": [...], "trends": [...], "anomalies": [...] }
        }
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sql": (
                    "SELECT region, SUM(amount) AS total_sales "
                    "FROM sales GROUP BY region ORDER BY total_sales DESC"
                ),
                "explanation": (
                    "Aggregates total sales by region, ordered from highest to lowest."
                ),
                "data": {
                    "columns": ["region", "total_sales"],
                    "rows": [
                        {"region": "North", "total_sales": "18450.75"},
                        {"region": "East",  "total_sales": "15230.00"},
                    ],
                    "row_count": 2,
                    "execution_mode": "mock",
                },
                "insights": {
                    "row_count": 2,
                    "columns_analyzed": ["region", "total_sales"],
                    "key_insights": [
                        {
                            "category": "key_insight",
                            "message": "Highest total sales is 18,450.75 (row: North).",
                            "value": "18,450.75",
                            "column": "total_sales",
                        }
                    ],
                    "trends": [],
                    "anomalies": [],
                    "summary": "2 record(s) analysed. No anomalies detected.",
                },
            }
        }
    )

    sql: str = Field(..., description="The generated SELECT SQL statement")
    explanation: str = Field(..., description="Plain-English description of what the SQL does")
    data: DataPayload = Field(..., description="Raw query results")
    insights: Dict[str, Any] = Field(..., description="Auto-generated analytical insights")
