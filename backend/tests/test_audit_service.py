"""
test_audit_service.py — Unit tests for app/services/audit_service.py

Run with:
    pytest tests/test_audit_service.py -v
"""

import json
import pytest
from pathlib import Path

from app.services import audit_service
from app.services.audit_service import record_query, get_logs, clear_logs
from app.models.audit import AuditLog


# ---------------------------------------------------------------------------
# Fixture: wipe in-memory store and disable file writes before each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_audit(tmp_path, monkeypatch):
    """
    Clear the in-memory log and redirect file output to a tmp dir
    so tests never write to the real logs/ folder.
    """
    clear_logs()
    monkeypatch.setattr(audit_service.settings, "AUDIT_ENABLED", True)
    monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(tmp_path / "audit.log"))
    yield
    clear_logs()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record(**kwargs) -> AuditLog:
    defaults = dict(
        user_id="u1",
        natural_language_query="Show total sales",
        generated_sql="SELECT SUM(amount) FROM sales",
        status="success",
        execution_time_ms=120.5,
        row_count=4,
    )
    defaults.update(kwargs)
    return record_query(**defaults)


# ---------------------------------------------------------------------------
# 1. record_query — return value and storage
# ---------------------------------------------------------------------------

class TestRecordQuery:
    def test_returns_audit_log(self):
        entry = _record()
        assert isinstance(entry, AuditLog)

    def test_log_id_is_uuid_string(self):
        entry = _record()
        assert len(entry.log_id) == 36
        assert entry.log_id.count("-") == 4

    def test_timestamp_is_iso_string(self):
        entry = _record()
        from datetime import datetime
        dt = datetime.fromisoformat(entry.timestamp)
        assert dt.tzinfo is not None  # timezone-aware

    def test_user_id_stored(self):
        entry = _record(user_id="alice")
        assert entry.user_id == "alice"

    def test_query_stored(self):
        entry = _record(natural_language_query="My query")
        assert entry.natural_language_query == "My query"

    def test_sql_stored(self):
        entry = _record(generated_sql="SELECT 1")
        assert entry.generated_sql == "SELECT 1"

    def test_status_success(self):
        entry = _record(status="success")
        assert entry.status == "success"

    def test_status_rejected(self):
        entry = _record(status="rejected", error="Forbidden verb")
        assert entry.status == "rejected"
        assert entry.error == "Forbidden verb"

    def test_execution_time_rounded(self):
        entry = _record(execution_time_ms=142.7654321)
        assert entry.execution_time_ms == 142.77

    def test_row_count_stored(self):
        entry = _record(row_count=12)
        assert entry.row_count == 12

    def test_environment_from_settings(self):
        entry = _record()
        assert entry.environment == audit_service.settings.ENVIRONMENT

    def test_error_none_by_default(self):
        entry = _record()
        assert entry.error is None

    def test_entry_added_to_store(self):
        _record()
        assert len(audit_service._AUDIT_LOG) == 1

    def test_multiple_entries_accumulate(self):
        _record()
        _record()
        _record()
        assert len(audit_service._AUDIT_LOG) == 3


# ---------------------------------------------------------------------------
# 2. get_logs
# ---------------------------------------------------------------------------

class TestGetLogs:
    def test_empty_store_returns_empty_list(self):
        assert get_logs() == []

    def test_returns_all_entries(self):
        _record()
        _record()
        assert len(get_logs()) == 2

    def test_returns_newest_first(self):
        _record(natural_language_query="first")
        _record(natural_language_query="second")
        logs = get_logs()
        assert logs[0].natural_language_query == "second"
        assert logs[1].natural_language_query == "first"

    def test_filter_by_user_id(self):
        _record(user_id="alice")
        _record(user_id="bob")
        _record(user_id="alice")
        alice_logs = get_logs(user_id="alice")
        assert len(alice_logs) == 2
        assert all(l.user_id == "alice" for l in alice_logs)

    def test_filter_unknown_user_returns_empty(self):
        _record(user_id="alice")
        assert get_logs(user_id="unknown") == []

    def test_limit_respected(self):
        for _ in range(10):
            _record()
        assert len(get_logs(limit=3)) == 3

    def test_limit_default_is_100(self):
        for _ in range(5):
            _record()
        assert len(get_logs()) == 5

    def test_all_entries_are_audit_log_instances(self):
        _record()
        for entry in get_logs():
            assert isinstance(entry, AuditLog)


# ---------------------------------------------------------------------------
# 3. clear_logs
# ---------------------------------------------------------------------------

class TestClearLogs:
    def test_clears_in_memory_store(self):
        _record()
        _record()
        clear_logs()
        assert audit_service._AUDIT_LOG == []

    def test_get_logs_empty_after_clear(self):
        _record()
        clear_logs()
        assert get_logs() == []

    def test_clear_when_empty_is_safe(self):
        clear_logs()  # must not raise


# ---------------------------------------------------------------------------
# 4. File sink
# ---------------------------------------------------------------------------

class TestFileSink:
    def test_file_created_on_record(self, tmp_path, monkeypatch):
        log_file = tmp_path / "audit.log"
        monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(log_file))
        _record()
        assert log_file.exists()

    def test_file_contains_valid_json_lines(self, tmp_path, monkeypatch):
        log_file = tmp_path / "audit.log"
        monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(log_file))
        _record()
        _record()
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "log_id" in obj
            assert "timestamp" in obj
            assert "user_id" in obj

    def test_file_appends_not_overwrites(self, tmp_path, monkeypatch):
        log_file = tmp_path / "audit.log"
        monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(log_file))
        _record()
        _record()
        _record()
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

    def test_no_file_written_when_disabled(self, tmp_path, monkeypatch):
        log_file = tmp_path / "audit.log"
        monkeypatch.setattr(audit_service.settings, "AUDIT_ENABLED", False)
        monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(log_file))
        _record()
        assert not log_file.exists()

    def test_nested_directory_created(self, tmp_path, monkeypatch):
        log_file = tmp_path / "nested" / "deep" / "audit.log"
        monkeypatch.setattr(audit_service.settings, "AUDIT_LOG_FILE", str(log_file))
        _record()
        assert log_file.exists()


# ---------------------------------------------------------------------------
# 5. AuditLog model
# ---------------------------------------------------------------------------

class TestAuditLogModel:
    def test_to_dynamo_returns_dict(self):
        entry = AuditLog(
            user_id="u1",
            natural_language_query="q",
            generated_sql="SELECT 1",
            status="success",
        )
        d = entry.to_dynamo()
        assert isinstance(d, dict)

    def test_to_dynamo_strips_none_values(self):
        entry = AuditLog(
            user_id="u1",
            natural_language_query="q",
            generated_sql="SELECT 1",
            status="success",
            error=None,
        )
        d = entry.to_dynamo()
        assert "error" not in d

    def test_to_dynamo_preserves_error_when_set(self):
        entry = AuditLog(
            user_id="u1",
            natural_language_query="q",
            generated_sql="",
            status="rejected",
            error="Forbidden verb",
        )
        d = entry.to_dynamo()
        assert d["error"] == "Forbidden verb"

    def test_model_dump_json_is_valid(self):
        entry = AuditLog(
            user_id="u1",
            natural_language_query="q",
            generated_sql="SELECT 1",
            status="success",
        )
        parsed = json.loads(entry.model_dump_json())
        assert parsed["user_id"] == "u1"
