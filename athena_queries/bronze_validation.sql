-- Bronze Layer Validation Queries
-- Run these queries in AWS Athena after the Glue crawler
-- has registered all four raw tables in the fintechflow database.
-- Purpose: confirm raw data landed correctly before cleaning.

-- 1. Row Counts

select count(*) as total_branches
from fintechflow.branches;

select count(*) as total_customers
from fintechflow.customers;

select count(*) as total_transactions
from fintechflow.transactions;

select count(*) as total_loans
from fintechflow.loans;

-- 2. Spot Check Raw Data

select *
from fintechflow.branches
limit 10;

select *
from fintechflow.customers
limit 10;

select *
from fintechflow.transactions
limit 10;

select *
from fintechflow.loans
limit 10;

-- 3. Confirm Dirty Data Injection Worked

-- Missing no_of_staff in branches
select no_of_staff
from fintechflow.branches
where no_of_staff is null
limit 5;

-- Inconsistent branch_type values including dirty variants
select branch_type, count(*) as count
from fintechflow.branches
group by branch_type
order by count desc;

-- Invalid postcodes present in branches
select post_code, count(*) as count
from fintechflow.branches
group by post_code
order by count desc
limit 20;

-- Distinct payment channels including dirty variants
select distinct payment_channel, count(*) as count
from fintechflow.transactions
group by payment_channel
order by count desc;

-- Missing values in transactions
select
    count(*) as total_rows,
    count(customer_id) as non_null_customer_id,
    count(*) - count(customer_id) as null_customer_id,
    count(*) - count(account_number) as null_account_number,
    count(*) - count(branch_id) as null_branch_id
from fintechflow.transactions;

-- Invalid interest rates in loans
select interest_rate, count(*) as count
from fintechflow.loans
where interest_rate < 0.03 or interest_rate > 0.30
group by interest_rate
order by count desc;
