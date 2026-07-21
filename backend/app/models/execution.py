from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional


class ExecutionMetadata(BaseModel):
    """
    Metadata produced by the execution layer for every query.
    Athena-specific fields (data_scanned_bytes, estimated_cost_usd) are
    populated only when USE_ATHENA=True; zero for mock mode.
    """

    execution_time_ms: float = Field(0.0, description="Wall-clock time in milliseconds")
    rows_returned: int = Field(0, description="Number of rows returned")
    data_scanned_bytes: int = Field(0, description="Bytes scanned (Athena only)")
    estimated_cost_usd: float = Field(0.0, description="Estimated cost in USD (Athena only)")
    execution_mode: str = Field("mock", description="'mock' or 'athena'")


class QueryResult(BaseModel):
    """Structured result returned by the execution service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "columns": ["region", "total_sales"],
                "rows": [
                    {"region": "North", "total_sales": "18450.75"},
                    {"region": "East",  "total_sales": "15230.00"},
                ],
                "row_count": 2,
                "execution_mode": "mock",
                "metadata": {
                    "execution_time_ms": 12.4,
                    "rows_returned": 2,
                    "data_scanned_bytes": 0,
                    "estimated_cost_usd": 0.0,
                    "execution_mode": "mock",
                },
                "error": None,
            }
        }
    )

    rows: List[dict] = Field(default_factory=list)
    row_count: int = Field(0)
    columns: List[str] = Field(default_factory=list)
    execution_mode: str = Field(..., description="'mock' or 'athena'")
    metadata: Optional[ExecutionMetadata] = Field(
        None, description="Execution statistics; populated on success"
    )
    error: Optional[str] = Field(None)
