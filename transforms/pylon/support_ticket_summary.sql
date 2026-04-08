-- Support Ticket Summary
--
-- Enriched view of Pylon support tickets with customer and account context.
-- Core model for Success Engineering dashboards.

WITH tickets AS (
  SELECT
    id,
    organization_id,
    subject,
    severity,
    status,
    assignee_id,
    created_at,
    resolved_at,
    first_response_at,
    channel
  FROM staging.pylon_tickets
),

orgs AS (
  SELECT
    id AS organization_id,
    name AS organization_name,
    plan_name,
    arr
  FROM salesforce.int_account
  WHERE is_active
),

final AS (
  SELECT
    t.id,
    t.subject,
    t.severity,
    t.status,
    t.channel,
    t.created_at,
    t.resolved_at,
    t.first_response_at,
    EXTRACT(EPOCH FROM (t.first_response_at - t.created_at)) / 3600
      AS hours_to_first_response,
    EXTRACT(EPOCH FROM (t.resolved_at - t.created_at)) / 3600
      AS hours_to_resolution,
    o.organization_name,
    o.plan_name,
    o.arr,
    t.assignee_id,
    t.organization_id,
    date_trunc('week', t.created_at) AS created_week
  FROM tickets t
  LEFT JOIN orgs o USING (organization_id)
)

SELECT * FROM final
