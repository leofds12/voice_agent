"""
Example AWS integration for the FastAPI application.
This demonstrates production patterns for S3, DynamoDB, and CloudWatch integration.
"""

import logging
import json
from datetime import datetime
from fastapi import APIRouter
from aws_client import aws_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/aws", tags=["aws"])


@router.post("/upload-audit-log")
async def upload_audit_log(user_id: str, action: str, details: dict):
    """
    Example: Store audit logs in S3 and DynamoDB for tracking.
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "userId": {"S": user_id},
        "timestamp": {"S": timestamp},
        "action": {"S": action},
        "details": {"S": json.dumps(details)},
    }

    if aws_client.put_item_dynamodb(log_entry):
        aws_client.put_metric(
            namespace="SQLAgent",
            metric_name="AuditLogRecorded",
            value=1,
            dimensions={"UserId": user_id, "Action": action},
        )
        return {"status": "success", "timestamp": timestamp}
    return {"status": "error", "message": "Failed to store audit log"}


@router.post("/export-query-results")
async def export_query_results(sql_query: str, results: list):
    """
    Example: Export query results to S3.
    """
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    key = f"query-results/{timestamp}.json"

    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"query": sql_query, "results": results}, f)
            temp_file = f.name

        success = aws_client.upload_to_s3(
            file_path=temp_file,
            key=key,
            metadata={"query": sql_query[:100], "timestamp": timestamp},
        )

        if success:
            aws_client.put_metric(
                namespace="SQLAgent",
                metric_name="QueryExported",
                value=len(results),
                unit="Count",
            )
            return {"status": "success", "s3_key": key}
        return {"status": "error", "message": "Failed to upload to S3"}
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@router.get("/health/cloudwatch")
async def health_cloudwatch():
    """
    Example: Report application health to CloudWatch.
    """
    try:
        aws_client.put_metric(
            namespace="SQLAgent",
            metric_name="ApplicationHealth",
            value=1,
            dimensions={"Status": "Healthy"},
        )
        return {"status": "healthy", "cloudwatch": "metric_sent"}
    except Exception as e:
        logger.error(f"Failed to send health metric: {e}")
        return {"status": "error", "message": str(e)}


def log_agent_execution(query: str, duration_ms: float, success: bool):
    """
    Helper function to log agent execution metrics to CloudWatch.
    Call this after agent processes a message.
    """
    aws_client.put_metric(
        namespace="SQLAgent",
        metric_name="QueryExecutionTime",
        value=duration_ms,
        unit="Milliseconds",
    )
    aws_client.put_metric(
        namespace="SQLAgent",
        metric_name="QuerySuccess" if success else "QueryFailure",
        value=1,
        unit="Count",
    )
    logger.info(
        f"Logged execution metrics - Duration: {duration_ms}ms, Success: {success}"
    )
