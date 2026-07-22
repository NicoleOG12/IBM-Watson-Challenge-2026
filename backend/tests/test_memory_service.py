"""
test_memory_service.py — Unit tests for app/services/memory_service.py

Run with:
    pytest tests/test_memory_service.py -v
"""

import pytest
from datetime import datetime, timezone

from app.services import memory_service
from app.services.memory_service import (
    get_context,
    save_interaction,
    get_user_memory,
    clear_memory,
    all_user_ids,
)
from app.models.memory import Interaction, UserMemory


# ---------------------------------------------------------------------------
# Fixture: auto-clear the in-memory store before every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_store():
    """Wipe the global store before each test to prevent leakage."""
    memory_service._STORE.clear()
    yield
    memory_service._STORE.clear()


# ---------------------------------------------------------------------------
# 1. save_interaction
# ---------------------------------------------------------------------------

class TestSaveInteraction:
    def test_first_save_creates_entry(self):
        save_interaction("u1", "Show total sales", "SELECT SUM(amount) FROM sales")
        assert "u1" in memory_service._STORE

    def test_saved_query_is_stored(self):
        save_interaction("u1", "Show total sales", "SELECT SUM(amount) FROM sales")
        mem = memory_service._STORE["u1"]
        assert mem.interactions[0].query == "Show total sales"

    def test_saved_sql_is_stored(self):
        save_interaction("u1", "Show total sales", "SELECT SUM(amount) FROM sales")
        mem = memory_service._STORE["u1"]
        assert mem.interactions[0].sql == "SELECT SUM(amount) FROM sales"

    def test_timestamp_is_datetime(self):
        save_interaction("u1", "q", "SELECT 1")
        mem = memory_service._STORE["u1"]
        assert isinstance(mem.interactions[0].timestamp, datetime)

    def test_multiple_saves_append(self):
        save_interaction("u1", "q1", "SELECT 1")
        save_interaction("u1", "q2", "SELECT 2")
        save_interaction("u1", "q3", "SELECT 3")
        mem = memory_service._STORE["u1"]
        assert len(mem.interactions) == 3

    def test_order_is_chronological(self):
        save_interaction("u1", "q1", "SELECT 1")
        save_interaction("u1", "q2", "SELECT 2")
        mem = memory_service._STORE["u1"]
        assert mem.interactions[0].query == "q1"
        assert mem.interactions[1].query == "q2"

    def test_separate_users_are_isolated(self):
        save_interaction("u1", "q for u1", "SELECT 1")
        save_interaction("u2", "q for u2", "SELECT 2")
        assert len(memory_service._STORE["u1"].interactions) == 1
        assert len(memory_service._STORE["u2"].interactions) == 1
        assert memory_service._STORE["u1"].interactions[0].query == "q for u1"

    def test_rolling_window_trims_oldest(self, monkeypatch):
        monkeypatch.setattr(memory_service.settings, "MEMORY_MAX_HISTORY", 3)
        for i in range(5):
            save_interaction("u1", f"q{i}", f"SELECT {i}")
        mem = memory_service._STORE["u1"]
        assert len(mem.interactions) == 3
        # Oldest (q0, q1) should be gone; q2, q3, q4 remain
        assert mem.interactions[0].query == "q2"
        assert mem.interactions[-1].query == "q4"


# ---------------------------------------------------------------------------
# 2. get_context
# ---------------------------------------------------------------------------

class TestGetContext:
    def test_new_user_returns_empty_context(self):
        ctx = get_context("unknown-user")
        assert ctx["user_id"] == "unknown-user"
        assert ctx["history"] == []
        assert ctx["last_query"] is None
        assert ctx["last_sql"] is None

    def test_context_has_required_keys(self):
        ctx = get_context("u1")
        for key in ("user_id", "history", "last_query", "last_sql"):
            assert key in ctx

    def test_history_reflects_saved_interactions(self):
        save_interaction("u1", "Show sales", "SELECT * FROM sales")
        ctx = get_context("u1")
        assert len(ctx["history"]) == 1
        assert ctx["history"][0]["query"] == "Show sales"
        assert ctx["history"][0]["sql"] == "SELECT * FROM sales"

    def test_last_query_is_most_recent(self):
        save_interaction("u1", "first", "SELECT 1")
        save_interaction("u1", "second", "SELECT 2")
        ctx = get_context("u1")
        assert ctx["last_query"] == "second"

    def test_last_sql_is_most_recent(self):
        save_interaction("u1", "first", "SELECT 1")
        save_interaction("u1", "second", "SELECT 2")
        ctx = get_context("u1")
        assert ctx["last_sql"] == "SELECT 2"

    def test_history_capped_by_max_history(self, monkeypatch):
        monkeypatch.setattr(memory_service.settings, "MEMORY_MAX_HISTORY", 3)
        for i in range(6):
            save_interaction("u1", f"q{i}", f"SELECT {i}")
        ctx = get_context("u1")
        assert len(ctx["history"]) == 3

    def test_history_entries_have_timestamp(self):
        save_interaction("u1", "q", "SELECT 1")
        ctx = get_context("u1")
        assert "timestamp" in ctx["history"][0]

    def test_different_users_get_different_contexts(self):
        save_interaction("u1", "u1 query", "SELECT 1")
        save_interaction("u2", "u2 query", "SELECT 2")
        ctx1 = get_context("u1")
        ctx2 = get_context("u2")
        assert ctx1["last_query"] == "u1 query"
        assert ctx2["last_query"] == "u2 query"


