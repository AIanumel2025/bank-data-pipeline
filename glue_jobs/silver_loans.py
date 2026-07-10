# AWS Glue Python Shell job for fintechflow-silver-loans
"""
Reads raw loans CSV from S3, applies cleaning transformations,
and writes cleaned Parquet to the S3 silver layer.

Cleaning decisions:
    1. Removed duplicate loan_id rows
    2. Standardised inconsistent loan_status values
    3. Set invalid interest rates to None (outside 0.03-0.30 UK range)
    4. Dropped rows with missing issue_date (cannot place in reporting period)
    5. Set balance > principal to None (impossible — system error)
    6. Converted and round all numeric columns to 2 decimal places

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

# we read the raw csv file from s3 into a dataframe
s3 = boto3.client('s3', region_name=region)
obj = s3.get_object(Bucket=bucket_name, Key='raw/loans/loans_data.csv')
loans = pd.read_csv(io.BytesIO(obj['Body'].read()))

# cleaning process
# remove duplicates on loan_id first
loans = loans.drop_duplicates(subset=['loan_id'])

# standardise loan_status column
loan_status_mask = {
    'paid off': 'Paid off', 'PAID': 'Paid off',
    'Closed': 'Paid off', 'Settled': 'Paid off', 'Fully Paid': 'Paid off',
    'active': 'Active', 'ACT': 'Active',
    'In Progress': 'Active', 'Live': 'Active', 'Ongoing': 'Active'
}
loans['loan_status'] = loans['loan_status'].map(loan_status_mask).fillna(loans['loan_status'])

# addressing invalid interest rates
loans['interest_rate'] = loans['interest_rate'].apply(
    lambda x: None if pd.notna(x) and (x < 0.03 or x > 0.30) else x
)

# drop examples with missing values in the issue_date column
loans.dropna(subset=['issue_date'], inplace=True)

# addressing instances where balance > principal amount
loans.loc[loans['balance'] > loans['principal_amount'], 'balance'] = None

# handle all numerical columns and round them to 2 decimal places
numeric_cols = [
    'principal_amount',
    'interest_rate',
    'term_months',
    'monthly_payment',
    'balance'
]
for col in numeric_cols:
    loans[col] = pd.to_numeric(loans[col], errors='coerce').round(2)

# write cleaned data to S3 silver layer as parquet
buffer = io.BytesIO()
loans.to_parquet(buffer, index=False)
buffer.seek(0)

s3.put_object(
    Bucket=bucket_name,
    Key='silver/loans/loans_silver.parquet',
    Body=buffer.getvalue()
)

print(f"Silver loans written successfully. Rows: {len(loans)}")
