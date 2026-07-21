"""
conftest.py — Shared pytest fixtures for the entire test suite.

Applied automatically to every test session via autouse=True.

Responsibilities:
  - Redirect audit file writes to a temp directory (never touches logs/)
  - Clear the audit in-memory store before every test
  - Clear the memory in-memory store before every test
  - Disable the schema LRU cache between tests so schema.json changes
    are always picked up in isolation
"""

import pytest

import app.services.audit_service as _audit_svc
import app.services.memory_service as _mem_svc
import app.services.schema_service as _schema_svc


@pytest.fixture(autouse=True)
def _clean_stores(tmp_path, monkeypatch):
    """
    Before each test:
      1. Clear the audit in-memory log.
      2. Clear the memory in-memory store.
      3. Redirect audit file output to a pytest-managed tmp directory.
      4. Clear the schema LRU cache so tests that call load_schema()
         don't share cached state.

    After each test: restores everything automatically (monkeypatch teardown).
    """
    # Audit
    _audit_svc.clear_logs()
    monkeypatch.setattr(
        _audit_svc.settings, "AUDIT_LOG_FILE", str(tmp_path / "audit.log")
    )

    # Memory
    _mem_svc._STORE.clear()

    # Schema cache
    _schema_svc.load_schema.cache_clear()

    yield

    # Teardown
    _audit_svc.clear_logs()
    _mem_svc._STORE.clear()
    _schema_svc.load_schema.cache_clear()
