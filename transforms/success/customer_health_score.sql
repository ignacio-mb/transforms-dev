-- Customer Health Score
--
-- Composite health score per customer combining product usage,
-- support interactions, and billing signals.

WITH usage AS (
  SELECT
    organization_id,
    count(DISTINCT user_id) AS active_users_30d,
    count(*) AS total_queries_30d,
    max(last_active_at) AS last_active_at
  FROM product.instance_activity
  WHERE activity_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY 1
),

support AS (
  SELECT
    organization_id,
    count(*) AS tickets_90d,
    count(*) FILTER (WHERE severity = 'critical') AS critical_tickets_90d,
    avg(first_response_hours) AS avg_response_hours
  FROM pylon.support_tickets
  WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY 1
),

billing AS (
  SELECT
    ms_organization_id AS organization_id,
    max(arr) AS current_arr,
    bool_or(is_auto_renewal) AS is_auto_renewal
  FROM revenue.monthly_revenue
  WHERE recognized_at = date_trunc('month', CURRENT_DATE)
  GROUP BY 1
),

final AS (
  SELECT
    COALESCE(u.organization_id, s.organization_id, b.organization_id) AS organization_id,
    u.active_users_30d,
    u.total_queries_30d,
    u.last_active_at,
    s.tickets_90d,
    s.critical_tickets_90d,
    b.current_arr,
    b.is_auto_renewal,
    -- Simple health score: higher is better
    CASE
      WHEN u.last_active_at < CURRENT_DATE - INTERVAL '14 days' THEN 'red'
      WHEN s.critical_tickets_90d > 2 THEN 'red'
      WHEN u.active_users_30d < 3 THEN 'yellow'
      WHEN s.tickets_90d > 10 THEN 'yellow'
      ELSE 'green'
    END AS health_status,
    CURRENT_DATE AS scored_at
  FROM usage u
  FULL JOIN support s USING (organization_id)
  FULL JOIN billing b USING (organization_id)
)

SELECT * FROM final
