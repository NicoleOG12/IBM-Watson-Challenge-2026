"""
sql_validator.py — SQL security validation layer.

Ensures that every SQL string produced by the LLM is safe before it reaches
the data source.  The validator is intentionally strict-by-default:
anything that cannot be positively identified as a read-only SELECT is
rejected.

Public API
----------
    result = validate_sql(sql_string)
    result.valid    # bool
    result.reason   # str — human-readable explanation
"""

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Immutable result returned by validate_sql()."""

    valid: bool
    reason: str

    def __bool__(self) -> bool:
        return self.valid


# ---------------------------------------------------------------------------
# Internal patterns
# ---------------------------------------------------------------------------

# Verbs that are never allowed, regardless of context
_FORBIDDEN_VERBS = re.compile(
    r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|"
    r"GRANT|REVOKE|MERGE|REPLACE|CALL|LOAD|COPY|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

# A SQL string must begin with SELECT (after optional whitespace/comments)
# Allow optional leading CTEs: WITH ... SELECT
_LEADING_SELECT = re.compile(
    r"^\s*(?:WITH\b.+?\bSELECT\b|SELECT\b)",
    re.IGNORECASE | re.DOTALL,
)

# Multiple statements: look for a semicolon that is NOT at the very end
# (trailing semicolon is harmless; a mid-string one hides a second statement)
_MULTIPLE_STATEMENTS = re.compile(
    r";(?!\s*$)",
    re.IGNORECASE,
)

# Inline comment styles that could be used to smuggle content
_INLINE_COMMENT = re.compile(r"--.*?$", re.MULTILINE)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

# Common SQL-injection patterns (comment-based termination tricks)
_INJECTION_PATTERNS = re.compile(
    r"(;\s*--|;\s*/\*|'\s*OR\b|'\s*AND\b|UNION\s+ALL\s+SELECT|UNION\s+SELECT)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_comments(sql: str) -> str:
    """Remove inline and block comments to expose the raw SQL tokens."""
    sql = _BLOCK_COMMENT.sub(" ", sql)
    sql = _INLINE_COMMENT.sub(" ", sql)
    return sql.strip()


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------

def validate_sql(sql: str) -> ValidationResult:
    """
    Validate that a SQL string is safe to execute.

    Checks (in order):
        1. Non-empty input
        2. No multiple statements (semicolon mid-string)
        3. No SQL-injection patterns
        4. No forbidden DML / DDL verbs
        5. Statement must start with SELECT (CTEs allowed: WITH … SELECT)

    Args:
        sql: The SQL string to validate.

    Returns:
        ValidationResult(valid=True, reason="SQL is valid.")
        — or —
        ValidationResult(valid=False, reason="<specific reason>")

    Examples:
        >>> validate_sql("SELECT * FROM sales")
        ValidationResult(valid=True, reason='SQL is valid.')

        >>> validate_sql("DROP TABLE sales")
        ValidationResult(valid=False, reason="Forbidden SQL verb detected: 'DROP'. ...")

        >>> validate_sql("SELECT 1; DROP TABLE users")
        ValidationResult(valid=False, reason='Multiple SQL statements detected...')
    """
    # --- 1. Non-empty -------------------------------------------------------
    if not sql or not sql.strip():
        return ValidationResult(
            valid=False,
            reason="SQL string is empty. A SELECT statement is required.",
        )

    # Work on a comment-stripped copy for pattern checks, but keep original
    # for the final leading-SELECT check (CTEs may use WITH before SELECT).
    stripped = _strip_comments(sql)

    # --- 2. Multiple statements ---------------------------------------------
    if _MULTIPLE_STATEMENTS.search(stripped):
        return ValidationResult(
            valid=False,
            reason=(
                "Multiple SQL statements detected (semicolon mid-string). "
                "Only a single SELECT statement is permitted."
            ),
        )

    # --- 3. Injection patterns ----------------------------------------------
    if _INJECTION_PATTERNS.search(stripped):
        return ValidationResult(
            valid=False,
            reason=(
                "Potential SQL injection pattern detected. "
                "The query was rejected for security reasons."
            ),
        )

    # --- 4. Forbidden verbs -------------------------------------------------
    match = _FORBIDDEN_VERBS.search(stripped)
    if match:
        verb = match.group(0).upper()
        return ValidationResult(
            valid=False,
            reason=(
                f"Forbidden SQL verb detected: '{verb}'. "
                "Only analytical SELECT queries are permitted. "
                "No data modification or DDL operations are allowed."
            ),
        )

    # --- 5. Must start with SELECT (or WITH … SELECT) ----------------------
    if not _LEADING_SELECT.match(stripped):
        return ValidationResult(
            valid=False,
            reason=(
                "SQL does not start with SELECT (or WITH … SELECT). "
                "Only read-only SELECT queries are permitted."
            ),
        )

    return ValidationResult(valid=True, reason="SQL is valid.")
