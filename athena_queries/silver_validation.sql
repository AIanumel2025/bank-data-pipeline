-- Silver Layer Validation Queries
-- Run these queries in AWS Athena after the silver Glue ETL jobs
-- have completed and the silver crawler has registered all tables.
-- Purpose: confirm cleaning decisions were applied correctly.

-- 1. Row Counts Post-Cleaning

select count(*) as total_branches
from finflow_silver.branches;

select count(*) as total_customers
from finflow_silver.customers;

select count(*) as total_transactions
from finflow_silver.transactions;

select count(*) as total_loans
from finflow_silver.loans;

-- 2. Confirm Branch Cleaning

-- branch_type should now only contain clean values
select branch_type, count(*) as count
from finflow_silver.branches
group by branch_type
order by count desc;

-- no_of_staff should have no nulls (filled with median)
select count(*) as null_staff_count
from finflow_silver.branches
where no_of_staff is null;

-- branch_manager should have no leading whitespace
select branch_manager
from finflow_silver.branches
where branch_manager like ' %'
limit 5;

-- 3. Confirm Customer Cleaning

-- gender should only contain Male, Female, Other
select gender, count(*) as count
from finflow_silver.customers
group by gender
order by count desc;

-- kyc_status should only contain Verified, Pending
select kyc_status, count(*) as count
from finflow_silver.customers
group by kyc_status
order by count desc;

-- annual_income should have no nulls (filled with median)
select count(*) as null_income_count
from finflow_silver.customers
where annual_income is null;

-- 4. Confirm Transaction Cleaning

-- payment_channel should only contain clean canonical values
select payment_channel, count(*) as count
from finflow_silver.transactions
group by payment_channel
order by count desc;

-- currency should only contain GBP
select currency, count(*) as count
from finflow_silver.transactions
group by currency
order by count desc;

-- negative balances should be gone
select count(*) as negative_balance_count
from finflow_silver.transactions
where balance_after_transaction < 0;

-- orphaned transactions flagged correctly
select orphaned, count(*) as count
from finflow_silver.transactions
group by orphaned;

-- 5. Confirm Loan Cleaning

-- loan_status should only contain clean canonical values
select loan_status, count(*) as count
from finflow_silver.loans
group by loan_status
order by count desc;

-- invalid interest rates should be null
select count(*) as null_rate_count
from finflow_silver.loans
where interest_rate is null;

-- no balance should exceed principal
select count(*) as impossible_balance_count
from finflow_silver.loans
where balance > principal_amount;
