# Development workflow

This guide covers the day-to-day loop of building and deploying transforms.

## The big picture

```
  You (editor)                 GitHub                    Metabase
  ───────────                  ──────                    ────────
  edit SQL        ──push──▶    branch                    
                               │                          
                               PR review                  
                               │                          
                               merge to main              
                               │                          
                              ─┘                    ◀── Remote Sync pulls
                                                        transforms run on schedule
```

Metabase's **Remote Sync** watches this repo. When changes land on `main`,
the production Metabase (read-only mode) pulls the new YAML and updates
its transforms. Dev instances in read-write mode can work on feature branches.

## Daily loop

### 1. Create a branch

```bash
git checkout -b transforms/add-churn-model
```

### 2. Add or edit a transform

**New transform:**

```bash
make new domain=revenue name=monthly_churn
# Creates transforms/revenue/monthly_churn.sql
#         transforms/revenue/monthly_churn.meta.yml
```

**Existing transform:** just edit the `.sql` file directly.

### 3. Test in Metabase

Before committing, test your SQL in Metabase's SQL editor:

1. Open the dev Metabase instance
2. Go to **+ New → SQL query**
3. Paste your SQL and run it
4. Verify the results look correct
5. Check row counts and edge cases

### 4. Build the sync YAML

```bash
make build
```

This regenerates `_sync/` from your SQL + metadata files.

### 5. Commit and push

```bash
git add .
git commit -m "Add monthly churn transform"
git push origin transforms/add-churn-model
```

### 6. Open a PR

The CI workflow will:
- Check that every `.sql` has a companion `.meta.yml`
- Verify `_sync/` is up to date
- Lint for trailing whitespace

### 7. Review and merge

Once approved, merge to `main`. The production Metabase will pick up
changes on its next sync cycle (typically within minutes).

## Editing from Metabase's UI

You can also create or edit transforms directly in Metabase when connected
in read-write mode:

1. Go to **Data Studio → Transforms → + New**
2. Write your SQL transform
3. Save it — Metabase pushes the YAML to your current branch
4. Pull the branch locally to see the changes

If you edit from the UI, pull the changes and run `make build` to ensure
the SQL source files stay in sync. The YAML is the source of truth when
editing from Metabase; the SQL files are the source of truth when editing
from your editor.

## Branching strategy

| Branch | Purpose | Metabase mode |
|---|---|---|
| `main` | Production transforms | Read-only |
| `dev/*` | Shared development | Read-write |
| `transforms/*` | Feature branches | Read-write (optional) |

## Resolving conflicts

If both the editor and Metabase UI have modified the same transform:

1. Pull the latest from the branch
2. The YAML in `_sync/` will have Metabase's version
3. Update your SQL source file to match (or merge manually)
4. Run `make build` to regenerate
5. Commit the resolved version
