{{ config(
    materialized='table'
) }}

select
loan_type,
loan_status,
default_flag,
count(loan_id) as total_loans,
round(avg(principal_amount), 2) as avg_principal,
round(avg(interest_rate), 2)  as avg_interest_rate,
round(avg(monthly_payment), 2) as avg_monthly_payment,
round(sum(balance), 2) as total_remaining_balance,
round(avg(term_months), 2) as avg_term_months
from {{ source('fintechflow_silver', 'loans') }}
group by
loan_type,
loan_status,
default_flag
order by
loan_type,
total_loans desc
