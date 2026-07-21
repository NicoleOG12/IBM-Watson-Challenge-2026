"""
app/services/execution/__init__.py

Public surface of the execution sub-package.

Usage:
    from app.services.execution import get_executor, ExecutionResult
    from app.services.execution import MockExecutor, AthenaExecutor
"""

from app.services.execution.base import ExecutionResult, QueryExecutor
from app.services.execution.mock_executor import MockExecutor
from app.services.execution.athena_executor import AthenaExecutor
from app.services.execution.factory import get_executor

__all__ = [
    "ExecutionResult",
    "QueryExecutor",
    "MockExecutor",
    "AthenaExecutor",
    "get_executor",
]
