"""
s3_service.py — S3 helper for raw data uploads and exports.

Bucket: athena-results  (configured via AWS_S3_DATA_BUCKET)
Region: sa-east-1       (configured via AWS_REGION)

Provides:
    upload_file(local_path, s3_key)   — upload a local file to S3
    download_file(s3_key, local_path) — download a file from S3
    list_objects(prefix)              — list keys under a prefix
    presigned_url(s3_key, expiry_s)   — generate a pre-signed GET URL

IAM role resolution follows the same pattern as AthenaExecutor:
  - Inside Lambda: role is attached automatically.
  - Outside Lambda: if AWS_ROLE_ARN is set, STS AssumeRole is called.
"""

import logging
from typing import List, Optional

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
            RoleSessionName="AiDataCopilotS3Session",
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

def upload_file(local_path: str, s3_key: str, bucket: Optional[str] = None) -> str:
    """
    Upload a local file to the data bucket.

    Args:
        local_path: Absolute or relative path to the local file.
        s3_key:     Destination key inside the bucket (e.g. "uploads/data.csv").
        bucket:     Target bucket. Defaults to settings.AWS_S3_DATA_BUCKET.

    Returns:
        The full S3 URI of the uploaded object (s3://bucket/key).
    """
    bucket = bucket or settings.AWS_S3_DATA_BUCKET
    client = _boto_client("s3")
    client.upload_file(local_path, bucket, s3_key)
    uri = f"s3://{bucket}/{s3_key}"
    logger.info("S3 upload complete: %s", uri)
    return uri


def download_file(s3_key: str, local_path: str, bucket: Optional[str] = None) -> None:
    """
    Download a file from the data bucket to a local path.

    Args:
        s3_key:     Source key inside the bucket.
        local_path: Destination path on the local filesystem.
        bucket:     Source bucket. Defaults to settings.AWS_S3_DATA_BUCKET.
    """
    bucket = bucket or settings.AWS_S3_DATA_BUCKET
    client = _boto_client("s3")
    client.download_file(bucket, s3_key, local_path)
    logger.info("S3 download complete: s3://%s/%s → %s", bucket, s3_key, local_path)


def list_objects(prefix: str = "", bucket: Optional[str] = None) -> List[str]:
    """
    List object keys in the data bucket under a given prefix.

    Args:
        prefix: Key prefix to filter by (e.g. "uploads/").
        bucket: Bucket to list. Defaults to settings.AWS_S3_DATA_BUCKET.

    Returns:
        List of matching object keys (strings).
    """
    bucket = bucket or settings.AWS_S3_DATA_BUCKET
    client = _boto_client("s3")
    paginator = client.get_paginator("list_objects_v2")
    keys: List[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    logger.debug("S3 list_objects: bucket=%s prefix=%s → %d keys", bucket, prefix, len(keys))
    return keys


def presigned_url(s3_key: str, expiry_seconds: int = 3600, bucket: Optional[str] = None) -> str:
    """
    Generate a pre-signed GET URL for a private S3 object.

    Args:
        s3_key:         Key of the object inside the bucket.
        expiry_seconds: URL validity in seconds (default 1 hour).
        bucket:         Bucket. Defaults to settings.AWS_S3_DATA_BUCKET.

    Returns:
        A pre-signed HTTPS URL string.
    """
    bucket = bucket or settings.AWS_S3_DATA_BUCKET
    client = _boto_client("s3")
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
    logger.debug("S3 presigned URL generated for %s (expires in %ds)", s3_key, expiry_seconds)
    return url
