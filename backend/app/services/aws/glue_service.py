"""
glue_service.py — AWS Glue helpers for catalog inspection and ETL job triggers.

Database: db_watson  (configured via GLUE_DATABASE)
Region:   sa-east-1  (configured via AWS_REGION)

Provides:
    list_tables(database)         — list table names in the Glue Data Catalog
    get_table_schema(table_name)  — return column metadata for a single table
    start_job(job_name, args)     — trigger a Glue ETL job run
    get_job_status(run_id)        — poll a job run's current status

IAM role resolution follows the same pattern as AthenaExecutor:
  - Inside Lambda: role is attached automatically.
  - Outside Lambda: if AWS_ROLE_ARN is set, STS AssumeRole is called.
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _boto_client(service: str):
    """
    Return a boto3 client for the given service.
    Uses STS-assumed credentials when AWS_ROLE_ARN is configured;
    otherwise relies on the default boto3 credential chain.
    """
    import boto3

    kwargs = {"region_name": settings.AWS_REGION}

    if settings.AWS_ROLE_ARN:
        sts = boto3.client("sts", region_name=settings.AWS_REGION)
        resp = sts.assume_role(
            RoleArn=settings.AWS_ROLE_ARN,
            RoleSessionName="AiDataCopilotGlueSession",
            DurationSeconds=3600,
        )
        creds = resp["Credentials"]
        kwargs.update(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )

    return boto3.client(service, **kwargs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_tables(database: Optional[str] = None) -> List[str]:
    """
    List all table names registered in the Glue Data Catalog database.

    Args:
        database: Glue database name. Defaults to settings.GLUE_DATABASE ("db_watson").

    Returns:
        List of table name strings.
    """
    database = database or settings.GLUE_DATABASE
    client = _boto_client("glue")
    paginator = client.get_paginator("get_tables")
    names: List[str] = []
    for page in paginator.paginate(DatabaseName=database):
        for table in page.get("TableList", []):
            names.append(table["Name"])
    logger.debug("Glue list_tables: database=%s → %d tables", database, len(names))
    return names


def get_table_schema(table_name: str, database: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Return column definitions for a Glue table.

    Args:
        table_name: Name of the table in the Glue Data Catalog.
        database:   Glue database name. Defaults to settings.GLUE_DATABASE.

    Returns:
        List of dicts with keys "name" and "type" for each column.
    """
    database = database or settings.GLUE_DATABASE
    client = _boto_client("glue")
    response = client.get_table(DatabaseName=database, Name=table_name)
    storage_desc = response["Table"].get("StorageDescriptor", {})
    columns = [
        {"name": col["Name"], "type": col["Type"]}
        for col in storage_desc.get("Columns", [])
    ]
    logger.debug(
        "Glue get_table_schema: database=%s table=%s → %d columns",
        database, table_name, len(columns),
    )
    return columns


def start_job(
    job_name: Optional[str] = None,
    arguments: Optional[Dict[str, str]] = None,
) -> str:
    """
    Trigger a Glue ETL job run.

    Args:
        job_name:  Glue job name. Defaults to settings.GLUE_JOB_NAME.
        arguments: Key-value pairs passed as --job-args to the Glue script.

    Returns:
        The JobRunId string for the triggered run.

    Raises:
        ValueError: If no job name is configured.
    """
    job_name = job_name or settings.GLUE_JOB_NAME
    if not job_name:
        raise ValueError(
            "GLUE_JOB_NAME must be set to trigger a Glue job. "
            "Set it in .env or pass job_name explicitly."
        )

    client = _boto_client("glue")
    kwargs: Dict[str, Any] = {"JobName": job_name}
    if arguments:
        kwargs["Arguments"] = arguments

    response = client.start_job_run(**kwargs)
    run_id: str = response["JobRunId"]
    logger.info("Glue job started: job=%s run_id=%s", job_name, run_id)
    return run_id


def get_job_status(run_id: str, job_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the current status of a Glue job run.

    Args:
        run_id:   The JobRunId returned by start_job().
        job_name: Glue job name. Defaults to settings.GLUE_JOB_NAME.

    Returns:
        Dict with keys:
            "state"   — e.g. "RUNNING", "SUCCEEDED", "FAILED", "STOPPED"
            "started" — ISO timestamp string (or None)
            "ended"   — ISO timestamp string (or None)
            "error"   — error message string (or None)
    """
    job_name = job_name or settings.GLUE_JOB_NAME
    client = _boto_client("glue")
    response = client.get_job_run(JobName=job_name, RunId=run_id)
    run = response["JobRun"]
    return {
        "state": run.get("JobRunState"),
        "started": str(run.get("StartedOn", "")),
        "ended": str(run.get("CompletedOn", "")),
        "error": run.get("ErrorMessage"),
    }
