# AWS Glue Python Shell job for fintechflow-silver-transactions
"""
Reads raw transactions CSV from S3 using chunk processing (3M rows),
applies cleaning transformations, and writes cleaned Parquet to S3.

Cleaning decisions:
    1. Remove duplicate transaction_id rows
    2. Flag null customer_id as orphaned transactions (retain)
    3. Flag null account_number (retain)
    4. Flag null branch_id (retain)
    5. Standardise inconsistent payment_channel values
    6. Standardise inconsistent transaction_status values
    7. Standardise inconsistent currency values
    8. Convert balance to numeric, set negatives to None

We set Glue job Max Capacity to 1 DPU minimum given 3M rows.

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
response = s3.get_object(Bucket=bucket_name, Key='raw/transactions/transactions_data.csv')
body = response['Body']

# masks defined before the loop
currency_mask = {
    'GBP': 'GBP',
    '£': 'GBP',
    'Sterling': 'GBP',
    'GB Pound': 'GBP'
}

payment_channels_mask = {
    'FPS': 'Faster Payments (FPS)', 'Faster Payments': 'Faster Payments (FPS)',
    'fps': 'Faster Payments (FPS)', 'FasterPayments': 'Faster Payments (FPS)',
    'BACS': 'Bacs Direct Debit', 'BacsDirectDebit': 'Bacs Direct Debit',
    'bacs': 'Bacs Direct Debit', 'Bacs_Direct_Debit': 'Bacs Direct Debit', 'Bacs': 'Bacs Direct Debit',
    'Bacs Credit': 'Bacs Direct Credit', 'BACS Direct Credit': 'Bacs Direct Credit',
    'Bacs_Credit': 'Bacs Direct Credit', 'bacs credit': 'Bacs Direct Credit', 'BacsCr': 'Bacs Direct Credit',
    'chaps': 'CHAPS', 'CHAPS payment': 'CHAPS', 'CHAPS_Transfer': 'CHAPS', 'CHAPS Transfer': 'CHAPS',
    'Contactless': 'Debit Card (Contactless)', 'Debit Contactless': 'Debit Card (Contactless)',
    'contless': 'Debit Card (Contactless)', 'card-contactless': 'Debit Card (Contactless)',
    'Chip & Pin': 'Debit Card (Chip & PIN)', 'Chip_and_Pin': 'Debit Card (Chip & PIN)',
    'PIN Debit': 'Debit Card (Chip & PIN)', 'chipandpin': 'Debit Card (Chip & PIN)',
    'Credit': 'Credit Card', 'CredCard': 'Credit Card', 'credit_card': 'Credit Card', 'CREDIT': 'Credit Card',
    'Digital Wallet': 'Digital Wallet (Apple/Google Pay)', 'ApplePay': 'Digital Wallet (Apple/Google Pay)',
    'GooglePay': 'Digital Wallet (Apple/Google Pay)', 'MobileWallet': 'Digital Wallet (Apple/Google Pay)',
    'DigiWallet': 'Digital Wallet (Apple/Google Pay)',
    'OpenBanking': 'Open Banking / Pay-by-Bank', 'PayByBank': 'Open Banking / Pay-by-Bank',
    'Open_Banking': 'Open Banking / Pay-by-Bank', 'OB': 'Open Banking / Pay-by-Bank',
    'ATM': 'ATM Withdrawal', 'atm': 'ATM Withdrawal',
    'ATM_Withdrawal': 'ATM Withdrawal', 'CashMachine': 'ATM Withdrawal',
    'SO': 'Standing Order', 'StandingOrder': 'Standing Order',
    'standing_order': 'Standing Order', 'std order': 'Standing Order',
    'cheq': 'Cheque', 'Cheque Payment': 'Cheque', 'cheque_payment': 'Cheque', 'CHK': 'Cheque'
}

transaction_status_mask = {
    'SUCCESS': 'Completed', 'OK': 'Completed',
    'Settled': 'Completed', 'Completed': 'Completed', 'done': 'Completed',
    'DECLINED': 'Failed', 'REJECTED': 'Failed', 'Failed': 'Failed', 'ERR': 'Failed'
}

# process in chunks
chunk_list = []
chunk_size = 50000

for chunk in pd.read_csv(body, chunksize=chunk_size):
    chunk = chunk.drop_duplicates(subset=['transaction_id'])
    chunk['orphaned'] = chunk['customer_id'].isna()
    chunk['missing_account'] = chunk['account_number'].isna()
    chunk['missing_branch'] = chunk['branch_id'].isna()
    chunk['payment_channel'] = chunk['payment_channel'].map(payment_channels_mask).fillna(chunk['payment_channel'])
    chunk['transaction_status'] = chunk['transaction_status'].map(transaction_status_mask).fillna(chunk['transaction_status'])
    chunk['currency'] = chunk['currency'].map(currency_mask).fillna(chunk['currency'])
    chunk['balance_after_transaction'] = pd.to_numeric(chunk['balance_after_transaction'], errors='coerce')
    chunk['balance_after_transaction'] = chunk['balance_after_transaction'].apply(
        lambda x: None if pd.notna(x) and x < 0 else x
    )
    chunk_list.append(chunk)

# combine all chunks into one DataFrame
transactions = pd.concat(chunk_list, ignore_index=True)

# operations that require the full dataset — run after combining
transactions = transactions.drop_duplicates(subset=['transaction_id'])

# write to S3 silver layer as parquet
buffer = io.BytesIO()
transactions.to_parquet(buffer, index=False)
buffer.seek(0)

s3.put_object(
    Bucket=bucket_name,
    Key='silver/transactions/transactions_silver.parquet',
    Body=buffer.getvalue()
)

print(f"Silver transactions written successfully. Rows: {len(transactions)}")
