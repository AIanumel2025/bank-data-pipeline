# AWS Glue Python Shell job for fintechflow-silver-customers
"""
Reads raw customers CSV from S3 using chunk processing (1M rows),
applies cleaning transformations, and writes cleaned Parquet to S3.

Cleaning actions:
    1. Removed duplicate cust_id rows
    2. Standardised inconsistent gender values
    3. Stripped whitespace from email addresses
    4. Converted empty strings to NaN in annual_income
    5. Filled missing annual_income with median value
    6. Dropped rows with invalid postcodes
    7. Standardised inconsistent kyc_status values

Note: I set Glue job Max Capacity to 1 DPU minimum given the 1M rows.

Job Parameters (set in Glue console):
    --BUCKET_NAME : S3 bucket name
    --REGION      : AWS region (e.g. eu-north-1)
"""

import sys
import io
import boto3
import pandas as pd
from awsglue.utils import getResolvedOptions

# obtaining job parameters
args = getResolvedOptions(sys.argv, ['BUCKET_NAME', 'REGION'])
bucket_name = args['BUCKET_NAME']
region = args['REGION']

s3 = boto3.client('s3', region_name=region)

# stream directly since we don't want to load entire file into memory
response = s3.get_object(Bucket=bucket_name, Key='raw/customers/customer_data.csv')
body = response['Body']

# masks defined before the loop
gender_mask = {
    'male': 'Male', 'MALE': 'Male', 'M': 'Male', 'm': 'Male',
    'female': 'Female', 'FEMALE': 'Female', 'F': 'Female', 'f': 'Female',
    'other': 'Other', 'OTHER': 'Other', 'O': 'Other', 'o': 'Other'
}

kyc_mask = {
    'verified': 'Verified', 'VERIFIED': 'Verified',
    'VErified': 'Verified', 'verify': 'Verified',
    'pending': 'Pending', 'PENDING': 'Pending',
    'pendinG': 'Pending', 'pend': 'Pending'
}

invalid_postcodes = [
    'BT1 1A', 'B1234 567', 'M9-9 ZZ',
    'G1 11A', 'BS1A 1AA', 'SA 1 1AA'
]

# process in chunks
chunk_list = []
chunk_size = 50000

for chunk in pd.read_csv(body, chunksize=chunk_size):
    chunk = chunk.drop_duplicates(subset=['cust_id'])
    chunk['gender'] = chunk['gender'].map(gender_mask).fillna(chunk['gender'])
    chunk['email'] = chunk['email'].str.strip()
    chunk['annual_income'] = pd.to_numeric(chunk['annual_income'], errors='coerce')
    chunk = chunk[~chunk['post_code'].isin(invalid_postcodes)]
    chunk['kyc_status'] = chunk['kyc_status'].map(kyc_mask).fillna(chunk['kyc_status'])
    chunk_list.append(chunk)

# combine all chunks into one DataFrame
customers = pd.concat(chunk_list, ignore_index=True)

# operations requiring full dataset — run after combining
customers = customers.drop_duplicates(subset=['cust_id'])
customers['annual_income'] = customers['annual_income'].fillna(
    customers['annual_income'].median()
)

# write to S3 silver layer as parquet
buffer = io.BytesIO()
customers.to_parquet(buffer, index=False)
buffer.seek(0)

s3.put_object(
    Bucket=bucket_name,
    Key='silver/customers/customers_silver.parquet',
    Body=buffer.getvalue()
)

print(f"Silver customers written successfully. Rows: {len(customers)}")
