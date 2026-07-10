# AWS Glue Python Shell job — fintechflow-silver-branches
"""
Reads raw branches CSV from S3, applies cleaning transformations,
and writes cleaned Parquet to the S3 silver layer

Cleaning actions:
    1. Removed duplicate branch_id rows
    2. Standardised inconsistent branch_type values
    3. Stripped whitespace from branch_manager names
    4. Filled missing no_of_staff with median value
    5. Dropped rows with invalid postcodes

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
obj = s3.get_object(Bucket=bucket_name, Key='raw/branches/real_branches_data.csv')
branches = pd.read_csv(io.BytesIO(obj['Body'].read()))

# cleaning process
# remove duplicates on branch_id first
branches = branches.drop_duplicates(subset=['branch_id'])

# standardise branch_type column
branch_type_mask = {
    'flagship': 'Flagship', 'FLAGSHIP': 'Flagship',
    'Flag-ship': 'Flagship', 'Flagshipp': 'Flagship', 'Premium': 'Flagship',
    'counter': 'Counter', 'COUNTER': 'Counter',
    'Counteer': 'Counter', 'Bank Counter': 'Counter', 'Desk': 'Counter',
    'self service': 'Self-Service', 'SELF-SERVICE': 'Self-Service',
    'SelfService': 'Self-Service', 'kiosk': 'Self-Service', 'Auto-Service': 'Self-Service',
    'hub': 'Hub', 'HUB': 'Hub',
    'Hubb': 'Hub', 'Central Hub': 'Hub', 'Branch Hub': 'Hub',
    'pop-up': 'Pop-Ups', 'pop up': 'Pop-Ups', 'POP-UP': 'Pop-Ups',
    'Popup': 'Pop-Ups', 'Popups': 'Pop-Ups', 'Event': 'Pop-Ups',
    'post office': 'Post Office Counters', 'PO Counter': 'Post Office Counters',
    'Post Office': 'Post Office Counters', 'PO': 'Post Office Counters', 'PostOffce': 'Post Office Counters',
    'multi bank': 'Multi-Bank', 'MULTI-BANK': 'Multi-Bank',
    'MultiBank': 'Multi-Bank', 'Shared Bank': 'Multi-Bank', 'Joint': 'Multi-Bank'
}
branches['branch_type'] = branches['branch_type'].map(branch_type_mask).fillna(branches['branch_type'])

# remove whitespaces
branches['branch_manager'] = branches['branch_manager'].str.strip()

# fill missing values in no_of_staff with median value
branches['no_of_staff'] = branches['no_of_staff'].fillna(branches['no_of_staff'].median())

# dropping invalid post codes
invalid_postcodes = [
    'BT1 1A',
    'B1234 567',
    'M9-9 ZZ',
    'G1 11A',
    'BS1A 1AA',
    'SA 1 1AA'
]
branches = branches[~branches['post_code'].isin(invalid_postcodes)]

# write cleaned data to S3 silver layer as parquet
buffer = io.BytesIO()
branches.to_parquet(buffer, index=False)
buffer.seek(0)

s3.put_object(
    Bucket=bucket_name,
    Key='silver/branches/branches_silver.parquet',
    Body=buffer.getvalue()
)

print(f"Silver branches written successfully. Rows: {len(branches)}")
