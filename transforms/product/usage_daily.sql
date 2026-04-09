-- Usage Daily
--
-- Daily product usage aggregates per customer.
-- The most granular usage model — everything else rolls up from here.

SELECT
  pe.event_date AS day,
  pe.customer_id,
  c.company,
  c.plan,
  pe.event_name,
  sum(pe.event_count) AS event_count,
  count(DISTINCT pe.user_email) AS unique_users
FROM raw.product_events pe
JOIN raw.customers c ON pe.customer_id = c.id
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1 DESC, event_count DESC
