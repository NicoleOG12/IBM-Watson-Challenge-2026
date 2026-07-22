"""
End-to-end test for ICA NL→SQL integration.

Usage:
    python test_ica_e2e.py

Requires in .env:
    ICA_KEY=<your-key>
    ICA_MOCK=False
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend dir first, then workspace root as fallback
_backend_env = Path(__file__).resolve().parent / ".env"
_root_env = Path(__file__).resolve().parents[2] / ".env"

if _backend_env.exists():
    load_dotenv(_backend_env)
    print(f"Loaded env from: {_backend_env}")
elif _root_env.exists():
    load_dotenv(_root_env)
    print(f"Loaded env from: {_root_env}")
else:
    sys.exit("ERROR: No .env file found.")

# Validate required settings before importing app modules
if not os.environ.get("ICA_KEY"):
    sys.exit("ERROR: ICA_KEY is not set in your .env file.")
if os.environ.get("ICA_MOCK", "True").strip().lower() in ("true", "1"):
    sys.exit(
        "ERROR: ICA_MOCK is still True. Set ICA_MOCK=False in your .env to use the real API."
    )

from app.models.llm import LLMRequest
from app.services.ica_service import generate_sql

TEST_QUERIES = [
    "Show me total sales by region",
    "What are the top 5 products by revenue?",
]


async def run() -> None:
    for query in TEST_QUERIES:
        print(f"\n{'-' * 60}")
        print(f"Query : {query}")

        result = await generate_sql(LLMRequest(natural_language_query=query))

        if result.sql:
            print(f"SQL   : {result.sql[:200]}{'...' if len(result.sql) > 200 else ''}")
            print(f"Expl  : {result.explanation[:150]}{'...' if len(result.explanation) > 150 else ''}")
            print("Status: OK")
        else:
            print(f"Status: FAIL - No SQL returned")
            print(f"Reason: {result.explanation}")

    print(f"\n{'-' * 60}")
    print("ICA e2e test complete.")


if __name__ == "__main__":
    asyncio.run(run())
