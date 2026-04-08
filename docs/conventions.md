# Conventions

Naming, SQL style, and review expectations for this repo.

## File naming

- SQL files: `snake_case.sql` — matches the target table name
- Metadata: `snake_case.meta.yml` — same stem as the SQL file
- Snippets: `snake_case.sql` — descriptive verb or noun

## SQL style

Follow the same conventions as the dbt repo:

- **Lowercase keywords**: `select`, `from`, `where` (or UPPERCASE — pick one per file, be consistent)
- **CTEs over subqueries**: use `WITH` blocks, name each CTE clearly
- **Final CTE**: always end with a `final` CTE and `SELECT * FROM final`
- **Trailing commas**: use trailing commas in column lists
- **No `SELECT *` from source**: explicitly list columns from source tables
- **Alias all joins**: `FROM orders o JOIN customers c ON ...`

### CTE naming conventions

```sql
WITH
  -- source CTEs: named after the table
  orders AS ( ... ),

  -- logic CTEs: named after what they compute
  daily_totals AS ( ... ),

  -- final CTE: always called "final"
  final AS ( ... )

SELECT * FROM final
```

## Column naming

- `snake_case` for all columns
- `id` for primary keys, `_id` suffix for foreign keys
- `_at` suffix for timestamps (`created_at`, `updated_at`)
- `_date` suffix for date-only columns
- `is_` prefix for booleans (`is_active`, `is_churned`)
- `_count` suffix for counts, `_amount` for money, `_rate` for ratios

## Metadata conventions

- `display_name`: Title Case, human-readable
- `description`: one to two sentences explaining what and who
- `tags`: always include at least one scheduling tag (`daily`/`hourly`)
- `table_name`: must match the SQL file stem

## PR review checklist

Before approving a transform PR, verify:

- [ ] SQL runs without errors in Metabase SQL editor
- [ ] Row counts are reasonable (not 0, not unexpectedly huge)
- [ ] `.meta.yml` has a meaningful `description`
- [ ] Tags are appropriate for the refresh cadence needed
- [ ] No hardcoded IDs or dates (use `CURRENT_DATE` etc.)
- [ ] Column names follow conventions
- [ ] `make build` has been run and `_sync/` is committed
- [ ] If incremental, `checkpoint_column` is tested

## Domain ownership

Each domain folder has a team owner responsible for reviewing PRs:

| Domain | Owner | Slack channel |
|---|---|---|
| `github`, `infrastructure`, `linear` | Engineering | #data-engineering |
| `revenue`, `salesforce`, `stripe` | Revenue ops | #data-revenue |
| `campaign`, `product`, `product_events` | Growth | #data-product |
| `success`, `discourse`, `pylon` | Customer Success | #data-success |
