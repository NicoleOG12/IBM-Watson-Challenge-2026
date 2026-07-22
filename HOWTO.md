# How-To Guide — AI Data Copilot

Step-by-step instructions for developers setting up, running, and extending the project.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Backend Setup](#2-backend-setup)
3. [Frontend Setup](#3-frontend-setup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Running with Real IBM ICA / watsonx Credentials](#5-running-with-real-ibm-ica--watsonx-credentials)
6. [Running with Real AWS Athena](#6-running-with-real-aws-athena)
7. [Using the API](#7-using-the-api)
8. [Running Tests](#8-running-tests)
9. [Adding a New Backend Endpoint](#9-adding-a-new-backend-endpoint)
10. [Mock vs. Real Mode Summary](#10-mock-vs-real-mode-summary)

---

## 1. Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.12 | Use `pyenv` or the official installer |
| Node.js | 20 LTS | npm 11+ is bundled |
| Git | any | — |
| AWS CLI (optional) | 2.x | Only needed for Athena / S3 |

---

## 2. Backend Setup

### 2.1 Create a virtual environment

```bash
cd watson-challenge-2026/backend

python -m venv .venv

# Activate — Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate — macOS / Linux
source .venv/bin/activate
```

### 2.2 Install dependencies

```bash
pip install -r requirements.txt
```

If you plan to use AWS services (Athena, Lambda, S3), uncomment and install `boto3`:

```bash
pip install "boto3>=1.34.0"
```

### 2.3 Create the `.env` file

```bash
cp .env.example .env
```

Edit `.env` with your credentials.  
For a fully local development run, the default mock settings work without any API keys:

```
WATSONX_MOCK=True
ICA_MOCK=True
DB_MOCK=True
USE_ATHENA=False
```

### 2.4 Start the backend server

```bash
uvicorn app.main:app --reload
```

The server starts at **`http://localhost:8000`**.

- Interactive Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`
- Health check → `http://localhost:8000/api/v1/health`

---

## 3. Frontend Setup

### 3.1 Install dependencies

```bash
cd watson-challenge-2026/frontend
npm install
```

### 3.2 Start the development server

```bash
npm start
# or: ng serve
```

The app starts at **`http://localhost:4200`**.

The Angular dev proxy (`proxy.conf.json`) forwards all `/api/*` requests to `http://localhost:8000/api/v1`, so the backend must be running on port 8000 for the UI to work.

### 3.3 Build for production

```bash
npm run build
```

Artifacts are output to `frontend/dist/`.

---

## 4. Environment Variables Reference

All variables live in `backend/.env` (copy from `backend/.env.example`).

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `AI Data Copilot` | Displayed in API metadata |
| `APP_VERSION` | `0.1.0` | Reported by `/health` |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `True` | Enables debug-level logging |
| `HOST` | `0.0.0.0` | Uvicorn bind host |
| `PORT` | `8000` | Uvicorn bind port |

### IBM watsonx.ai

| Variable | Default | Description |
|----------|---------|-------------|
| `WATSONX_API_KEY` | *(empty)* | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | *(empty)* | watsonx project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Regional endpoint |
| `WATSONX_MODEL_ID` | `ibm/granite-13b-chat-v2` | Model to use |
| `WATSONX_MAX_NEW_TOKENS` | `512` | Max tokens per completion |
| `WATSONX_TEMPERATURE` | `0.0` | Sampling temperature |
| `WATSONX_MOCK` | `True` | `True` = use static mock responses |

### IBM Consulting Advantage (ICA)

| Variable | Default | Description |
|----------|---------|-------------|
| `ICA_KEY` | *(empty)* | ICA developer API key (Settings → API Keys in the ICA UI) |
| `ICA_BASE_URL` | `https://api.nextgen-beta.ica.ibm.com/ica/v1` | ICA API base URL |
| `ICA_MODEL_ID` | `meta-llama/llama-4-maverick-17b-128e-instruct-fp8` | Chat model for NL→SQL |
| `ICA_MOCK` | `True` | `True` = use mock NL→SQL |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/copilot` | PostgreSQL connection string |
| `DB_MOCK` | `True` | `True` = use in-memory SQLite mock data |

### AWS

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `sa-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | *(empty)* | Static credentials (leave empty inside Lambda) |
| `AWS_SECRET_ACCESS_KEY` | *(empty)* | Static credentials (leave empty inside Lambda) |
| `AWS_ROLE_ARN` | *(empty)* | IAM Role to assume via STS (optional) |
| `USE_ATHENA` | `False` | `True` = route queries to real AWS Athena |
| `ATHENA_DB` | `db_watson` | Athena / Glue database name |
| `ATHENA_OUTPUT` | `s3://database-watson/query-results/` | S3 path for Athena results |
| `AWS_LAMBDA_FUNCTION_NAME` | `ConsulteFunction02` | Lambda function name |
| `AWS_S3_DATA_BUCKET` | `database-watson` | S3 bucket for raw data |
| `GLUE_DATABASE` | `db_watson` | Glue Data Catalog database |
| `GLUE_JOB_NAME` | *(empty)* | Glue ETL job name (optional) |

### Conversation & Audit

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_MAX_HISTORY` | `10` | Rolling conversation window per user |
| `AUDIT_ENABLED` | `True` | Enable/disable audit logging |
| `AUDIT_LOG_FILE` | `logs/audit.log` | Path to the JSON-lines audit file |

### Anomaly Detection

| Variable | Default | Description |
|----------|---------|-------------|
| `ANOMALY_VARIATION_THRESHOLD` | `30.0` | Coefficient of variation (%) above which a column is flagged |
| `ANOMALY_IQR_MULTIPLIER` | `1.5` | IQR fence multiplier for outlier detection (Tukey = 1.5) |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-me-in-production` | Application secret — **must** be rotated in production |

---

## 5. Running with Real IBM ICA / watsonx Credentials

1. Obtain an **ICA developer API key** from the ICA UI → Settings → API Keys.
2. In your `.env` file, set:

```env
ICA_KEY=<your-ica-key>
ICA_MOCK=False

WATSONX_API_KEY=<your-ibm-cloud-api-key>
WATSONX_PROJECT_ID=<your-project-id>
WATSONX_MOCK=False
```

3. Restart the backend:

```bash
uvicorn app.main:app --reload
```

The NL→SQL pipeline will now call the real ICA `/chat-models/chat/completions` endpoint.

> **Tip:** Keep `DB_MOCK=True` and `USE_ATHENA=False` while testing the LLM integration to avoid needing a real database.

---

## 6. Running with Real AWS Athena

1. Configure AWS credentials using one of these methods:
   - **Environment variables** — set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
   - **IAM Role** — set `AWS_ROLE_ARN` and the app will call STS `AssumeRole` at startup
   - **Instance profile** — leave credential variables empty when running inside Lambda

2. Set the following in `.env`:

```env
USE_ATHENA=True
ATHENA_DB=db_watson
ATHENA_OUTPUT=s3://database-watson/query-results/
AWS_REGION=sa-east-1
```

3. Install the AWS SDK if not already installed:

```bash
pip install "boto3>=1.34.0"
```

4. Restart the backend. Queries will now execute against real Athena.

---

## 7. Using the API

### Health check

```bash
curl http://localhost:8000/api/v1/health
```

```json
{ "status": "ok", "version": "0.1.0", "environment": "development" }
```

### Submit a natural language query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "natural_language_query": "Show me total sales by region for last quarter"
  }'
```

The response includes:
- `result.sql` — the generated SQL
- `result.data` — columns, rows, row count
- `result.insights` — anomaly summary and key insights
- `cost_estimate` — estimated bytes scanned and USD cost
- `next_steps` — three LLM-suggested follow-up questions
- `matched_query` — a previously saved query that matched (if any)

### Validate SQL

```bash
curl -X POST http://localhost:8000/api/v1/sql/validate \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM sales WHERE region = '\''North'\''"}'
```

### Save a query

```bash
curl -X POST http://localhost:8000/api/v1/queries/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "question": "Total sales by region",
    "sql": "SELECT region, SUM(amount) FROM sales GROUP BY region",
    "tags": ["sales", "regional"],
    "description": "Regional sales aggregation"
  }'
```

### List audit logs

```bash
curl "http://localhost:8000/api/v1/audit?user_id=user-123&limit=20"
```

---

## 8. Running Tests

```bash
cd watson-challenge-2026/backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_query_service.py

# Run smoke tests
python smoke_test.py
python smoke_test_remaining.py
```

Test configuration is in [`backend/pytest.ini`](backend/pytest.ini).

---

## 9. Adding a New Backend Endpoint

Follow the existing pattern — keep controllers thin and put logic in services.

**Step 1 — Create or update a service** in `backend/app/services/`:

```python
# backend/app/services/my_service.py
def do_something(data: str) -> str:
    return data.upper()
```

**Step 2 — Add a Pydantic model** in `backend/app/models/` (if needed):

```python
# backend/app/models/my_model.py
from pydantic import BaseModel

class MyRequest(BaseModel):
    data: str

class MyResponse(BaseModel):
    result: str
```

**Step 3 — Create a controller** in `backend/app/controllers/`:

```python
# backend/app/controllers/my_controller.py
from fastapi import APIRouter
from app.models.my_model import MyRequest, MyResponse
from app.services.my_service import do_something

router = APIRouter(tags=["My Feature"])

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest) -> MyResponse:
    return MyResponse(result=do_something(request.data))
```

**Step 4 — Register the router** in [`backend/app/routers/routes.py`](backend/app/routers/routes.py):

```python
from app.controllers.my_controller import router as my_router

api_router.include_router(my_router)
```

The new endpoint is now available at `POST /api/v1/my-endpoint`.

---

## 10. Mock vs. Real Mode Summary

| Feature | Mock mode (default) | Real mode |
|---------|--------------------|-----------| 
| NL→SQL | Static SQL string | IBM ICA API (`ICA_MOCK=False`) |
| LLM insights / next steps | Static responses | watsonx.ai (`WATSONX_MOCK=False`) |
| Query execution | In-memory SQLite | AWS Athena (`USE_ATHENA=True`) |
| Database | In-memory store | PostgreSQL (`DB_MOCK=False`) |

All four flags are independent — you can mix and match to test partial integrations.
