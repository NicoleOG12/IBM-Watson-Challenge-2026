from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class Insight(BaseModel):
    """A single business insight extracted from a result set."""

    category: str = Field(
        ..., description="One of: 'key_insight', 'trend', 'anomaly'"
    )
    message: str = Field(..., description="Plain-English, business-friendly description")
    value: Optional[str] = Field(None, description="Supporting numeric or string value")
    column: Optional[str] = Field(None, description="Column the insight relates to")


class InsightReport(BaseModel):
    """Complete analysis report for a query result set."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "row_count": 4,
                "columns_analyzed": ["region", "total_sales"],
                "key_insights": [
                    {
                        "category": "key_insight",
                        "message": "North is the top-performing region with $18,450.75 in sales.",
                        "value": "18450.75",
                        "column": "total_sales",
                    }
                ],
                "trends": [
                    {
                        "category": "trend",
                        "message": "Total sales values range from $8,200 to $18,450 — a 2.2× spread across regions.",
                        "value": None,
                        "column": "total_sales",
                    }
                ],
                "anomalies": [],
                "summary": "4 regions analysed. North leads in total sales. No anomalies detected.",
            }
        }
    )

    row_count: int
    columns_analyzed: List[str]
    key_insights: List[Insight] = Field(default_factory=list)
    trends: List[Insight] = Field(default_factory=list)
    anomalies: List[Insight] = Field(default_factory=list)
    summary: str
