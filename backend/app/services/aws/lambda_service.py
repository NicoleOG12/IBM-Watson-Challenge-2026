"""
lambda_service.py — AWS Lambda invocation helpers.

Target function: ConsulteFunction02  (configured via AWS_LAMBDA_FUNCTION_NAME)
Region:          sa-east-1           (configured via AWS_REGION)

Provides:
    invoke_sync(payload)  — synchronous invocation (RequestResponse), returns parsed response
    invoke_async(payload) — asynchronous invocation (Event), fire-and-forget

IAM role resolution follows the same pattern as AthenaExecutor:
  - Inside Lambda: role is attached automatically.
  - Outside Lambda: if AWS_ROLE_ARN is set, STS AssumeRole is called.
"""

import json
import logging
from typing import Any, Dict, Optional

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
            RoleSessionName="AiDataCopilotLambdaSession",
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

def invoke_sync(
    payload: Dict[str, Any],
    function_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Invoke a Lambda function synchronously (RequestResponse) and return the response.

    Args:
        payload:       JSON-serialisable dict sent as the Lambda event.
        function_name: Lambda function name or ARN.
                       Defaults to settings.AWS_LAMBDA_FUNCTION_NAME.

    Returns:
        Parsed JSON response body from the Lambda function.

    Raises:
        RuntimeError: If the Lambda invocation returns a FunctionError.
    """
    function_name = function_name or settings.AWS_LAMBDA_FUNCTION_NAME
    client = _boto_client("lambda")

    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )

    if response.get("FunctionError"):
        error_payload = response["Payload"].read().decode("utf-8")
        raise RuntimeError(
            f"Lambda function {function_name} returned an error: {error_payload}"
        )

    raw = response["Payload"].read().decode("utf-8")
    result = json.loads(raw) if raw else {}
    logger.info("Lambda invoke_sync: function=%s status=%d", function_name, response["StatusCode"])
    return result


def invoke_async(
    payload: Dict[str, Any],
    function_name: Optional[str] = None,
) -> None:
    """
    Invoke a Lambda function asynchronously (Event) — fire-and-forget.

    Args:
        payload:       JSON-serialisable dict sent as the Lambda event.
        function_name: Lambda function name or ARN.
                       Defaults to settings.AWS_LAMBDA_FUNCTION_NAME.
    """
    function_name = function_name or settings.AWS_LAMBDA_FUNCTION_NAME
    client = _boto_client("lambda")

    client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8"),
    )
    logger.info("Lambda invoke_async: function=%s (fire-and-forget)", function_name)
