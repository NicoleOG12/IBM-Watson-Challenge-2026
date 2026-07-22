"""
aws_controller.py — REST endpoints for the AWS integrations.

Prefix: /aws

Endpoints:
    GET  /aws/status            — connectivity check for Athena, S3, Glue, Lambda
    GET  /aws/glue/tables       — list tables in the Glue Data Catalog
    GET  /aws/glue/tables/{table}/schema — return column metadata for a table
    POST /aws/glue/jobs/start   — trigger a Glue ETL job run
    GET  /aws/glue/jobs/{run_id} — poll a Glue job run status
    GET  /aws/s3/objects        — list objects in the data bucket
    POST /aws/s3/presign        — generate a pre-signed GET URL
    POST /aws/lambda/invoke     — invoke Lambda synchronously
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/aws", tags=["AWS"])


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class GlueJobStartRequest(BaseModel):
    job_name: Optional[str] = None
    arguments: Optional[Dict[str, str]] = None


class S3PresignRequest(BaseModel):
    s3_key: str
    expiry_seconds: int = 3600
    bucket: Optional[str] = None


class LambdaInvokeRequest(BaseModel):
    payload: Dict[str, Any]
    function_name: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status", summary="AWS connectivity status")
async def aws_status():
    """
    Quick connectivity check that verifies each AWS service is reachable
    using the configured region, role, and credentials.

    Returns a dict with a 'services' key whose values are either 'ok' or
    an error message string.
    """
    results: Dict[str, str] = {}

    # ── Athena ────────────────────────────────────────────────────────────────
    try:
        import boto3
        client = boto3.client("athena", region_name=settings.AWS_REGION)
        client.list_work_groups()
        results["athena"] = "ok"
    except Exception as exc:
        results["athena"] = str(exc)

    # ── S3 ────────────────────────────────────────────────────────────────────
    try:
        import boto3
        client = boto3.client("s3", region_name=settings.AWS_REGION)
        client.head_bucket(Bucket=settings.AWS_S3_DATA_BUCKET)
        results["s3"] = "ok"
    except Exception as exc:
        results["s3"] = str(exc)

    # ── Glue ──────────────────────────────────────────────────────────────────
    try:
        import boto3
        client = boto3.client("glue", region_name=settings.AWS_REGION)
        client.get_database(Name=settings.GLUE_DATABASE)
        results["glue"] = "ok"
    except Exception as exc:
        results["glue"] = str(exc)

    # ── Lambda ────────────────────────────────────────────────────────────────
    try:
        import boto3
        client = boto3.client("lambda", region_name=settings.AWS_REGION)
        client.get_function(FunctionName=settings.AWS_LAMBDA_FUNCTION_NAME)
        results["lambda"] = "ok"
    except Exception as exc:
        results["lambda"] = str(exc)

    return {
        "region": settings.AWS_REGION,
        "athena_db": settings.ATHENA_DB,
        "s3_bucket": settings.AWS_S3_DATA_BUCKET,
        "glue_database": settings.GLUE_DATABASE,
        "lambda_function": settings.AWS_LAMBDA_FUNCTION_NAME,
        "services": results,
    }


# ── Glue endpoints ────────────────────────────────────────────────────────────

@router.get("/glue/tables", summary="List Glue Data Catalog tables")
async def glue_list_tables(database: Optional[str] = Query(None)):
    """List all tables registered in the Glue Data Catalog database (default: db_watson)."""
    try:
        from app.services.aws.glue_service import list_tables
        tables = list_tables(database)
        return {"database": database or settings.GLUE_DATABASE, "tables": tables}
    except Exception as exc:
        logger.error("glue_list_tables error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/glue/tables/{table_name}/schema", summary="Get Glue table schema")
async def glue_table_schema(table_name: str, database: Optional[str] = Query(None)):
    """Return column definitions for a single Glue table."""
    try:
        from app.services.aws.glue_service import get_table_schema
        columns = get_table_schema(table_name, database)
        return {
            "database": database or settings.GLUE_DATABASE,
            "table": table_name,
            "columns": columns,
        }
    except Exception as exc:
        logger.error("glue_table_schema error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/glue/jobs/start", summary="Start a Glue ETL job")
async def glue_start_job(body: GlueJobStartRequest):
    """Trigger a Glue ETL job run and return the run ID."""
    try:
        from app.services.aws.glue_service import start_job
        run_id = start_job(body.job_name, body.arguments)
        return {"job_name": body.job_name or settings.GLUE_JOB_NAME, "run_id": run_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("glue_start_job error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/glue/jobs/{run_id}", summary="Get Glue job run status")
async def glue_job_status(run_id: str, job_name: Optional[str] = Query(None)):
    """Poll the status of a Glue job run."""
    try:
        from app.services.aws.glue_service import get_job_status
        status = get_job_status(run_id, job_name)
        return {"run_id": run_id, **status}
    except Exception as exc:
        logger.error("glue_job_status error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ── S3 endpoints ──────────────────────────────────────────────────────────────

@router.get("/s3/objects", summary="List S3 objects")
async def s3_list_objects(
    prefix: str = Query("", description="Key prefix to filter"),
    bucket: Optional[str] = Query(None),
):
    """List object keys in the data bucket under a given prefix."""
    try:
        from app.services.aws.s3_service import list_objects
        keys = list_objects(prefix, bucket)
        return {"bucket": bucket or settings.AWS_S3_DATA_BUCKET, "prefix": prefix, "keys": keys}
    except Exception as exc:
        logger.error("s3_list_objects error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/s3/presign", summary="Generate pre-signed S3 URL")
async def s3_presign(body: S3PresignRequest):
    """Generate a pre-signed GET URL for a private S3 object."""
    try:
        from app.services.aws.s3_service import presigned_url
        url = presigned_url(body.s3_key, body.expiry_seconds, body.bucket)
        return {"url": url, "expires_in_seconds": body.expiry_seconds}
    except Exception as exc:
        logger.error("s3_presign error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ── Lambda endpoint ───────────────────────────────────────────────────────────

@router.post("/lambda/invoke", summary="Invoke Lambda function")
async def lambda_invoke(body: LambdaInvokeRequest):
    """Invoke a Lambda function synchronously and return its response."""
    try:
        from app.services.aws.lambda_service import invoke_sync
        result = invoke_sync(body.payload, body.function_name)
        return {
            "function": body.function_name or settings.AWS_LAMBDA_FUNCTION_NAME,
            "result": result,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.error("lambda_invoke error", exc_info=exc)
        raise HTTPException(status_code=502, detail=str(exc))
