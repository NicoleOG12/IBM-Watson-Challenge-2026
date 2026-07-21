"""
schema_service.py — Schema metadata management for schema-aware SQL generation.

Responsibilities:
    1. Load table/column metadata from data/schema.json (or a custom path)
    2. Cache the parsed SchemaContext so it is only read from disk once
    3. Expose build_context_prompt(schema, user_query) which injects the
       schema into the LLM system prompt, dramatically improving SQL accuracy

Usage:
    from app.services.schema_service import load_schema, build_context_prompt

    schema = load_schema()                          # loads & caches schema.json
    prompt = build_context_prompt(schema, query)    # returns the full prompt string
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.models.schema import SchemaContext, TableMeta

logger = logging.getLogger(__name__)

# Default path — relative to the project root (where uvicorn is launched from)
_DEFAULT_SCHEMA_PATH = Path("data/schema.json")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_schema(path: Optional[str] = None) -> SchemaContext:
    """
    Load and validate schema metadata from a JSON file.

    The result is cached after the first load; call load_schema.cache_clear()
    if you need to reload (e.g. hot-reload during development).

    Args:
        path: Optional file path override. Defaults to data/schema.json.

    Returns:
        A validated SchemaContext instance.

    Raises:
        FileNotFoundError: if the schema file does not exist.
        ValueError: if the file content does not match the expected schema.
    """
    schema_path = Path(path) if path else _DEFAULT_SCHEMA_PATH

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found at '{schema_path}'. "
            "Create data/schema.json or set the SCHEMA_PATH env variable."
        )

    logger.info("Loading schema metadata", extra={"path": str(schema_path)})
    raw = json.loads(schema_path.read_text(encoding="utf-8"))
    schema = SchemaContext(**raw)
    logger.info(
        "Schema loaded",
        extra={"tables": [t.table_name for t in schema.tables]},
    )
    return schema


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _render_table(table: TableMeta) -> str:
    """
    Render a single TableMeta into a compact, human-readable block
    that the LLM can parse without ambiguity.

    Example output:
        Table: sales
        Description: Records of individual product sales transactions.
        Columns:
          - sale_id (UUID): Unique identifier for each sale
          - region (VARCHAR): Geographic region where the sale occurred
          ...
    """
    col_lines = "\n".join(
        f"  - {col.name} ({col.type}): {col.description}"
        for col in table.columns
    )
    return (
        f"Table: {table.table_name}\n"
        f"Description: {table.description}\n"
        f"Columns:\n{col_lines}"
    )


def build_context_prompt(schema: SchemaContext, user_query: str) -> str:
    """
    Build a schema-aware prompt by combining:
        1. A structured schema block (table names, columns, descriptions)
        2. The strict SQL generation rules
        3. The user's natural language query

    The schema block is placed at the top so the model has full context
    before it reads the question.

    Args:
        schema:     The SchemaContext loaded from schema.json.
        user_query: The raw natural language question from the user.

    Returns:
        A single prompt string ready to be sent to the LLM.

    Example:
        >>> schema = load_schema()
        >>> prompt = build_context_prompt(schema, "Total sales by region last quarter")
        >>> print(prompt[:200])
        You are an expert SQL analyst...
    """
    schema_block_lines = [
        "DATABASE SCHEMA",
        "=" * 60,
        "Use ONLY the tables and columns listed below. Do not invent",
        "table or column names that are not present in this schema.",
        "",
    ]
    for table in schema.tables:
        schema_block_lines.append(_render_table(table))
        schema_block_lines.append("")  # blank line between tables

    schema_block = "\n".join(schema_block_lines).rstrip()

    rules_block = """\
STRICT RULES — you MUST follow all of them:
1. Output ONLY a valid SQL SELECT statement using the schema above.
2. NEVER generate DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, CREATE, EXEC,
   GRANT, REVOKE, MERGE, or any other data-modification or DDL statement.
3. If the user's question implies a data change, set sql to an empty string
   and explain why in the explanation field.
4. Reference only tables and columns that appear in the schema above.
5. Always include an explanation field describing in plain English what the SQL does.
6. Return your response as valid JSON with exactly these two keys:
   { "sql": "<SELECT statement>", "explanation": "<plain English explanation>" }
7. Do not include markdown code fences, comments, or any text outside the JSON object."""

    example_block = """\
EXAMPLE INPUT:
  Show me total sales by region for last quarter.

EXAMPLE OUTPUT:
  {
    "sql": "SELECT region, SUM(amount) AS total_sales FROM sales WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') GROUP BY region ORDER BY total_sales DESC",
    "explanation": "Aggregates total sales by region for the previous quarter, ordered from highest to lowest."
  }"""

    question_block = f"QUESTION:\n  {user_query}"

    return "\n\n".join([
        "You are an expert SQL analyst assistant integrated into an AI-powered data copilot.",
        schema_block,
        rules_block,
        example_block,
        question_block,
    ])
