# we generate a realistic dataset of 200000 UK bank loans
with deliberate dirty data injection to simulate real-world
data quality issues.

# generate_customers.py must be run first (uses customers DataFrame)
"""

import pandas as pd
import numpy as np
import random
from faker import Faker

fake = Faker()

# Reference Lists
loan_type = ['Mortgage', 'Personal', 'Joint', 'Guarantor']
loan_status = ['Active', 'Paid off']

# Dirty Data Variants
loan_status_dirty = {
    'Paid off': ['paid off', 'PAID', 'Closed', 'Settled', 'Fully Paid'],
    'Active': ['active', 'ACT', 'In Progress', 'Live', 'Ongoing']
}

invalid_rates = [0.0001, 0.99, 50.0, -0.05]


# generator function
def generate_loans(customers):
    loans = []
    customer_ids = customers['cust_id'].tolist()

    for i in range(200000):
        principal = random.randint(10000, 1000000)
        interest_rate = random.uniform(0.03, 0.30)
        term = random.randint(12, 480)

        # Monthly payment formula: M = P * (r(1+r)^n) / ((1+r)^n - 1)
        monthly_rate = interest_rate / 12
        monthly_payment = round(
            principal * (monthly_rate * (1 + monthly_rate) ** term) /
            ((1 + monthly_rate) ** term - 1), 2
        )
        remaining_balance = round(principal * random.uniform(0.1, 1.0), 2)

        loan_data = {
            'loan_id': f"LOAN{i + 1:06d}",
            'customer_id': random.choice(customer_ids),
            'loan_type': random.choice(loan_type),
            'principal_amount': principal,
            'interest_rate': round(interest_rate, 4),
            'term_months': term,
            'monthly_payment': monthly_payment,
            'loan_status': random.choices(['Active', 'Paid off'], weights=[90, 10])[0],
            'default_flag': random.choices(['True', 'False'], weights=[5, 95])[0],
            'issue_date': fake.date_between(start_date='-10y', end_date='today'),
            'balance': remaining_balance
        }
        loans.append(loan_data)
    return pd.DataFrame(loans)


# ── Dirty Data Injection ──────────────────────────────────────────────────────
def inject_loans_dirty(df):
    # Null interest rates
    null_idx = df.sample(frac=0.05).index
    df.loc[null_idx, 'interest_rate'] = np.nan

    # Null issue dates
    null_date_idx = df.sample(frac=0.05).index
    df.loc[null_date_idx, 'issue_date'] = None

    # Loan status inconsistencies
    valid_status = df['loan_status'].isin(loan_status_dirty.keys())
    status_idx = df[valid_status].sample(frac=0.08).index
    df.loc[status_idx, 'loan_status'] = df.loc[status_idx, 'loan_status'].apply(
        lambda x: random.choice(loan_status_dirty[x])
    )

    # Duplicate rows
    duplicates = df.sample(frac=0.06)
    df = pd.concat([df, duplicates], ignore_index=True)

    # Invalid interest rates
    rate_idx = df.sample(frac=0.05).index
    df.loc[rate_idx, 'interest_rate'] = df.loc[rate_idx, 'interest_rate'].apply(
        lambda x: random.choice(invalid_rates)
    )

    # Balance greater than principal (impossible in reality)
    balance_idx = df.sample(frac=0.04).index
    df.loc[balance_idx, 'balance'] = df.loc[balance_idx, 'principal_amount'] * random.uniform(1.1, 2.0)

    return df


# Main
if __name__ == "__main__":
    print("Loading customers...")
    customers = pd.read_csv('customer_data.csv')

    print("Generating loans dataset...")
    loans = generate_loans(customers)
    dirty_loans = inject_loans_dirty(loans)
    dirty_loans.to_csv('loans_data.csv', index=False)
    print(f"Done. Shape: {dirty_loans.shape}")
