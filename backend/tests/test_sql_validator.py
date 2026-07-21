"""
test_sql_validator.py — Unit tests for app/security/sql_validator.py

Run with:
    pytest tests/test_sql_validator.py -v
"""

import pytest
from app.security.sql_validator import validate_sql, ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_valid(sql: str):
    result = validate_sql(sql)
    assert result.valid is True, f"Expected valid, got rejected.\nSQL: {sql!r}\nReason: {result.reason}"


def assert_invalid(sql: str, reason_fragment: str = ""):
    result = validate_sql(sql)
    assert result.valid is False, f"Expected invalid, but was accepted.\nSQL: {sql!r}"
    if reason_fragment:
        assert reason_fragment.lower() in result.reason.lower(), (
            f"Expected reason to contain {reason_fragment!r}, got: {result.reason!r}"
        )


# ---------------------------------------------------------------------------
# 1. Valid SELECT queries — should all pass
# ---------------------------------------------------------------------------

class TestValidSelects:
    def test_simple_select(self):
        assert_valid("SELECT * FROM sales")

    def test_select_with_where(self):
        assert_valid("SELECT id, amount FROM sales WHERE region = 'North'")

    def test_select_with_aggregation(self):
        assert_valid(
            "SELECT region, SUM(amount) AS total FROM sales GROUP BY region ORDER BY total DESC"
        )

    def test_select_with_join(self):
        assert_valid(
            "SELECT s.region, p.name FROM sales s JOIN products p ON s.product_id = p.product_id"
        )

    def test_select_with_subquery(self):
        assert_valid(
            "SELECT * FROM (SELECT region, COUNT(*) AS cnt FROM sales GROUP BY region) sub WHERE cnt > 10"
        )

    def test_select_with_cte(self):
        assert_valid(
            "WITH regional AS (SELECT region, SUM(amount) AS total FROM sales GROUP BY region) "
            "SELECT * FROM regional WHERE total > 1000"
        )

    def test_select_case_insensitive(self):
        assert_valid("select id from orders")

    def test_select_mixed_case(self):
        assert_valid("Select Id, Name From customers Where segment = 'enterprise'")

    def test_select_trailing_semicolon(self):
        # A trailing semicolon is harmless
        assert_valid("SELECT 1;")

    def test_select_with_limit(self):
        assert_valid("SELECT * FROM orders LIMIT 100")

    def test_select_with_date_function(self):
        assert_valid(
            "SELECT region, SUM(amount) FROM sales "
            "WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') "
            "GROUP BY region"
        )


# ---------------------------------------------------------------------------
# 2. Forbidden DML / DDL verbs — should all be rejected
# ---------------------------------------------------------------------------

class TestForbiddenVerbs:
    def test_delete(self):
        assert_invalid("DELETE FROM sales WHERE id = 1", "Forbidden SQL verb")

    def test_update(self):
        assert_invalid("UPDATE sales SET amount = 0", "Forbidden SQL verb")

    def test_insert(self):
        assert_invalid("INSERT INTO sales (region, amount) VALUES ('North', 100)", "Forbidden SQL verb")

    def test_drop_table(self):
        assert_invalid("DROP TABLE sales", "Forbidden SQL verb")

    def test_alter_table(self):
        assert_invalid("ALTER TABLE sales ADD COLUMN discount NUMERIC", "Forbidden SQL verb")

    def test_truncate(self):
        assert_invalid("TRUNCATE TABLE sales", "Forbidden SQL verb")

    def test_create_table(self):
        assert_invalid("CREATE TABLE test (id INT)", "Forbidden SQL verb")

    def test_exec(self):
        assert_invalid("EXEC sp_rename 'sales', 'transactions'", "Forbidden SQL verb")

    def test_grant(self):
        assert_invalid("GRANT SELECT ON sales TO user1", "Forbidden SQL verb")

    def test_revoke(self):
        assert_invalid("REVOKE SELECT ON sales FROM user1", "Forbidden SQL verb")

    def test_merge(self):
        assert_invalid("MERGE INTO sales USING staging ON sales.id = staging.id", "Forbidden SQL verb")

    def test_forbidden_verb_mixed_case(self):
        assert_invalid("dElEtE FROM sales", "Forbidden SQL verb")

    def test_forbidden_verb_after_valid_select(self):
        # A forbidden verb after SELECT inside a subquery must still be caught
        assert_invalid("SELECT * FROM (DROP TABLE sales) sub", "Forbidden SQL verb")


# ---------------------------------------------------------------------------
# 3. Multiple statements — should be rejected
# ---------------------------------------------------------------------------

class TestMultipleStatements:
    def test_two_statements_semicolon(self):
        assert_invalid(
            "SELECT * FROM sales; SELECT * FROM orders",
            "Multiple SQL statements",
        )

    def test_select_then_drop(self):
        assert_invalid(
            "SELECT 1; DROP TABLE users",
            "Multiple SQL statements",
        )

    def test_select_then_insert(self):
        assert_invalid(
            "SELECT * FROM sales; INSERT INTO sales VALUES (1, 'x', 50)",
            "Multiple SQL statements",
        )

    def test_trailing_semicolon_allowed(self):
        # Only one statement — trailing ; is fine
        assert_valid("SELECT * FROM sales;")


# ---------------------------------------------------------------------------
# 4. Empty / blank input — should be rejected
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_string(self):
        assert_invalid("", "empty")

    def test_whitespace_only(self):
        assert_invalid("   ", "empty")

    def test_none_equivalent_empty(self):
        assert_invalid("", "empty")


# ---------------------------------------------------------------------------
# 5. Non-SELECT openers — should be rejected
# ---------------------------------------------------------------------------

class TestNonSelectOpeners:
    def test_bare_table_name(self):
        assert_invalid("sales", "does not start with SELECT")

    def test_explain_only(self):
        assert_invalid("EXPLAIN SELECT * FROM sales", "does not start with SELECT")

    def test_show_tables(self):
        assert_invalid("SHOW TABLES", "does not start with SELECT")

    def test_describe(self):
        assert_invalid("DESCRIBE sales", "does not start with SELECT")


# ---------------------------------------------------------------------------
# 6. SQL-injection patterns — should be rejected
# ---------------------------------------------------------------------------

class TestInjectionPatterns:
    def test_union_select(self):
        assert_invalid(
            "SELECT id FROM sales UNION SELECT password FROM users",
            "injection",
        )

    def test_union_all_select(self):
        assert_invalid(
            "SELECT 1 UNION ALL SELECT table_name FROM information_schema.tables",
            "injection",
        )


# ---------------------------------------------------------------------------
# 7. ValidationResult properties
# ---------------------------------------------------------------------------

class TestValidationResult:
    def test_valid_result_is_truthy(self):
        result = validate_sql("SELECT 1")
        assert bool(result) is True

    def test_invalid_result_is_falsy(self):
        result = validate_sql("DROP TABLE sales")
        assert bool(result) is False

    def test_valid_reason_text(self):
        result = validate_sql("SELECT 1")
        assert result.reason == "SQL is valid."

    def test_result_is_immutable(self):
        result = validate_sql("SELECT 1")
        with pytest.raises((AttributeError, TypeError)):
            result.valid = False  # type: ignore
