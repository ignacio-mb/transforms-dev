-- Cloud Instance Health
--
-- Operational health metrics per cloud-hosted Metabase instance.
-- Tracks uptime, error rates, and resource utilization.

WITH metrics AS (
  SELECT
    instance_id,
    date,
    avg_response_time_ms,
    p99_response_time_ms,
    error_rate,
    request_count,
    cpu_utilization_pct,
    memory_utilization_pct,
    db_connection_pool_usage_pct
  FROM staging.cloud_instance_metrics
  WHERE date >= CURRENT_DATE - INTERVAL '30 days'
),

incidents AS (
  SELECT
    instance_id,
    count(*) AS incidents_30d,
    max(severity) AS worst_severity
  FROM staging.cloud_incidents
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY 1
),

final AS (
  SELECT
    m.instance_id,
    m.date,
    m.avg_response_time_ms,
    m.p99_response_time_ms,
    m.error_rate,
    m.request_count,
    m.cpu_utilization_pct,
    m.memory_utilization_pct,
    m.db_connection_pool_usage_pct,
    COALESCE(i.incidents_30d, 0) AS incidents_30d,
    i.worst_severity,
    CASE
      WHEN m.error_rate > 0.05 THEN 'degraded'
      WHEN m.p99_response_time_ms > 5000 THEN 'slow'
      WHEN m.cpu_utilization_pct > 90 THEN 'resource_constrained'
      ELSE 'healthy'
    END AS health_status
  FROM metrics m
  LEFT JOIN incidents i ON m.instance_id = i.instance_id
)

SELECT * FROM final
