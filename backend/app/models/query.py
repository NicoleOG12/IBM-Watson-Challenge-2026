from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.models.anomaly import AnomalyRules
from app.models.cost import CostEstimate
from app.models.saved_query import SavedQuery


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "natural_language_query": "Show me total sales by region for last quarter",
                "anomaly_rules": {
                    "variation_threshold": 25.0,
                    "iqr_multiplier": 1.5,
                },
            }
        }
    )

    user_id: str = Field(..., description="Unique identifier of the requesting user")
    natural_language_query: str = Field(
        ..., min_length=1, description="The natural language query from the user"
    )
    anomaly_rules: Optional[AnomalyRules] = Field(
        default=None,
        description=(
            "Optional per-request overrides for anomaly detection thresholds. "
            "Falls back to ANOMALY_VARIATION_THRESHOLD and ANOMALY_IQR_MULTIPLIER from config when None."
        ),
    )


class QueryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_id": "user-123",
                "natural_language_query": "Show me total sales by region for last quarter",
                "result": {
                    "sql": "SELECT region, SUM(amount) AS total_sales FROM sales GROUP BY region",
                    "explanation": "Aggregates total sales by region.",
                    "data": {
                        "columns": ["region", "total_sales"],
                        "rows": [{"region": "North", "total_sales": "18450.75"}],
                        "row_count": 1,
                        "execution_mode": "mock",
                    },
                    "insights": {
                        "summary": "1 record(s) analysed. No anomalies detected.",
                        "key_insights": [],
                        "trends": [],
                        "anomalies": [],
                    },
                },
                "cost_estimate": {
                    "bytes_scanned": 150000000,
                    "estimated_cost_usd": 0.00075,
                    "table_count": 1,
                    "has_filter": True,
                    "is_mock": True,
                },
                "status": "success",
                "timestamp": "2024-01-01T12:00:00",
            }
        }
    )

    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    natural_language_query: str
    result: Optional[dict] = None
    cost_estimate: Optional[CostEstimate] = Field(
        default=None,
        description="Formula-based cost estimate for the generated SQL (informational only)",
    )
    next_steps: List[str] = Field(
        default_factory=list,
        description="LLM-generated follow-up question suggestions",
    )
    matched_query: Optional[SavedQuery] = Field(
        default=None,
        description="Existing saved query that matched the user's question (above similarity threshold)",
    )
    status: str = "pending"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
