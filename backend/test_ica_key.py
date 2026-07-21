"""
Quick connectivity test for the IBM ICA API key.

Usage:
    python test_ica_key.py

The script loads ICA_KEY from the project root .env file and
probes a set of known ICA / watsonx endpoints to find which one
responds, confirming the key is valid and the service is reachable.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import httpx

# ---------------------------------------------------------------------------
# Load credentials from .env (never hardcode keys in source)
# Checks backend/.env first, then the workspace root .env as fallback.
# ---------------------------------------------------------------------------
_backend_env = Path(__file__).resolve().parent / ".env"
_root_env = Path(__file__).resolve().parents[2] / ".env"

if _backend_env.exists():
    load_dotenv(_backend_env)
    print(f"Loaded env from: {_backend_env}")
elif _root_env.exists():
    load_dotenv(_root_env)
    print(f"Loaded env from: {_root_env}")
else:
    sys.exit(f"ERROR: No .env file found at:\n  {_backend_env}\n  {_root_env}")

ICA_KEY: str = os.environ.get("ICA_KEY", "")
if not ICA_KEY:
    sys.exit(
        "ERROR: ICA_KEY is not set. "
        "Add it to your .env file and make sure it is not committed to git."
    )

# ---------------------------------------------------------------------------
# Candidate endpoints to probe (GET requests)
# All paths are from the official ICA OpenAPI spec.
# ---------------------------------------------------------------------------
ICA_BASE_URL = "https://api.nextgen-beta.ica.ibm.com/ica/v1"

CANDIDATES = [
    {
        "label": "ICA — list assistants",
        "url": f"{ICA_BASE_URL}/assistants",
    },
    {
        "label": "ICA — list agents",
        "url": f"{ICA_BASE_URL}/agents",
    },
    {
        "label": "ICA — list digital-workforce",
        "url": f"{ICA_BASE_URL}/digital-workforce",
    },
    {
        "label": "ICA — list chat-models",
        "url": f"{ICA_BASE_URL}/chat-models",
    },
    {
        "label": "ICA — list files",
        "url": f"{ICA_BASE_URL}/files",
    },
]


def probe(url: str, key: str) -> tuple[int, str]:
    """Return (status_code, short_body) for a GET request."""
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=10) as client:
        r = client.get(url, headers=headers)
    return r.status_code, r.text[:300]


def test_key() -> None:
    found = False

    for candidate in CANDIDATES:
        label = candidate["label"]
        url = candidate["url"]
        print(f"Trying  {label}")
        print(f"        {url}")

        try:
            status, body = probe(url, ICA_KEY)
        except httpx.ConnectError:
            print("        → SKIP — could not connect\n")
            continue
        except httpx.TimeoutException:
            print("        → SKIP — timed out\n")
            continue

        if status == 200:
            print(f"        → ✓ 200 OK  —  key is valid!\n")
            found = True
            break
        elif status == 401:
            print("        → FAIL 401 Unauthorized — key is invalid or expired.\n")
            sys.exit(1)
        elif status == 403:
            print("        → FAIL 403 Forbidden — key lacks permissions.\n")
            sys.exit(1)
        else:
            print(f"        → {status}  body: {body}\n")

    if not found:
        print(
            "No candidate endpoint returned 200.\n"
            "Please check the correct ICA base URL in the IBM Cloud service credentials\n"
            "and update CANDIDATES in this file."
        )
        sys.exit(1)


if __name__ == "__main__":
    test_key()
