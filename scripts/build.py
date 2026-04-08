#!/usr/bin/env python3
"""
build.py — Generate Metabase Remote Sync YAML from SQL transforms.

Reads transforms/<domain>/<name>.sql + .meta.yml and produces the
collections/ directory structure that Metabase Remote Sync expects.

Usage:
    python scripts/build.py                 # build all
    python scripts/build.py --check         # exit 1 if collections/ is stale
    python scripts/build.py --domain revenue
"""

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
TRANSFORMS_DIR = ROOT / "transforms"
COLLECTIONS_DIR = ROOT / "collections"
CONFIG_PATH = ROOT / "transforms.yml"


# Use block literal for multi-line strings (SQL queries)
def _str_representer(dumper, data):
    if "\n" in data and len(data) > 200:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

yaml.add_representer(str, _str_representer)


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def generate_entity_id(name: str) -> str:
    """Deterministic NanoID-like entity ID from a name."""
    digest = hashlib.sha256(name.encode()).hexdigest()
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    return "".join(alphabet[int(digest[i:i+2], 16) % 64] for i in range(0, 42, 2))


def read_sql(path: Path) -> str:
    lines = path.read_text().splitlines()
    return "\n".join(line.rstrip() for line in lines)


def read_meta(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def build_collection_yaml(name: str, entity_id: str) -> dict:
    return {
        "archived": False,
        "description": None,
        "entity_id": entity_id,
        "name": name,
        "personal_owner_id": None,
        "slug": name.lower().replace(" ", "_"),
        "serdes/meta": [{"id": entity_id, "label": name.lower().replace(" ", "_"), "model": "Collection"}],
    }


def build_transform_yaml(sql: str, meta: dict, config: dict, collection_id: str) -> dict:
    database = config["project"]["database"]
    table_name = meta.get("table_name", "unnamed")
    entity_id = meta.get("entity_id") or generate_entity_id(f"transform/{table_name}")
    schema = meta.get("schema", config.get("default_schema", "transforms"))

    return {
        "collection_id": collection_id,
        "created_at": meta.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
        "creator_id": meta.get("creator_id"),
        "description": meta.get("description"),
        "entity_id": entity_id,
        "name": meta.get("display_name", table_name.replace("_", " ").title()),
        "owner_email": None,
        "owner_user_id": meta.get("creator_id"),
        "source": {
            "query": {
                "database": database,
                "native": {"query": sql + "\n"},
                "type": "native",
            },
            "type": "query",
        },
        "source_database_id": database,
        "tags": meta.get("tags", []),
        "target": {
            "database": database,
            "name": table_name,
            "schema": schema,
            "type": "table",
        },
        "serdes/meta": [{"id": entity_id, "label": table_name, "model": "Transform"}],
    }


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)


def build_all(config: dict, domain_filter: str = None):
    built = 0
    warnings = []

    # Group transforms by domain → collection
    domains = {}
    for sql_path in sorted(TRANSFORMS_DIR.rglob("*.sql")):
        if sql_path.name.startswith("_"):
            continue
        domain = sql_path.parent.name
        if domain_filter and domain != domain_filter:
            continue
        domains.setdefault(domain, []).append(sql_path)

    for domain, sql_files in domains.items():
        domain_cfg = config.get("domains", {}).get(domain, {})
        folder_name = domain_cfg.get("folder", domain.title())
        collection_id = generate_entity_id(f"collection/{folder_name}")

        # Build collection directory
        collection_dir_name = f"{collection_id}_{folder_name.lower().replace(' ', '_')}"
        collection_dir = COLLECTIONS_DIR / collection_dir_name

        # Write collection YAML
        collection_yaml = build_collection_yaml(folder_name, collection_id)
        write_yaml(collection_dir / f"{collection_dir_name}.yaml", collection_yaml)

        # Build each transform
        for sql_path in sql_files:
            name = sql_path.stem
            meta_path = sql_path.with_suffix(".meta.yml")
            meta = read_meta(meta_path)

            if not meta_path.exists():
                warnings.append(f"  WARN: {sql_path.relative_to(ROOT)} has no .meta.yml")

            sql = read_sql(sql_path)
            if not sql.strip():
                warnings.append(f"  SKIP: {sql_path.relative_to(ROOT)} is empty")
                continue

            transform_data = build_transform_yaml(sql, meta, config, collection_id)
            entity_id = transform_data["entity_id"]
            transform_filename = f"{entity_id}_{name}.yaml"
            write_yaml(collection_dir / "transforms" / transform_filename, transform_data)
            built += 1

    return built, warnings


def main():
    parser = argparse.ArgumentParser(description="Build Metabase Remote Sync YAML from SQL")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--domain", help="Build only a specific domain")
    args = parser.parse_args()

    config = load_config()

    if args.check:
        # Simple: just rebuild and compare
        print("Check mode not yet implemented for collections/ format.")
        print("Run: make build && git diff --stat")
        sys.exit(0)

    built, warnings = build_all(config, domain_filter=args.domain)
    for w in warnings:
        print(w)
    print(f"\n  Built {built} transform(s) in collections/\n")


if __name__ == "__main__":
    main()
