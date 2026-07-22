# IBM Watson Challenge 2026 — AI Data Copilot

An AI-powered corporate data assistant built for the IBM Watson Challenge.  
Ask questions in plain language and receive structured query results, cost estimates, anomaly insights, and follow-up suggestions — all in one pipeline.

---

## Architecture Overview

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│   Angular 21 Frontend       │  HTTP  │   FastAPI Backend (Python 3.12)  │
│   (port 4200)               │◄──────►│   (port 8000)                    │
│                             │        │                                  │
│  • Chat interface           │        │  • NL → SQL (IBM ICA / watsonx)  │
│  • SQL preview + approval   │        │  • Query execution (Athena/mock) │
│  • Cost & metadata display  │        │  • Anomaly detection             │
│  • Saved query manager      │        │  • Conversation memory           │
│  • Audit log viewer         │        │  • Audit logging                 │
└─────────────────────────────┘        └──────────────┬───────────────────┘
                                                       │
                                        ┌──────────────▼───────────────────┐
                                        │   AWS (optional / production)    │
                                        │   Athena · S3 · Lambda · Glue   │
                                        └──────────────────────────────────┘
```

---

## Quick Start

Prerequisites: **Python 3.12+**, **Node.js 20+ / npm 11+**

```bash
# 1. Clone the repo
git clone <repo-url>
cd watson-challenge-2026

# 2. Backend — create environment and install dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env — at minimum set ICA_KEY or leave WATSONX_MOCK=True / ICA_MOCK=True for local dev

# 4. Start the backend
uvicorn app.main:app --reload
# API is available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs

# 5. Frontend (new terminal)
cd ../frontend
npm install
npm start
# App is available at http://localhost:4200
```

---

## Repository Structure

```
watson-challenge-2026/
├── backend/
│   ├── app/
│   │   ├── config.py               # Pydantic settings — all env vars
│   │   ├── main.py                 # FastAPI app factory + middleware
│   │   ├── controllers/            # HTTP route handlers (thin layer)
│   │   ├── services/               # Business logic (query pipeline, LLM, etc.)
│   │   ├── models/                 # Pydantic request / response schemas
│   │   ├── security/               # SQL validator + injection guard
│   │   ├── middleware/             # Request logging middleware
│   │   └── routers/routes.py       # Central router registration
│   ├── .env.example                # Template for all environment variables
│   ├── requirements.txt            # Python dependencies
│   └── tests/                      # pytest test suite
│
└── frontend/
    ├── src/app/
    │   ├── components/             # Chat, sidebar, navbar, right panel
    │   ├── services/               # Angular services (one per backend domain)
    │   └── models/copilot.models.ts # TypeScript interfaces
    ├── proxy.conf.json             # Dev proxy: /api → http://localhost:8000/api/v1
    └── package.json
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/v1/health` | Service health check |
| `POST` | `/api/v1/query` | Main pipeline — NL query → SQL → data → insights |
| `POST` | `/api/v1/sql/validate` | Validate a SQL string against the security ruleset |
| `POST` | `/api/v1/cost/estimate` | Estimate query cost (bytes scanned, USD) |
| `GET`  | `/api/v1/memory/{user_id}` | Retrieve conversation history for a user |
| `GET`  | `/api/v1/queries/saved` | List saved queries (filterable by `user_id`, `tag`) |
| `POST` | `/api/v1/queries/save` | Explicitly save a query |
| `GET`  | `/api/v1/queries/match` | Find saved queries by keyword similarity |
| `PATCH`| `/api/v1/queries/saved/{query_id}` | Update a saved query |
| `DELETE`| `/api/v1/queries/saved/{query_id}` | Delete a saved query |
| `GET`  | `/api/v1/audit` | List audit log entries |
| `GET`  | `/api/v1/copilot/next-steps` | LLM-generated follow-up question suggestions |

Full interactive documentation is available at **`http://localhost:8000/docs`** when the backend is running.

---

## Configuration

All settings are controlled via environment variables loaded from a `.env` file.  
See [`backend/.env.example`](backend/.env.example) for the full list and descriptions.

Key toggles for local development:

| Variable | Default | Purpose |
|----------|---------|---------|
| `WATSONX_MOCK` | `True` | Use static mock LLM responses (no API key needed) |
| `ICA_MOCK` | `True` | Use mock NL→SQL (no ICA key needed) |
| `DB_MOCK` | `True` | Use in-memory SQLite instead of PostgreSQL |
| `USE_ATHENA` | `False` | Route query execution to real AWS Athena |

---

## Running Tests

```bash
cd backend
pytest
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 21, TypeScript, Lucide icons |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| LLM | IBM watsonx.ai (`ibm/granite-13b-chat-v2`) · IBM ICA API |
| Query engine | AWS Athena (production) · SQLite mock (development) |
| Cloud | AWS Lambda · S3 · Glue |

---

## License

Internal IBM project — IBM Watson Challenge 2026.
