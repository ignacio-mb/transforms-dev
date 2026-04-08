#!/usr/bin/env python3
"""
pull.py — Extract editable SQL + metadata from Metabase Remote Sync YAML.

After Metabase pushes transforms to the repo via Remote Sync,
run this to update your transforms/ source files.

Reads:  collections/<id>_<name>/transforms/<id>_<name>.yaml
Writes: transforms/<domain>/<name>.sql + transforms/<domain>/<name>.meta.yml

Usage:
    python scripts/pull.py              # extract all
    python scripts/pull.py --dry-run    # preview without writing
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
COLLECTIONS_DIR = ROOT / "collections"
TRANSFORMS_DIR = ROOT / "transforms"
CONFIG_PATH = ROOT / "transforms.yml"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def collection_name_to_domain(collection_name: str, config: dict) -> str:
    """Map a Metabase collection name (e.g. 'Revenue') to a domain folder."""
    for domain, dcfg in config.get("domains", {}).items():
        if dcfg.get("folder", "").lower() == collection_name.lower():
            return domain
    # Fallback: snake_case the collection name
    return collection_name.lower().replace(" ", "_")


def get_collection_name(collection_dir: Path) -> str:
    """Extract the human-readable collection name from the directory name.
    Directory format: <entity_id>_<name>, e.g. 'ax3R21WJwpE2Duf4Ln1Gs_revenue'
    """
    dir_name = collection_dir.name
    # The entity ID is the part before the first underscore that looks like a NanoID
    # But names can have underscores too. Check the collection YAML for the real name.
    collection_yamls = list(collection_dir.glob("*.yaml"))
    # Filter out the transforms subdirectory files
    collection_yamls = [f for f in collection_yamls if f.stem == dir_name]
    if collection_yamls:
        with open(collection_yamls[0]) as f:
            data = yaml.safe_load(f)
        if data and "name" in data:
            return data["name"]
    # Fallback: strip entity_id prefix
    parts = dir_name.split("_", 1)
    return parts[1] if len(parts) > 1 else dir_name


def extract_transform(yml_path: Path, domain: str, dry_run: bool = False):
    """Extract a single transform YAML into .sql + .meta.yml."""
    with open(yml_path) as f:
        data = yaml.safe_load(f)

    if not data:
        print(f"  SKIP: {yml_path.name} — empty")
        return None

    # Extract SQL
    source = data.get("source", {})
    query = source.get("query", {})
    native = query.get("native", {})
    sql = native.get("query", "")

    if not sql:
        source_type = source.get("type", "unknown")
        print(f"  SKIP: {yml_path.name} — no native SQL (source type: {source_type})")
        return None

    # Extract target info
    target = data.get("target", {})
    table_name = target.get("name", yml_path.stem)

    # Build metadata
    meta = {}
    meta["display_name"] = data.get("name", table_name.replace("_", " ").title())

    desc = data.get("description")
    if desc:
        meta["description"] = desc

    meta["table_name"] = table_name

    target_schema = target.get("schema")
    if target_schema:
        meta["schema"] = target_schema

    tags = data.get("tags", [])
    if tags:
        meta["tags"] = tags

    # Preserve entity_id, collection_id, and timestamps for round-tripping
    if data.get("entity_id"):
        meta["entity_id"] = data["entity_id"]
    if data.get("collection_id"):
        meta["collection_id"] = data["collection_id"]
    if data.get("created_at"):
        meta["created_at"] = data["created_at"]
    if data.get("creator_id"):
        meta["creator_id"] = data["creator_id"]

    # Write files
    domain_dir = TRANSFORMS_DIR / domain
    sql_path = domain_dir / f"{table_name}.sql"
    meta_path = domain_dir / f"{table_name}.meta.yml"

    if dry_run:
        status = "UPDATE" if sql_path.exists() else "CREATE"
        print(f"  {status}: transforms/{domain}/{table_name}.sql")
        print(f"  {status}: transforms/{domain}/{table_name}.meta.yml")
        return table_name

    domain_dir.mkdir(parents=True, exist_ok=True)

    with open(sql_path, "w") as f:
        f.write(sql.rstrip() + "\n")

    with open(meta_path, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    status = "updated" if sql_path.exists() else "created"
    print(f"  {status}: transforms/{domain}/{table_name}.sql")
    return table_name


def main():
    parser = argparse.ArgumentParser(description="Extract SQL from Metabase Remote Sync YAML")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    config = load_config()

    if not COLLECTIONS_DIR.exists():
        print("No collections/ directory found.")
        print("Connect Remote Sync, push changes from Metabase, then git pull.")
        sys.exit(1)

    extracted = 0

    for collection_dir in sorted(COLLECTIONS_DIR.iterdir()):
        if not collection_dir.is_dir():
            continue

        transforms_dir = collection_dir / "transforms"
        if not transforms_dir.exists():
            continue

        collection_name = get_collection_name(collection_dir)
        domain = collection_name_to_domain(collection_name, config)

        print(f"\n  {collection_name} → transforms/{domain}/")

        for yml_path in sorted(transforms_dir.glob("*.yaml")):
            result = extract_transform(yml_path, domain, dry_run=args.dry_run)
            if result:
                extracted += 1

    action = "Would extract" if args.dry_run else "Extracted"
    print(f"\n  {action} {extracted} transform(s)\n")


if __name__ == "__main__":
    main()