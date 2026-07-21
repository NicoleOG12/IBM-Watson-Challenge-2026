"""
docs_service.py — Automatic Markdown logbook generation for user sessions.

Assembles a chronological, human-readable Markdown document from a user's
enriched conversation history. Suitable for copy-paste into Confluence, Notion,
or a daily standup update.

Logbook structure per interaction:
    ## Query N — HH:MM (UTC)
    **Question:** ...
    **SQL:**
    ```sql
    ...
    ```
    **Tables:** table_a, table_b
    **Filters:** col > value, ...
    **Result:** N rows | Status: success

Public API
----------
    from app.services.docs_service import export_logbook

    markdown = export_logbook(user_id)
    # Returns None if the user has no history
"""

import logging
from datetime import timezone
from typing import Optional

from app.services.memory_service import get_user_memory

logger = logging.getLogger(__name__)


def export_logbook(user_id: str) -> Optional[str]:
    """
    Generate a Markdown logbook for a user's full session history.

    Pulls from the enriched memory store (tables_used, filters_applied,
    status, row_count populated by Sub-Task 1).

    Args:
        user_id: The user whose history to export.

    Returns:
        A Markdown string, or None if the user has no recorded interactions.
    """
    memory = get_user_memory(user_id)
    if not memory or not memory.interactions:
        logger.debug("No history found for logbook export", extra={"user_id": user_id})
        return None

    lines: list[str] = []

    # ── Document header ────────────────────────────────────────────────────
    lines.append(f"# Session Logbook — {user_id}")
    lines.append("")
    lines.append(
        f"_Generated automatically by Bob · {len(memory.interactions)} interaction(s)_"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── One section per interaction ────────────────────────────────────────
    for idx, interaction in enumerate(memory.interactions, start=1):
        # Format timestamp in UTC
        ts = interaction.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        time_str = ts.strftime("%H:%M UTC")
        date_str = ts.strftime("%Y-%m-%d")

        lines.append(f"## Query {idx} — {time_str} ({date_str})")
        lines.append("")
        lines.append(f"**Question:** {interaction.query}")
        lines.append("")

        # SQL block
        lines.append("**SQL:**")
        lines.append("```sql")
        lines.append(interaction.sql.strip())
        lines.append("```")
        lines.append("")

        # Tables
        if interaction.tables_used:
            lines.append(f"**Tables:** {', '.join(interaction.tables_used)}")
        else:
            lines.append("**Tables:** _none detected_")

        # Filters
        if interaction.filters_applied:
            lines.append(f"**Filters:** {' | '.join(interaction.filters_applied)}")
        else:
            lines.append("**Filters:** _none (full scan)_")

        # Result summary
        status_label = interaction.status.capitalize()
        lines.append(
            f"**Result:** {interaction.row_count} row(s) | Status: {status_label}"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    logger.info(
        "Logbook exported",
        extra={"user_id": user_id, "interactions": len(memory.interactions)},
    )

    return "\n".join(lines)
