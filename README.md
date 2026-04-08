# transforms-dev

Data transforms for Metabase, version-controlled and synced via [Remote Sync](https://www.metabase.com/docs/latest/installation-and-operation/remote-sync).

This repo replaces dbt for internal data modeling at Metabase. Instead of dbt's `ref()` + scheduler, we use **Metabase Transforms** — SQL queries that write results back to the database as persistent tables, editable from Metabase's UI or from this repo.

## How it works

```
┌──────────────────┐       git push         ┌──────────────────┐
│                  │ ───────────────────▶   │                  │
│  Code editor     │                        │  GitHub repo     │
|                  │   ◀───────────────     │  (this repo)     │
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

## Scripts

| Script | Direction | What it does |
|---|---|---|
| `make pull` | Metabase → SQL | Reads the YAML in `collections/` (written by Metabase via Remote Sync) and extracts each transform into an editable `.sql` file and a `.meta.yml` file in `transforms/<domain>/`. Run after `git pull`. |
| `make build` | SQL → Metabase | Reads your `.sql` + `.meta.yml` source files in `transforms/` and assembles them back into the `collections/` YAML structure that Remote Sync expects. Run after editing SQL, before you commit. |
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

## Environments

| Instance | Mode | Branch | Purpose |
|---|---|---|---|
| `dev.metabase.internal` | Read-write | `dev/*`, feature branches | Build + test transforms |
| `prod.metabase.internal` | Read-only | `main` | Production analytics |
