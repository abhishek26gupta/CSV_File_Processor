# CSV Processing with AWS Lambda and LocalStack

This project demonstrates how to use AWS Lambda, S3, DynamoDB, and SNS in a local development environment using LocalStack. The Lambda function processes a CSV file uploaded to S3, extracts metadata, stores it in DynamoDB, and sends a notification via SNS.

## Prerequisites
- Kali Linux
- Python 3.8+
- AWS CLI
- LocalStack
- Docker
- boto3, pandas, numpy

## Setup
1. **Install Dependencies:**
   ```bash
   pip install boto3 pandas numpy
   ```

2. **Start LocalStack:**
   ```bash
   localstack start -d
   ```

3. **Set AWS Environment Variables:**
   ```bash
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Create Resources:**
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 mb s3://csv-upload-bucket
   aws --endpoint-url=http://localhost:4566 dynamodb create-table --table-name CsvMetadata --attribute-definitions AttributeName=filename,AttributeType=S --key-schema AttributeName=filename,KeyType=HASH --billing-mode PAY_PER_REQUEST
   aws --endpoint-url=http://localhost:4566 sns create-topic --name CsvProcessingComplete
   ```

5. **Package Lambda Function:**
   ```bash
   zip -r function.zip lambda_function.py
   ```

6. **Deploy Lambda Function:**
   ```bash
   aws --endpoint-url=http://localhost:4566 lambda create-function --function-name CsvProcessor --runtime python3.8 --role arn:aws:iam::000000000000:role/execution-role --handler lambda_function.lambda_handler --zip-file fileb://function.zip
   ```

7. **Subscribe to SNS Topic:**
   ```bash
   aws --endpoint-url=http://localhost:4566 sns subscribe --topic-arn arn:aws:sns:us-east-1:000000000000:CsvProcessingComplete --protocol email --notification-endpoint your-email@example.com
   ```
   *(Confirm the email subscription received in your inbox.)*

## Usage
1. **Upload a CSV File:**
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 cp example.csv s3://csv-upload-bucket/
   ```

2. **Invoke Lambda Manually (Optional):**
   ```bash
   aws --endpoint-url=http://localhost:4566 lambda invoke --function-name CsvProcessor --payload '{"Records": [{"s3": {"bucket": {"name": "csv-upload-bucket"}, "object": {"key": "example.csv"}}}]}' response.json
   ```

3. **Check DynamoDB for Metadata:**
   ```bash
   aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name CsvMetadata
   ```

4. **Check Logs:**
   ```bash
   aws --endpoint-url=http://localhost:4566 logs filter-log-events --log-group-name /aws/lambda/CsvProcessor
   ```

---
**Troubleshooting:**
- If you get a `No module named 'pandas'` error, package dependencies inside a `venv` and deploy them:
  ```bash
  mkdir package && pip install --target ./package boto3 pandas numpy
  cd package && zip -r ../function.zip .
  cd .. && zip -g function.zip lambda_function.py
  ```
  Then update the function:
  ```bash
  aws --endpoint-url=http://localhost:4566 lambda update-function-code --function-name CsvProcessor --zip-file fileb://function.zip
  ```

