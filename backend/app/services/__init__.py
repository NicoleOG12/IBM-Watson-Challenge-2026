"""
services/__init__.py — Public re-exports for all service layer functions.
"""

from app.services.audit_service import clear_logs, get_logs, record_query
from app.services.execution_service import execute_query, set_connector
from app.services.execution import (
    AthenaExecutor,
    ExecutionResult,
    MockExecutor,
    QueryExecutor,
    get_executor,
)
from app.services.insights_service import analyze_results
from app.services.memory_service import (
    all_user_ids,
    clear_memory,
    get_context,
    get_user_memory,
    save_interaction,
)
from app.services.query_service import QueryService
from app.services.response_formatter import format_error_response, format_response
from app.services.schema_service import build_context_prompt, load_schema
from app.services.watsonx_service import build_prompt, generate_sql

__all__ = [
    # audit
    "clear_logs",
    "get_logs",
    "record_query",
    # execution
    "execute_query",
    "set_connector",
    "AthenaExecutor",
    "ExecutionResult",
    "MockExecutor",
    "QueryExecutor",
    "get_executor",
    # insights
    "analyze_results",
    # memory
    "all_user_ids",
    "clear_memory",
    "get_context",
    "get_user_memory",
    "save_interaction",
    # orchestration
    "QueryService",
    # response
    "format_error_response",
    "format_response",
    # schema
    "build_context_prompt",
    "load_schema",
    # watsonx
    "build_prompt",
    "generate_sql",
]
