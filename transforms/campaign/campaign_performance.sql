-- Campaign Performance
--
-- Unified view of paid and email campaigns with attribution.
-- Combines Google Ads, LinkedIn, and email campaign data.

WITH paid AS (
  SELECT
    campaign_id,
    campaign_name,
    'paid' AS channel,
    platform,
    date,
    impressions,
    clicks,
    spend,
    conversions
  FROM staging.paid_campaigns_daily
),

email AS (
  SELECT
    campaign_id,
    campaign_name,
    'email' AS channel,
    'customer_io' AS platform,
    sent_date AS date,
    recipients AS impressions,
    unique_opens AS clicks,
    0::numeric AS spend,
    unique_clicks AS conversions
  FROM staging.email_campaigns
),

combined AS (
  SELECT * FROM paid
  UNION ALL
  SELECT * FROM email
),

final AS (
  SELECT
    campaign_id,
    campaign_name,
    channel,
    platform,
    date,
    impressions,
    clicks,
    spend,
    conversions,
    CASE WHEN impressions > 0
      THEN round(clicks::numeric / impressions, 4)
      ELSE 0
    END AS click_through_rate,
    CASE WHEN clicks > 0
      THEN round(spend / clicks, 2)
      ELSE 0
    END AS cost_per_click,
    date_trunc('week', date) AS week,
    date_trunc('month', date) AS month
  FROM combined
)

SELECT * FROM final
