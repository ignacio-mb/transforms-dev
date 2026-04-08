-- Support Weekly
--
-- Weekly support metrics: volume, response times, SLA rates by severity.
-- Designed for the weekly support team review.

WITH tickets AS (
  SELECT
    date_trunc('week', t.created_at)::date AS week,
    t.severity,
    t.channel,
    c.plan,
    count(*) AS ticket_count,
    count(*) FILTER (WHERE t.status IN ('resolved', 'closed')) AS resolved_count,
    round(avg(
      EXTRACT(EPOCH FROM (t.first_reply_at - t.created_at)) / 3600
    ) FILTER (WHERE t.first_reply_at IS NOT NULL), 1) AS avg_hours_to_reply,
    round(avg(
      EXTRACT(EPOCH FROM (t.resolved_at - t.created_at)) / 3600
    ) FILTER (WHERE t.resolved_at IS NOT NULL), 1) AS avg_hours_to_resolve,
    count(DISTINCT t.customer_id) AS unique_customers
  FROM raw.support_tickets t
  JOIN raw.customers c ON t.customer_id = c.id
  GROUP BY 1, 2, 3, 4
)

SELECT
  week,
  severity,
  channel,
  plan,
  ticket_count,
  resolved_count,
  ticket_count - resolved_count AS still_open,
  avg_hours_to_reply,
  avg_hours_to_resolve,
  unique_customers,
  CASE
    WHEN ticket_count > 0
    THEN round(resolved_count::numeric / ticket_count, 2)
    ELSE 0
  END AS resolution_rate
FROM tickets
ORDER BY week DESC, ticket_count DESC
