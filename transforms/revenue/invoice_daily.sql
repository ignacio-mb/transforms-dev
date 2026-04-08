-- Invoice Daily
--
-- One row per day with invoice counts and amounts by status.
-- Lightweight incremental transform for real-time revenue monitoring.

SELECT
  i.issued_at::date AS day,
  c.plan,
  i.status,
  count(*) AS invoice_count,
  sum(i.amount) AS total_amount,
  avg(i.amount) AS avg_amount,
  count(DISTINCT i.customer_id) AS unique_customers
FROM raw.invoices i
JOIN raw.customers c ON i.customer_id = c.id
GROUP BY 1, 2, 3
ORDER BY 1 DESC