# ---------------------------------------------------------------------------
# 3. get_user_memory
# ---------------------------------------------------------------------------

class TestGetUserMemory:
    def test_returns_none_for_unknown_user(self):
        assert get_user_memory("nobody") is None

    def test_returns_user_memory_object(self):
        save_interaction("u1", "q", "SELECT 1")
        mem = get_user_memory("u1")
        assert isinstance(mem, UserMemory)

    def test_user_id_correct(self):
        save_interaction("u1", "q", "SELECT 1")
        mem = get_user_memory("u1")
        assert mem.user_id == "u1"

    def test_interactions_populated(self):
        save_interaction("u1", "q", "SELECT 1")
        save_interaction("u1", "q2", "SELECT 2")
        mem = get_user_memory("u1")
        assert len(mem.interactions) == 2


# ---------------------------------------------------------------------------
# 4. clear_memory
# ---------------------------------------------------------------------------

class TestClearMemory:
    def test_clear_removes_user(self):
        save_interaction("u1", "q", "SELECT 1")
        clear_memory("u1")
        assert "u1" not in memory_service._STORE

    def test_clear_unknown_user_is_safe(self):
        clear_memory("nobody")  # must not raise

    def test_clear_only_affects_target_user(self):
        save_interaction("u1", "q", "SELECT 1")
        save_interaction("u2", "q", "SELECT 2")
        clear_memory("u1")
        assert "u1" not in memory_service._STORE
        assert "u2" in memory_service._STORE

    def test_context_empty_after_clear(self):
        save_interaction("u1", "q", "SELECT 1")
        clear_memory("u1")
        ctx = get_context("u1")
        assert ctx["history"] == []
        assert ctx["last_query"] is None


# ---------------------------------------------------------------------------
# 5. all_user_ids
# ---------------------------------------------------------------------------

class TestAllUserIds:
    def test_empty_store_returns_empty_list(self):
        assert all_user_ids() == []

    def test_returns_all_users(self):
        save_interaction("u1", "q", "s")
        save_interaction("u2", "q", "s")
        save_interaction("u3", "q", "s")
        ids = all_user_ids()
        assert set(ids) == {"u1", "u2", "u3"}

    def test_cleared_user_not_in_list(self):
        save_interaction("u1", "q", "s")
        save_interaction("u2", "q", "s")
        clear_memory("u1")
        assert "u1" not in all_user_ids()


# ---------------------------------------------------------------------------
# 6. Interaction model
# ---------------------------------------------------------------------------

class TestInteractionModel:
    def test_timestamp_defaults_to_now(self):
        before = datetime.now(timezone.utc)
        i = Interaction(query="q", sql="SELECT 1")
        after = datetime.now(timezone.utc)
        assert before <= i.timestamp <= after

    def test_fields_stored_correctly(self):
        i = Interaction(query="What is total sales?", sql="SELECT SUM(amount) FROM sales")
        assert i.query == "What is total sales?"
        assert i.sql == "SELECT SUM(amount) FROM sales"


# ---------------------------------------------------------------------------
# 7. UserMemory model
# ---------------------------------------------------------------------------

class TestUserMemoryModel:
    def test_last_sql_none_when_empty(self):
        m = UserMemory(user_id="u1")
        assert m.last_sql is None

    def test_last_query_none_when_empty(self):
        m = UserMemory(user_id="u1")
        assert m.last_query is None

    def test_last_sql_returns_most_recent(self):
        m = UserMemory(user_id="u1")
        m.interactions.append(Interaction(query="q1", sql="SELECT 1"))
        m.interactions.append(Interaction(query="q2", sql="SELECT 2"))
        assert m.last_sql == "SELECT 2"

    def test_last_query_returns_most_recent(self):
        m = UserMemory(user_id="u1")
        m.interactions.append(Interaction(query="q1", sql="SELECT 1"))
        m.interactions.append(Interaction(query="q2", sql="SELECT 2"))
        assert m.last_query == "q2"
