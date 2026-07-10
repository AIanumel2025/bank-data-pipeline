{{ config(
    materialized='table',
    schema='fintechflow_gold'
) }}

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
from {{ source("fintechflow_silver", "transactions" ) }} t 
join {{ source('fintechflow_silver', 'branches') }} b on t.branch_id = b.branch_id 
group by b.branch_id, b.branch_name, b.branch_city, b.branch_type, b.opening_date 
order by total_transactions desc
