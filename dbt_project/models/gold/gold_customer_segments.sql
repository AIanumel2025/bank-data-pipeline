{{ config(
    materialized='table'
) }}

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
from {{ source('fintechflow_silver', 'customers') }}
group by
risk_rating,
employment_status,
city
order by
risk_rating,
employment_status,
total_customers desc
