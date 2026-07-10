# We generates a realistic dataset of 1,000,000 UK bank customers
again with deliberate dirty data injection to simulate real-world
data quality issues.

# generate_branches.py must be run first  because it uses branches DataFrame

import pandas as pd
import random
import string
from faker import Faker

fake = Faker()

city = [
    'Belfast', 'Birmingham', 'Bristol', 'Manchester',
    'Edinburgh', 'Glasgow', 'Leeds', 'Derry', 'Cardiff', 'Swansea'
]

risk_rating = ['Low', 'Medium', 'High']
kyc_status = ['Verified', 'Pending']
employment_status = ['Employed', 'Self-Employed', 'Unemployed']
marital_status = ['Married', 'Single', 'Divorced', 'Widowed']
gender = ['Male', 'Female', 'Other']

# dataset maps
city_province_map = {
    'Belfast': 'Northern Ireland',
    'Birmingham': 'England',
    'Bristol': 'England',
    'Manchester': 'England',
    'Edinburgh': 'Scotland',
    'Glasgow': 'Scotland',
    'Leeds': 'England',
    'Derry': 'Northern Ireland',
    'Cardiff': 'Wales',
    'Swansea': 'Wales'
}

city_postcode_map = {
    'Belfast': 'BT',
    'Birmingham': 'B',
    'Bristol': 'BS',
    'Manchester': 'M',
    'Edinburgh': 'EH',
    'Glasgow': 'G',
    'Leeds': 'LS',
    'Derry': 'BT',
    'Cardiff': 'CF',
    'Swansea': 'SA'
}

occupation_map = {
    'Employed': [
        'National Health Service (NHS) - Nurse',
        'Tesco PLC - Retail Assistant',
        'Lloyds Banking Group - Financial Analyst',
        'BT Group - Telecommunications Engineer',
        'AstraZeneca - Research Scientist',
        'Ministry of Defence - Civil Servant'
    ],
    'Self-Employed': [
        'Freelance Web Developer',
        'Private Tutor (Maths/Science)',
        'Independent Handyperson',
        'Mobile Hair/Beauty Therapist',
        'Street Food Trader',
        'Freelance Content Creator/Copywriter'
    ],
    'Unemployed': [
        'Actively seeking entry-level retail positions',
        'Recently graduated student applying for graduate schemes',
        'Individual transitioning between contracts',
        'Former hospitality worker seeking immediate re-employment'
    ]
}

# Dirty data variants
gender_dirty = {
    'Male': ['male', 'MALE', 'M', 'm'],
    'Female': ['female', 'FEMALE', 'F', 'f'],
    'Other': ['other', 'OTHER', 'O', 'o']
}

dirty_kyc = {
    'Verified': ['verified', 'VERIFIED', 'VErified', 'verify'],
    'Pending': ['pending', 'PENDING', 'pendinG', 'pend']
}

invalid_postcodes = [
    'BT1 1A',
    'B1234 567',
    'M9-9 ZZ',
    'G1 11A',
    'BS1A 1AA',
    'SA 1 1AA'
]

# function to generate postcodes
def generate_postcode(selected_city):
    prefix = city_postcode_map.get(selected_city)
    outward_num = random.randint(1, 9)
    inward_num = random.randint(1, 9)
    inward_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"{prefix}{outward_num} {inward_num}{inward_letters}"


# Dataset generating function
def generate_customers():
    cust = []
    for i in range(1000000):
        current_emp_status = random.choice(employment_status)
        current_city = random.choice(city)
        data_ = {
            'cust_id': f"CUST{i + 1:07d}",
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'gender': random.choice(gender),
            'marital_status': random.choice(marital_status),
            'employment_status': current_emp_status,
            'kyc_status': random.choice(kyc_status),
            'risk_rating': random.choice(risk_rating),
            'address': fake.address().replace('\n', ', '),
            'city': current_city,
            'province': city_province_map[current_city],
            'post_code': generate_postcode(current_city),
            'phone_number': fake.phone_number(),
            'email': fake.email(),
            'annual_income': random.randint(20000, 1000000),
            'occupation': random.choice(occupation_map[current_emp_status])
        }
        cust.append(data_)
    return pd.DataFrame(cust)


# dirty data injection function
def inject_customer_dirty(df):
    # Gender inconsistencies
    valid_mask = df['gender'].isin(gender_dirty.keys())
    gender_index = df[valid_mask].sample(frac=0.05).index
    df.loc[gender_index, 'gender'] = df.loc[gender_index, 'gender'].apply(
        lambda x: random.choice(gender_dirty[x])
    )

    # Invalid postcodes
    post_index = df.sample(frac=0.03).index
    df.loc[post_index, 'post_code'] = df.loc[post_index, 'post_code'].apply(
        lambda x: random.choice(invalid_postcodes)
    )

    # Email whitespaces
    email_index = df.sample(frac=0.08).index
    df.loc[email_index, 'email'] = df.loc[email_index, 'email'].apply(lambda x: " " + x)

    # Missing annual income values
    income_index = df.sample(frac=0.07).index
    df.loc[income_index, 'annual_income'] = None

    # Duplicate rows
    duplicates = df.sample(frac=0.05)
    df = pd.concat([df, duplicates], ignore_index=True)

    # 6. KYC status inconsistencies
    kyc_mask = df['kyc_status'].isin(dirty_kyc.keys())
    kyc_index = df[kyc_mask].sample(frac=0.10).index
    df.loc[kyc_index, 'kyc_status'] = df.loc[kyc_index, 'kyc_status'].apply(
        lambda x: random.choice(dirty_kyc[x])
    )

    return df


# Main
if __name__ == "__main__":
    print("Generating customers dataset (this may take several minutes)...")
    customers = generate_customers()
    dirty_customers = inject_customer_dirty(customers)
    dirty_customers.to_csv('customer_data.csv', index=False)
    print(f"Done. Shape: {dirty_customers.shape}")
