-- Gold Layer Analytics Queries
-- Run these queries in AWS Athena against the gold layer tables
-- produced by dbt. These answer the core business questions
-- the pipeline was built to address.

-- 1. Branch Performance

-- Which branches have the highest transaction volumes?
select
b.branch_name,
b.branch_id,
b.branch_city,
b.branch_type,
b.opening_date,
count(t.transaction_id) as total_transactions,
count(distinct t.customer_id) as unique_customers,
round(sum(t.balance_after_transaction), 2) as total_value,
round(avg(t.balance_after_transaction), 2) as avg_transaction_value,
count(case when t.payment_channel = 'ATM Withdrawal' then 1 end) as atm_count,
count(case when t.payment_channel = 'Digital Wallet (Apple/Google Pay)' then 1 end) as digital_wallet_count,
count(case when t.payment_channel = 'Faster Payments (FPS)' or t.payment_channel = 'Open Banking / Pay-by-Bank' or t.payment_channel = 'Bacs Direct Credit' or t.payment_channel = 'Bacs Direct Debit' then 1 end) as online_count,
count(case when t.payment_channel = 'Debit Card (Chip & PIN)' or t.payment_channel = 'Debit Card (Contactless)' or t.payment_channel = 'Credit Card' then 1 end) as card_count,
count(case when t.payment_channel = 'CHAPS' then 1 end) as chaps_count,
count(case when t.payment_channel = 'Standing Order' then 1 end) as standing_order_count,
count(case when t.payment_channel = 'Cheque' then 1 end) as cheque_count,
count(case when t.transaction_status = 'Completed' then 1 end) as completed_count,
count(case when t.transaction_status = 'Failed' then 1 end) as failed_count
from "finflow_silver"."transactions" t
join "finflow_silver"."branches" b on t.branch_id = b.branch_id
group by b.branch_id, b.branch_name, b.branch_city, b.branch_type, b.opening_date
order by total_transactions desc
limit 10;

-- Which cities process the most transactions?
select
b.branch_city,
count(t.transaction_id) as total_transactions,
round(sum(t.balance_after_transaction), 2) as total_value
from "finflow_silver"."transactions" t
join "finflow_silver"."branches" b on t.branch_id = b.branch_id
group by b.branch_city
order by total_transactions desc;

-- What is the payment channel distribution across all branches?
select
payment_channel,
count(*) as transaction_count,
round(count(*) * 100.0 / sum(count(*)) over(), 2) as pct_of_total
from "finflow_silver"."transactions"
group by payment_channel
order by transaction_count desc;

-- 2. Customer Segments

-- How do customers break down by risk rating and employment status?
select
risk_rating,
employment_status,
city,
count(cust_id) as total_customers,
round(avg(annual_income), 2) as avg_annual_income,
round(min(annual_income), 2) as min_annual_income,
round(max(annual_income), 2) as max_annual_income,
count(case when kyc_status = 'Verified' then 1 end) as verified_count,
count(case when kyc_status = 'Pending' then 1 end) as pending_count,
count(case when gender = 'Male' then 1 end) as male_count,
count(case when gender = 'Female' then 1 end) as female_count
from "finflow_silver"."customers"
group by risk_rating, employment_status, city
order by risk_rating, employment_status, total_customers desc;

-- 3. Loan Performance

-- How do loans perform by type, status and default flag?
select
loan_type,
loan_status,
default_flag,
count(loan_id) as total_loans,
round(avg(principal_amount), 2) as avg_principal,
round(avg(interest_rate), 4) as avg_interest_rate,
round(avg(monthly_payment), 2) as avg_monthly_payment,
round(sum(balance), 2) as total_remaining_balance,
round(avg(term_months), 0) as avg_term_months
from "finflow_silver"."loans"
group by loan_type, loan_status, default_flag
order by loan_type, total_loans desc;

-- What is the default rate per loan type?
select
loan_type,
count(*) as total_loans,
count(case when default_flag = 'True' then 1 end) as defaulted_loans,
round(count(case when default_flag = 'True' then 1 end) * 100.0 / count(*), 2) as default_rate_pct
from "finflow_silver"."loans"
group by loan_type
order by default_rate_pct desc;
