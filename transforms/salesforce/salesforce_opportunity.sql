-- Salesforce Opportunity
--
-- Clean view of Salesforce opportunities with stage history
-- and account enrichment. Used by Revenue team dashboards.

WITH opportunity AS (
  SELECT
    id,
    name,
    account_id,
    owner_id,
    stage_name,
    amount,
    close_date,
    created_date,
    is_won,
    is_closed,
    fiscal_quarter,
    fiscal_year,
    lead_source,
    type,
    probability
  FROM staging.salesforce_opportunities
),

account AS (
  SELECT
    id,
    name AS account_name,
    industry,
    annual_revenue AS account_arr,
    billing_country
  FROM staging.salesforce_accounts
),

final AS (
  SELECT
    o.id,
    o.name,
    o.stage_name,
    o.amount,
    o.close_date,
    o.created_date,
    o.is_won,
    o.is_closed,
    o.probability,
    o.fiscal_quarter,
    o.fiscal_year,
    o.lead_source,
    o.type,
    a.account_name,
    a.industry,
    a.billing_country,
    o.account_id,
    o.owner_id
  FROM opportunity o
  LEFT JOIN account a ON o.account_id = a.id
)

SELECT * FROM final
