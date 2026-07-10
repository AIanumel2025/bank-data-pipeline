# boto3 S3 Ingestion Script
# To upload generated CSV datasets to the Fintechflow S3 bronze layer.

Folder structure in S3:
    raw/branches/real_branches_data.csv
    raw/customers/customer_data.csv
    raw/transactions/transactions_data.csv
    raw/loans/loans_data.csv

Authentication:
    Uses AWS credentials stored in Google Colab Secrets Manager.
    Keys required:
        - aws_access_key_id
        - aws_secret_access_key

Usage:
    Run in Google Colab after generating all four datasets.
    Ensure CSV files are uploaded to /content/ in Colab first.
"""

import boto3
from google.colab import userdata

# AWS credentials
aws_access_key_id = userdata.get('aws_access_key_id')
aws_secret_access_key = userdata.get('aws_secret_access_key')

# S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='eu-north-1'
)

# configuration
bucket_name = 'fintechflow-raw-aanumel-065320271511-eu-north-1-an'

# Local Colab path to S3 destination key
datasets = {
    '/content/real_branches_data.csv': 'raw/branches/real_branches_data.csv',
    '/content/customer_data.csv':      'raw/customers/customer_data.csv',
    '/content/transactions_data.csv':  'raw/transactions/transactions_data.csv',
    '/content/loans_data.csv':         'raw/loans/loans_data.csv'
}

# Upload
for local_path, s3_key in datasets.items():
    print(f"  Uploading {local_path} → s3://{bucket_name}/{s3_key}")
    s3.upload_file(local_path, bucket_name, s3_key)
    print(f"  Done")

print("\nAll datasets uploaded successfully to S3 bronze layer.")
