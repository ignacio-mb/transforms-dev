# transforms-dev

Data transforms for Metabase, version-controlled and synced via [Remote Sync](https://www.metabase.com/docs/latest/installation-and-operation/remote-sync).

This repo replaces dbt for internal data modeling at Metabase. Instead of dbt's `ref()` + scheduler, we use **Metabase Transforms** — SQL queries that write results back to the database as persistent tables, editable from Metabase's UI or from this repo.

## How it works

```
┌──────────────────┐       git push        ┌──────────────────┐
│                  │ ───────────────────▶   │                  │
│  Your editor     │                        │  GitHub repo     │
│  (VS Code, etc)  │   ◀───────────────    │  (this repo)     │
│                  │       git pull         │                  │
└──────────────────┘                        └────────┬─────────┘
                                                     │
                                              Remote Sync
                                                     │
                                            ┌────────▼─────────┐
                                            │                  │
                                            │  Metabase (dev)  │
                                            │  Read-write mode │
                                            │                  │
                                            └────────┬─────────┘
                                                     │
                                                PR + merge
                                                     │
                                            ┌────────▼─────────┐
                                            │                  │
                                            │  Metabase (prod) │
                                            │  Read-only mode  │
                                            │                  │
                                            └──────────────────┘
```

**The loop:** edit SQL → run `make build` → commit → Metabase picks it up via Remote Sync. Or edit in Metabase's UI → Metabase pushes YAML to a branch → you pull.

## Quick start

```bash
# Clone and set up
git clone git@github.com:metabase/transforms-models.git
cd transforms-models
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml

# Create a new transform
cp transforms/_template.sql transforms/revenue/my_new_transform.sql
cp transforms/_template.meta.yml transforms/revenue/my_new_transform.meta.yml

# Edit SQL and metadata
$EDITOR transforms/revenue/my_new_transform.sql
$EDITOR transforms/revenue/my_new_transform.meta.yml

# Build serialization YAML
make build

# Commit and push
git add . && git commit -m "Add my_new_transform" && git push
```

## Repo structure

```
transforms-models/
├── transforms/                     # ← you edit these
│   ├── _template.sql               #   SQL template for new transforms
│   ├── _template.meta.yml          #   metadata template
│   ├── github/                     #   domain folders (mirror dbt structure)
│   │   ├── gh_issue_summary.sql
│   │   └── gh_issue_summary.meta.yml
│   ├── revenue/
│   ├── salesforce/
│   └── ...
├── snippets/                       # reusable SQL fragments (Metabase snippets)
│   └── normalize_email.sql
├── _sync/                          # ← generated, do not edit by hand
│   └── transforms/                 #   Metabase serialization YAML
│       └── gh_issue_summary.yml
├── scripts/
│   └── build.py                    # generates _sync/ from transforms/
├── docs/
│   ├── workflow.md
│   ├── adding-a-transform.md
│   └── conventions.md
├── Makefile
└── transforms.yml                  # project config (database name, schemas)
```

## Key concepts

| dbt concept | Metabase Transforms equivalent |
|---|---|
| `models/domain/model.sql` | `transforms/domain/transform.sql` |
| `schema.yml` | `.meta.yml` per transform |
| `{{ ref('other_model') }}` | Direct table reference or `{{ #snippet }}` |
| `dbt run` | Transform runs on schedule in Metabase |
| `dbt build` | `make build` (generates serialization YAML) |
| Materializations (table/view) | All transforms are materialized tables |
| Seeds | CSV upload in Metabase |
| Macros | Snippets (with variables) |

## Environments

| Instance | Mode | Branch | Purpose |
|---|---|---|---|
| `dev.metabase.internal` | Read-write | `dev/*`, feature branches | Build + test transforms |
| `prod.metabase.internal` | Read-only | `main` | Production analytics |

## Prerequisites

- Metabase Pro/Enterprise with Transforms add-on
- Remote Sync enabled and connected to this repo
- Transform sync toggled on in Admin → Remote Sync
- Database user with write privileges (for transform execution)
- Python 3.9+ (for the build script)

## Documentation

- [Workflow guide](docs/workflow.md) — day-to-day development loop
- [Adding a transform](docs/adding-a-transform.md) — step-by-step guide
- [Conventions](docs/conventions.md) — naming, SQL style, review checklist
