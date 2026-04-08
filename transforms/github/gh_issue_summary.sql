-- GitHub Issue Summary
--
-- Aggregated view of GitHub issues with team assignments, customer impact,
-- and triage status. Replaces the dbt gh_issue model.
--
-- Source tables: staging.github_issues, github.gh_issue_customer_mention,
--               staging.github_issue_label_history

WITH issue AS (
  SELECT * FROM staging.github_issues
),

customer_mention AS (
  SELECT * FROM github.gh_issue_customer_mention
),

agg_customer_mention AS (
  SELECT
    issue_number,
    count(DISTINCT pylon_organization_id) AS customer_upvotes,
    min(ticket_severity) AS customer_severity
  FROM customer_mention
  GROUP BY 1
),

issue_team_label_status AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY github_issue_id, label
      ORDER BY updated_at DESC
    ) AS status_rank
  FROM staging.github_issue_label_history
  WHERE label ~* 'Team/'
    AND label !~* 'deprecated'
),

issue_team AS (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY github_issue_id
      ORDER BY updated_at, label
    ) AS rank
  FROM issue_team_label_status
  WHERE status_rank = 1
    AND action = 'added'
),

final AS (
  SELECT
    i.id,
    i.created_at,
    i.updated_at,
    i.closed_at,
    i.repository,
    i.user_login,
    i.milestone,
    i.number,
    i.state,
    i.state_reason,
    i.type,
    i.priority,
    m.customer_severity,
    i.escalation_status,
    i.feature_cluster,
    i.feature,
    i.is_pull_request,
    i.is_bug,
    i.is_feature_request,
    i.title,
    i.comments,
    i.upvotes,
    i.recent_upvotes,
    COALESCE(m.customer_upvotes, 0) AS customer_upvotes,
    t.label AS team_label,
    i.user_id,
    i.milestone_id
  FROM issue i
  LEFT JOIN agg_customer_mention m ON i.number = m.issue_number
  LEFT JOIN issue_team t ON i.id = t.github_issue_id AND t.rank = 1
)

SELECT * FROM final
