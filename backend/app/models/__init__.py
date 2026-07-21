"""
models/__init__.py — Public re-exports for all domain model classes.

Import from here rather than from individual modules to keep call-sites
stable when internal file structure changes.
"""

from app.models.audit import AuditLog
from app.models.execution import ExecutionMetadata, QueryResult
from app.models.insight import Insight, InsightReport
from app.models.llm import LLMRequest, LLMResult
from app.models.memory import Interaction, UserMemory
from app.models.query import HealthResponse, QueryRequest, QueryResponse
from app.models.response import DataPayload, FormattedResponse
from app.models.schema import ColumnMeta, SchemaContext, TableMeta

__all__ = [
    # audit
    "AuditLog",
    # execution
    "ExecutionMetadata",
    "QueryResult",
    # insight
    "Insight",
    "InsightReport",
    # llm
    "LLMRequest",
    "LLMResult",
    # memory
    "Interaction",
    "UserMemory",
    # query
    "HealthResponse",
    "QueryRequest",
    "QueryResponse",
    # response
    "DataPayload",
    "FormattedResponse",
    # schema
    "ColumnMeta",
    "SchemaContext",
    "TableMeta",
]
