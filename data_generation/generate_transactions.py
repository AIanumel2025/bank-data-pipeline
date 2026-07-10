# Generating a realistic dataset of 3000000 UK banking transactions with deliberate dirty data injection to simulate real-world data quality issues.

# generate_branches.py must be run first (uses branches DataFrame)
# generate_customers.py must be run first (uses customers DataFrame)

import pandas as pd
import random
from datetime import date, timedelta

# reference lists
transaction_type = [
    'Deposit',
    'Withdrawals',
    'Bearer Cheque',
    'Order Cheque',
    'Card Transactions',
    'Online Transfer',
    'Standing Order',
    'International Transfer',
    'Forex Transactions'
]

merchant_category_map = {
    'Grocery Stores': 5411,
    'Supermarkets': 5411,
    'Restaurants': 5812,
    'Fast Food': 5814,
    'Service Stations (Fuel)': 5541,
    'Department Stores': 5311,
    'Clothing Stores': 5651,
    'Airlines': 4511,
    'Hotels/Motels': 3501,
    'Utilities (Electric, Gas, Water)': 4900,
    'Telecommunications': 4814,
    'Pharmacies': 5912,
    'Public Transport': 4111,
    'Professional Services': 8999,
    'Government Services': 9399
}

payment_channels = [
    'Faster Payments (FPS)',
    'Bacs Direct Debit',
    'Bacs Direct Credit',
    'CHAPS',
    'Debit Card (Contactless)',
    'Debit Card (Chip & PIN)',
    'Credit Card',
    'Digital Wallet (Apple/Google Pay)',
    'Open Banking / Pay-by-Bank',
    'ATM Withdrawal',
    'Standing Order',
    'Cheque'
]

transaction_status = ['Completed', 'Failed', 'Pending']

# Dirty Data Variants 
transaction_status_dirty = {
    'Completed': ['SUCCESS', 'OK', 'Settled', 'done'],
    'Failed': ['DECLINED', 'REJECTED', 'ERR']
}

currency_dirty = ['GBP', '£', 'Sterling', 'GB Pound']

payment_channels_dirty = {
    'Faster Payments (FPS)': ['FPS', 'Faster Payments', 'fps', 'FasterPayments'],
    'Bacs Direct Debit': ['BACS', 'BacsDirectDebit', 'bacs', 'Bacs_Direct_Debit', 'Bacs'],
    'Bacs Direct Credit': ['Bacs Credit', 'BACS Direct Credit', 'Bacs_Credit', 'bacs credit', 'BacsCr'],
    'CHAPS': ['chaps', 'CHAPS payment', 'CHAPS_Transfer', 'CHAPS Transfer'],
    'Debit Card (Contactless)': ['Contactless', 'Debit Contactless', 'contless', 'card-contactless'],
    'Debit Card (Chip & PIN)': ['Chip & Pin', 'Chip_and_Pin', 'PIN Debit', 'chipandpin'],
    'Credit Card': ['Credit', 'CredCard', 'credit_card', 'CREDIT'],
    'Digital Wallet (Apple/Google Pay)': ['Digital Wallet', 'ApplePay', 'GooglePay', 'MobileWallet', 'DigiWallet'],
    'Open Banking / Pay-by-Bank': ['OpenBanking', 'PayByBank', 'Open_Banking', 'OB'],
    'ATM Withdrawal': ['ATM', 'atm', 'ATM_Withdrawal', 'CashMachine'],
    'Standing Order': ['SO', 'StandingOrder', 'standing_order', 'std order'],
    'Cheque': ['cheq', 'Cheque Payment', 'cheque_payment', 'CHK']
}


# generator function
def generate_transactions(branches, customers):
    """
    Generates 3,000,000 transaction records.

    Args:
        branches: DataFrame from generate_branches()
        customers: DataFrame from generate_customers()

    Returns dataframe of raw transactions
    """
    transactions = []
    customer_ids = customers['cust_id'].tolist()
    branch_ids = branches['branch_id'].tolist()
    start = date(2024, 1, 1)

    for i in range(3000000):
        random_days = random.randint(0, 365)
        custom_id = random.choice(customer_ids)
        bran_id = random.choice(branch_ids)

        data__ = {
            'transaction_id': f"TXN{i + 1:07d}",
            'account_number': random.randint(10000000, 99999999),
            'customer_id': custom_id,
            'branch_id': bran_id,
            'transaction_date': start + timedelta(days=random_days),
            'transaction_type': random.choice(transaction_type),
            'balance_after_transaction': random.randint(10, 100000),
            'currency': 'GBP',
            'payment_channel': random.choice(payment_channels),
            'merchant_category_code': merchant_category_map[random.choice(list(merchant_category_map.keys()))],
            'transaction_status': random.choice(transaction_status),
            'fraud_flag': random.choices(['True', 'False'], weights=[10, 90])[0]
        }
        transactions.append(data__)
    return pd.DataFrame(transactions)


# Dirty Data Injection function
def inject_transaction_dirty(df):
    # Null customer_id and account_number (orphan transactions)
    null_idx = df.sample(frac=0.05).index
    df.loc[null_idx, 'customer_id'] = None
    df.loc[null_idx, 'account_number'] = None

    # Payment channel inconsistencies
    valid_pay = df['payment_channel'].isin(payment_channels_dirty.keys())
    pay_channel_idx = df[valid_pay].sample(frac=0.09).index
    df.loc[pay_channel_idx, 'payment_channel'] = df.loc[pay_channel_idx, 'payment_channel'].apply(
        lambda x: random.choice(payment_channels_dirty[x])
    )

    # Transaction status inconsistencies
    valid_status = df['transaction_status'].isin(transaction_status_dirty.keys())
    status_idx = df[valid_status].sample(frac=0.08).index
    df.loc[status_idx, 'transaction_status'] = df.loc[status_idx, 'transaction_status'].apply(
        lambda x: random.choice(transaction_status_dirty[x])
    )

    # Currency inconsistencies
    currency_idx = df.sample(frac=0.07).index
    df.loc[currency_idx, 'currency'] = df.loc[currency_idx, 'currency'].apply(
        lambda x: random.choice(currency_dirty)
    )

    # Duplicate rows
    duplicates = df.sample(frac=0.06)
    df = pd.concat([df, duplicates], ignore_index=True)

    # Invalid/negative balance values
    amnt_index = df.sample(frac=0.05).index
    df.loc[amnt_index, 'balance_after_transaction'] = df.loc[amnt_index, 'balance_after_transaction'].apply(
        lambda x: random.choice([0.0, -abs(x)]) if x is not None else x
    )

    # Null branch_id
    branch_idx = df.sample(frac=0.05).index
    df.loc[branch_idx, 'branch_id'] = None

    return df


# Main
if __name__ == "__main__":
    print("Loading branches and customers...")
    branches = pd.read_csv('real_branches_data.csv')
    customers = pd.read_csv('customer_data.csv')

    print("Generating transactions dataset (this may take several minutes)...")
    transactions = generate_transactions(branches, customers)
    dirty_transactions = inject_transaction_dirty(transactions)
    dirty_transactions.to_csv('transactions_data.csv', index=False)
    print(f"Done. Shape: {dirty_transactions.shape}")
