# In this file I generate a realistic dataset of 800 UK bank branches
with deliberate dirty data injection to simulate real-world
data quality issues.

import pandas as pd
import random
import string
from faker import Faker

fake = Faker()

city = [
    'Belfast', 'Birmingham', 'Bristol', 'Manchester',
    'Edinburgh', 'Glasgow', 'Leeds', 'Derry', 'Cardiff', 'Swansea'
]

branch_type = [
    'Flagship', 'Counter', 'Self-Service', 'Hub',
    'Pop-Ups', 'Post Office Counters', 'Multi-Bank'
]

# maps 
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

# Include dirty data variants
dirty_branch_types = {
    'Flagship': ['flagship', 'FLAGSHIP', 'Flag-ship', 'Flagshipp', 'Premium'],
    'Counter': ['counter', 'COUNTER', 'Counteer', 'Bank Counter', 'Desk'],
    'Self-Service': ['self service', 'SELF-SERVICE', 'SelfService', 'kiosk', 'Auto-Service'],
    'Hub': ['hub', 'HUB', 'Hubb', 'Central Hub', 'Branch Hub'],
    'Pop-Ups': ['pop-up', 'pop up', 'POP-UP', 'Popup', 'Popups', 'Event'],
    'Post Office Counters': ['post office', 'PO Counter', 'Post Office', 'PO', 'PostOffce'],
    'Multi-Bank': ['multi bank', 'MULTI-BANK', 'MultiBank', 'Shared Bank', 'Joint']
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


# generator function
def generate_branches():
    data = []
    for i in range(800):
        selected_city = random.choice(city)
        br = {
            'branch_id': f"BR{i + 1:03d}",
            'branch_name': f"{selected_city} branch",
            'branch_city': selected_city,
            'branch_province': city_province_map[selected_city],
            'post_code': generate_postcode(selected_city),
            'opening_date': fake.date_between(start_date='-8y', end_date='today'),
            'branch_manager': fake.name(),
            'no_of_staff': random.randint(1, 50),
            'branch_type': random.choice(branch_type)
        }
        data.append(br)
    return pd.DataFrame(data)


# we apply the dirty data injection function
def inject_dirty_data(df):
    # Whitespace issues in branch_manager
    valid_mask = df['gender'].isin(dirty_branch_types.keys()) if 'gender' in df.columns else pd.Series([True] * len(df))
    branch_index = df.sample(frac=0.05).index
    df.loc[branch_index, 'branch_manager'] = df.loc[branch_index, 'branch_manager'].apply(lambda x: " " + x)

    # Missing no_of_staff values
    staff_index = df.sample(frac=0.10).index
    df.loc[staff_index, 'no_of_staff'] = None

    # Inconsistent branch_type values
    valid_mask = df['branch_type'].isin(dirty_branch_types.keys())
    type_index = df[valid_mask].sample(frac=0.10).index
    df.loc[type_index, 'branch_type'] = df.loc[type_index, 'branch_type'].apply(
        lambda x: random.choice(dirty_branch_types[x])
    )

    # Duplicate rows
    duplicates = df.sample(frac=0.02)
    df = pd.concat([df, duplicates], ignore_index=True)

    # Invalid postcodes
    post_index = df.sample(frac=0.03).index
    df.loc[post_index, 'post_code'] = df.loc[post_index, 'post_code'].apply(
        lambda x: random.choice(invalid_postcodes)
    )

    return df


# Main
if __name__ == "__main__":
    print("Generating branches dataset...")
    branches = generate_branches()
    dirty_branches = inject_dirty_data(branches)
    dirty_branches.to_csv('real_branches_data.csv', index=False)
    print(f"Done. Shape: {dirty_branches.shape}")
    print(dirty_branches.head())
