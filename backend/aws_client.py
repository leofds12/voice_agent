import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional, Any, Dict
import os
from config import (
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    AWS_S3_BUCKET,
    AWS_DYNAMODB_TABLE,
    AWS_ENABLE_LOGGING,
)

logger = logging.getLogger(__name__)

class AWSClient:
    """Production-grade AWS client with connection pooling and error handling."""

    def __init__(self):
        self._s3_client = None
        self._dynamodb_client = None
        self._cloudwatch_client = None
        self._logs_client = None
        self._session = None
        self._config = None
        self._init_logging()

    def _init_logging(self):
        if AWS_ENABLE_LOGGING:
            boto3.set_stream_logger("", logging.DEBUG)
            logger.info("AWS logging enabled")

    def _get_session(self) -> boto3.Session:
        if not self._session:
            session_kwargs = {"region_name": AWS_REGION}
            if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                session_kwargs.update({
                    "aws_access_key_id": AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
                })
                if AWS_SESSION_TOKEN:
                    session_kwargs["aws_session_token"] = AWS_SESSION_TOKEN

            self._session = boto3.Session(**session_kwargs)
            logger.info(f"AWS session created for region: {AWS_REGION}")

        return self._session

    def _get_boto_config(self) -> Config:
        if not self._config:
            self._config = Config(
                region_name=AWS_REGION,
                retries={"max_attempts": 3, "mode": "adaptive"},
                connect_timeout=5,
                read_timeout=60,
                max_pool_connections=10,
            )
        return self._config

    @property
    def s3(self):
        """Lazy-load S3 client."""
        if not self._s3_client:
            self._s3_client = self._get_session().client(
                "s3", config=self._get_boto_config()
            )
            logger.info("S3 client initialized")
        return self._s3_client

    @property
    def dynamodb(self):
        """Lazy-load DynamoDB client."""
        if not self._dynamodb_client:
            self._dynamodb_client = self._get_session().client(
                "dynamodb", config=self._get_boto_config()
            )
            logger.info("DynamoDB client initialized")
        return self._dynamodb_client

    @property
    def cloudwatch(self):
        """Lazy-load CloudWatch client."""
        if not self._cloudwatch_client:
            self._cloudwatch_client = self._get_session().client(
                "cloudwatch", config=self._get_boto_config()
            )
            logger.info("CloudWatch client initialized")
        return self._cloudwatch_client

    @property
    def logs(self):
        """Lazy-load CloudWatch Logs client."""
        if not self._logs_client:
            self._logs_client = self._get_session().client(
                "logs", config=self._get_boto_config()
            )
            logger.info("CloudWatch Logs client initialized")
        return self._logs_client

    def upload_to_s3(
        self,
        file_path: str,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Upload file to S3."""
        bucket = bucket or AWS_S3_BUCKET
        if not bucket:
            logger.error("S3 bucket not configured")
            return False

        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata

            key = key or os.path.basename(file_path)
            self.s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
            logger.info(f"File uploaded to S3: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False

    def download_from_s3(
        self, key: str, file_path: str, bucket: Optional[str] = None
    ) -> bool:
        """Download file from S3."""
        bucket = bucket or AWS_S3_BUCKET
        if not bucket:
            logger.error("S3 bucket not configured")
            return False

        try:
            self.s3.download_file(bucket, key, file_path)
            logger.info(f"File downloaded from S3: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False

    def put_item_dynamodb(
        self,
        item: Dict[str, Any],
        table: Optional[str] = None,
    ) -> bool:
        """Put item into DynamoDB table."""
        table = table or AWS_DYNAMODB_TABLE
        if not table:
            logger.error("DynamoDB table not configured")
            return False

        try:
            self.dynamodb.put_item(TableName=table, Item=item)
            logger.info(f"Item stored in DynamoDB table: {table}")
            return True
        except ClientError as e:
            logger.error(f"DynamoDB put_item failed: {e}")
            return False

    def get_item_dynamodb(
        self, key: Dict[str, Any], table: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB table."""
        table = table or AWS_DYNAMODB_TABLE
        if not table:
            logger.error("DynamoDB table not configured")
            return None

        try:
            response = self.dynamodb.get_item(TableName=table, Key=key)
            item = response.get("Item")
            if item:
                logger.info(f"Item retrieved from DynamoDB table: {table}")
            return item
        except ClientError as e:
            logger.error(f"DynamoDB get_item failed: {e}")
            return None

    def put_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Put custom metric to CloudWatch."""
        try:
            kwargs = {
                "Namespace": namespace,
                "MetricData": [
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                    }
                ],
            }
            if dimensions:
                kwargs["MetricData"][0]["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(**kwargs)
            logger.info(f"Metric published to CloudWatch: {namespace}/{metric_name}")
            return True
        except ClientError as e:
            logger.error(f"CloudWatch put_metric failed: {e}")
            return False

    def log_to_cloudwatch(
        self,
        log_group: str,
        log_stream: str,
        message: str,
        sequence_token: Optional[str] = None,
    ) -> Optional[str]:
        """Write logs to CloudWatch Logs."""
        try:
            kwargs = {
                "logGroupName": log_group,
                "logStreamName": log_stream,
                "logEvents": [{"message": message, "timestamp": int(__import__('time').time() * 1000)}],
            }
            if sequence_token:
                kwargs["sequenceToken"] = sequence_token

            response = self.logs.put_log_events(**kwargs)
            return response.get("nextSequenceToken")
        except ClientError as e:
            logger.error(f"CloudWatch Logs put_log_events failed: {e}")
            return None

    def close(self):
        """Close all client connections."""
        if self._s3_client:
            self._s3_client.close()
        if self._dynamodb_client:
            self._dynamodb_client.close()
        if self._cloudwatch_client:
            self._cloudwatch_client.close()
        if self._logs_client:
            self._logs_client.close()
        logger.info("AWS clients closed")


aws_client = AWSClient()
