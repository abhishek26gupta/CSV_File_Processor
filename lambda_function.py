import os
import json
import boto3
import pandas as pd
import logging
from datetime import datetime
from io import StringIO
from dotenv import load_dotenv
from typing import Any, Dict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "http://localhost:4566")
DYNAMODB_ENDPOINT: str = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
SNS_ENDPOINT: str = os.getenv("SNS_ENDPOINT", "http://localhost:4566")
TABLE_NAME: str = os.getenv("DYNAMODB_TABLE", "CsvMetadata")
SNS_TOPIC_ARN: str = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:000000000000:CsvProcessingComplete")

s3_client = boto3.client("s3", endpoint_url=S3_ENDPOINT)
dynamodb = boto3.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT)
sns_client = boto3.client("sns", endpoint_url=SNS_ENDPOINT)

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        for record in event.get("Records", []):
            bucket: str = record["s3"]["bucket"]["name"]
            key: str = record["s3"]["object"]["key"]

            csv_obj = s3_client.get_object(Bucket=bucket, Key=key)
            csv_data: str = csv_obj["Body"].read().decode("utf-8")
            df = pd.read_csv(StringIO(csv_data))

            metadata = {
                "filename": key,
                "upload_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "file_size_bytes": csv_obj["ContentLength"],
                "row_count": df.shape[0],
                "column_count": df.shape[1],
                "column_names": df.columns.tolist(),
            }

            table.put_item(Item=metadata)
            logger.info(f"Stored metadata for {key} in DynamoDB.")

            if SNS_TOPIC_ARN:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=json.dumps(metadata),
                    Subject="CSV Processing Complete",
                )
                logger.info(f"Sent SNS notification for {key}.")

        return {"statusCode": 200, "body": json.dumps("CSV processed successfully.")}
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps("Error processing CSV file")}

