# Adding a transform

Step-by-step guide to creating a new transform in this repo.

## 1. Decide on the domain

Pick the domain folder that matches the data source or team that owns it.
Available domains (mapped from the dbt repo):

| Domain | Schema | Metabase folder | Team |
|---|---|---|---|
| `github` | `github` | Engineering | Engineering |
| `revenue` | `revenue` | Revenue | Finance |
| `salesforce` | `salesforce` | Revenue | Revenue ops |
| `campaign` | `campaign` | Marketing & Growth | Marketing |
| `product` | `product` | Product | Product |
| `success` | `success` | Success Engineering | CS |
| `discourse` | `discourse` | Success Engineering | CS |
| `pylon` | `pylon` | Success Engineering | CS |
| `infrastructure` | `infrastructure` | Engineering | Infra |
| `stripe` | `stripe` | Operations | Finance |

Need a new domain? Add it to `transforms.yml` under `domains:`.

## 2. Scaffold the files

```bash
make new domain=revenue name=monthly_churn
```

This creates two files:
- `transforms/revenue/monthly_churn.sql` — your SQL query
- `transforms/revenue/monthly_churn.meta.yml` — transform metadata

## 3. Write the SQL

Open the `.sql` file and write a `SELECT` query. Key differences from dbt:

| dbt | Transforms |
|---|---|
| `{{ ref('other_model') }}` | `schema.table_name` (direct reference) |
| `{{ source('raw', 'table') }}` | `raw_schema.table_name` |
| `{{ config(materialized='table') }}` | Not needed — all transforms materialize |
| Jinja `{% if %}` | Not available — use SQL `CASE` or snippets |
| `{{ dbt_utils.generate_surrogate_key() }}` | `md5(col1::text \|\| col2::text)` |
| `{{ datediff('a', 'b', 'day') }}` | `EXTRACT(EPOCH FROM (b - a)) / 86400` |

### Referencing other transforms

Since transforms write persistent tables, reference them by their
target schema and table name:

```sql
-- In dbt:         {{ ref('monthly_revenue') }}
-- In transforms:  revenue.monthly_revenue
SELECT * FROM revenue.monthly_revenue
```

### Using snippets

Snippets are reusable SQL fragments. Reference them with Metabase's syntax:

```sql
SELECT
  email,
  {{ snippet: normalize_email }} AS email_domain
FROM users
```

## 4. Fill in the metadata

Edit the `.meta.yml` file:

```yaml
display_name: Monthly Churn        # Human-readable name in Metabase
description: >                     # Shows in Data Studio
  Monthly churn rate by plan type.

table_name: monthly_churn          # Target table in the database
                                   # Schema comes from transforms.yml

tags:                              # Tags for scheduling via Jobs
  - daily
  - revenue

incremental: false                 # Set true for append-only transforms
```

### Tags and scheduling

Tags group transforms into **Jobs** in Metabase. Common tags:

- `daily` — runs every morning
- `hourly` — runs every hour
- `critical` — higher priority, alerting if failed
- Domain tags (`revenue`, `engineering`, etc.) for filtering

## 5. Build and test

```bash
# Generate serialization YAML
make build

# Test the SQL in Metabase's SQL editor
# Copy-paste your SQL and run it to verify results
```

## 6. Commit

```bash
git add transforms/revenue/monthly_churn.sql
git add transforms/revenue/monthly_churn.meta.yml
git add _sync/transforms/monthly_churn.yml
git commit -m "Add monthly churn transform"
```

## 7. Entity IDs

On first build, the script auto-generates a deterministic entity ID.
Once the transform exists in Metabase, you can pin the entity ID in the
`.meta.yml` to prevent any future ID drift:

```yaml
entity_id: aBcDeFgHiJkLmNoPqRsT_
```

Copy it from Metabase: open the transform → Info → Entity ID.
