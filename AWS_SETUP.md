# AWS Production Setup Guide

This guide explains how to integrate and use the boto3 AWS client in your SQL Agent application for production deployment.

## Quick Start

### 1. Install Dependencies

```bash
pip install boto3>=1.35.0
```

Or use the updated `pyproject.toml`:

```bash
pip install -e .
```

### 2. Configure AWS Credentials

Choose one of these methods (in order of precedence):

#### Option A: Environment Variables (Recommended for EC2/ECS)
```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_SESSION_TOKEN=your-session-token  # Optional, for temporary credentials
```

#### Option B: .env File (Development)
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_DYNAMODB_TABLE=your-table-name
AWS_ENABLE_LOGGING=true
```

#### Option C: IAM Role (Recommended for Production EC2/ECS)
No configuration needed - boto3 will automatically use the instance/task IAM role.

### 3. Create AWS Resources

#### S3 Bucket
```bash
aws s3 mb s3://your-bucket-name --region us-east-1
```

#### DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name sql-agent-logs \
  --attribute-definitions AttributeName=userId,AttributeType=S AttributeName=timestamp,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Usage

### Import the Client

```python
from aws_client import aws_client

# The client is a singleton, automatically initialized
```

### S3 Operations

```python
# Upload file
aws_client.upload_to_s3(
    file_path="/path/to/file",
    bucket="my-bucket",
    key="subfolder/filename",
    metadata={"source": "sql-agent"}
)

# Download file
aws_client.download_from_s3(
    key="subfolder/filename",
    file_path="/local/path",
    bucket="my-bucket"
)
```

### DynamoDB Operations

```python
# Store item
aws_client.put_item_dynamodb({
    "userId": {"S": "user123"},
    "timestamp": {"S": "2025-05-19T10:30:00"},
    "query": {"S": "SELECT * FROM sales"},
    "results": {"N": "42"}
})

# Retrieve item
item = aws_client.get_item_dynamodb(
    key={
        "userId": {"S": "user123"},
        "timestamp": {"S": "2025-05-19T10:30:00"}
    }
)
```

### CloudWatch Metrics

```python
# Put custom metric
aws_client.put_metric(
    namespace="SQLAgent",
    metric_name="QueryExecutionTime",
    value=123.45,
    unit="Milliseconds",
    dimensions={"UserId": "user123", "QueryType": "SELECT"}
)
```

### CloudWatch Logs

```python
# Write to CloudWatch Logs
aws_client.log_to_cloudwatch(
    log_group="/aws/sql-agent/app",
    log_stream="production",
    message="Query executed successfully"
)
```

## FastAPI Integration Example

See `aws_integration_example.py` for complete examples including:
- Audit logging to DynamoDB
- Exporting query results to S3
- Health checks with CloudWatch metrics
- Query execution tracking

To use in your main app:

```python
from fastapi import FastAPI
from aws_integration_example import router as aws_router

app = FastAPI()
app.include_router(aws_router)
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region for all services |
| `AWS_ACCESS_KEY_ID` | None | AWS access key (optional if using IAM role) |
| `AWS_SECRET_ACCESS_KEY` | None | AWS secret access key |
| `AWS_SESSION_TOKEN` | None | Temporary session token for assumed roles |
| `AWS_S3_BUCKET` | None | Default S3 bucket name |
| `AWS_DYNAMODB_TABLE` | None | Default DynamoDB table name |
| `AWS_ENABLE_LOGGING` | `true` | Enable boto3 debug logging |

## IAM Policy for Production

### Minimal Policy for S3 + DynamoDB + CloudWatch

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/sql-agent-logs"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:PutLogEvents",
        "logs:CreateLogStream"
      ],
      "Resource": "*"
    }
  ]
}
```

## Production Deployment on AWS

### EC2 with IAM Role
1. Create EC2 instance with IAM role (with above policy)
2. No credentials needed - boto3 uses instance metadata
3. Set environment variables for S3 bucket/DynamoDB table

### ECS with Task Role
1. Create ECS task role with above policy
2. Launch task with IAM task role
3. boto3 automatically uses container credentials

### Lambda
```python
# No special configuration needed
from aws_client import aws_client

def lambda_handler(event, context):
    aws_client.upload_to_s3(...)
    return {"statusCode": 200}
```

## Error Handling

The client methods return boolean or None on error and log exceptions:

```python
if not aws_client.upload_to_s3("file.txt"):
    logger.error("Upload failed")

item = aws_client.get_item_dynamodb(key)
if not item:
    logger.error("Item not found or error occurred")
```

## Resource Cleanup

For graceful shutdown:

```python
from contextlib import asynccontextmanager
from aws_client import aws_client

@asynccontextmanager
async def lifespan(app):
    yield
    aws_client.close()  # Close all connections

app = FastAPI(lifespan=lifespan)
```

## Performance Tuning

The client is configured with:
- **Connection pooling**: max 10 concurrent connections
- **Retries**: Adaptive retry strategy with 3 max attempts
- **Timeouts**: 5s connect, 60s read
- **Lazy loading**: Clients created on first use

For high-load scenarios, increase pool connections in `aws_client.py`:

```python
def _get_boto_config(self):
    return Config(
        max_pool_connections=50,  # Increase for heavy workloads
        ...
    )
```

## Troubleshooting

### "Unable to locate credentials"
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Or use IAM role on EC2/ECS
- Or configure AWS CLI: `aws configure`

### "NoSuchBucket" or "NoSuchTable"
- Verify bucket/table names in environment variables
- Check AWS region matches resource location
- Confirm IAM permissions are correct

### Timeout errors
- Check network connectivity to AWS
- Increase timeout in `_get_boto_config()`
- Check CloudWatch for AWS service errors

### Enable detailed logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Then set AWS_ENABLE_LOGGING=true
```
