#!/usr/bin/env python3
"""
build.py — Generate Metabase serialization YAML from SQL transforms.

Reads each .sql file + its companion .meta.yml in transforms/,
and produces the YAML that Metabase Remote Sync expects in _sync/.

Usage:
    python scripts/build.py                 # build all
    python scripts/build.py --check         # dry-run, exit 1 if _sync/ is stale
    python scripts/build.py --domain github # build only one domain
"""

import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent


# Custom YAML representer: use block literal style (|) for multi-line strings
# that are long enough to be SQL queries (not short descriptions)
def _str_representer(dumper, data):
    if "\n" in data and len(data) > 200:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_representer)
TRANSFORMS_DIR = ROOT / "transforms"
SNIPPETS_DIR = ROOT / "snippets"
SYNC_DIR = ROOT / "_sync"
CONFIG_PATH = ROOT / "transforms.yml"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def generate_entity_id(name: str) -> str:
    """
    Generate a deterministic NanoID-like entity ID from the transform name.
    This keeps entity IDs stable across builds so Metabase doesn't
    create duplicate entities on each import.
    """
    digest = hashlib.sha256(name.encode()).hexdigest()
    # NanoID alphabet: A-Za-z0-9_-  (64 chars), length 21
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    entity_id = ""
    for i in range(0, 42, 2):
        byte_val = int(digest[i : i + 2], 16)
        entity_id += alphabet[byte_val % len(alphabet)]
    return entity_id


def read_sql(sql_path: Path) -> str:
    """Read SQL file, strip trailing whitespace per line (YAML multi-line compat)."""
    lines = sql_path.read_text().splitlines()
    return "\n".join(line.rstrip() for line in lines)


def read_meta(meta_path: Path) -> dict:
    """Read the companion .meta.yml file."""
    if not meta_path.exists():
        return {}
    with open(meta_path) as f:
        return yaml.safe_load(f) or {}


def build_transform_yaml(
    sql: str, meta: dict, domain: str, name: str, config: dict
) -> dict:
    """
    Build the serialization YAML dict for a single transform.

    This follows the Metabase Card serialization format, which is what
    Remote Sync reads for transforms. Transforms are Cards with
    type=transform and additional transform-specific fields.
    """
    database = config["project"]["database"]
    domain_config = config.get("domains", {}).get(domain, {})
    schema = meta.get("schema", domain_config.get("schema", config.get("default_schema", "transforms")))
    table_name = meta.get("table_name", name)
    folder = meta.get("folder", domain_config.get("folder"))
    entity_id = meta.get("entity_id") or generate_entity_id(f"{domain}/{name}")

    transform = {
        "name": meta.get("display_name", name.replace("_", " ").title()),
        "description": meta.get("description", ""),
        "entity_id": entity_id,
        "type": "transform",
        "query_type": "native",
        "database_id": database,
        "dataset_query": {
            "database": database,
            "type": "native",
            "native": {"query": sql},
        },
        "archived": False,
        "transform": {
            "target_schema": schema,
            "target_table": table_name,
            "incremental": meta.get("incremental", False),
        },
    }

    if meta.get("incremental"):
        transform["transform"]["checkpoint_column"] = meta.get("checkpoint_column", "")

    if meta.get("tags"):
        transform["transform"]["tags"] = meta["tags"]

    if folder:
        transform["folder"] = folder

    # Preserve serdes/meta for round-tripping with Metabase
    transform["serdes/meta"] = [
        {"model": "Transform", "id": entity_id, "label": name}
    ]

    return transform


def build_snippet_yaml(sql_path: Path) -> dict:
    """Build serialization YAML for a Metabase snippet."""
    name = sql_path.stem
    sql = read_sql(sql_path)
    entity_id = generate_entity_id(f"snippet/{name}")

    return {
        "name": name,
        "description": f"Reusable SQL snippet: {name}",
        "entity_id": entity_id,
        "content": sql,
        "archived": False,
        "serdes/meta": [
            {"model": "NativeQuerySnippet", "id": entity_id, "label": name}
        ],
    }


def build_all(config: dict, domain_filter: str = None):
    """Walk transforms/ and generate _sync/ output."""
    sync_transforms = SYNC_DIR / "transforms"
    sync_snippets = SYNC_DIR / "snippets"
    sync_transforms.mkdir(parents=True, exist_ok=True)
    sync_snippets.mkdir(parents=True, exist_ok=True)

    built = 0
    errors = []

    # Build transforms
    for sql_path in sorted(TRANSFORMS_DIR.rglob("*.sql")):
        if sql_path.name.startswith("_"):
            continue  # skip templates

        domain = sql_path.parent.name
        if domain_filter and domain != domain_filter:
            continue

        name = sql_path.stem
        meta_path = sql_path.with_suffix(".meta.yml")
        meta = read_meta(meta_path)

        if not meta and not meta_path.exists():
            errors.append(f"  WARN: {sql_path.relative_to(ROOT)} has no .meta.yml companion")

        sql = read_sql(sql_path)
        if not sql.strip():
            errors.append(f"  SKIP: {sql_path.relative_to(ROOT)} is empty")
            continue

        transform_dict = build_transform_yaml(sql, meta, domain, name, config)
        out_path = sync_transforms / f"{name}.yml"

        with open(out_path, "w") as f:
            yaml.dump(
                transform_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=120,
            )
        built += 1

    # Build snippets
    if SNIPPETS_DIR.exists():
        for sql_path in sorted(SNIPPETS_DIR.glob("*.sql")):
            snippet_dict = build_snippet_yaml(sql_path)
            out_path = sync_snippets / f"{sql_path.stem}.yml"
            with open(out_path, "w") as f:
                yaml.dump(
                    snippet_dict,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            built += 1

    return built, errors


def check_mode(config: dict):
    """Dry-run: check if _sync/ matches what would be generated."""
    import tempfile
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_sync = Path(tmpdir) / "_sync"
        tmp_transforms = tmp_sync / "transforms"
        tmp_snippets = tmp_sync / "snippets"
        tmp_transforms.mkdir(parents=True)
        tmp_snippets.mkdir(parents=True)

        # Build into temp directory
        for sql_path in sorted(TRANSFORMS_DIR.rglob("*.sql")):
            if sql_path.name.startswith("_"):
                continue
            domain = sql_path.parent.name
            name = sql_path.stem
            meta_path = sql_path.with_suffix(".meta.yml")
            meta = read_meta(meta_path)
            sql = read_sql(sql_path)
            if not sql.strip():
                continue
            t = build_transform_yaml(sql, meta, domain, name, config)
            out = tmp_transforms / f"{name}.yml"
            with open(out, "w") as f:
                yaml.dump(t, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)

        if SNIPPETS_DIR.exists():
            for sql_path in sorted(SNIPPETS_DIR.glob("*.sql")):
                s = build_snippet_yaml(sql_path)
                out = tmp_snippets / f"{sql_path.stem}.yml"
                with open(out, "w") as f:
                    yaml.dump(s, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        if not SYNC_DIR.exists():
            print("_sync/ directory does not exist. Run: make build")
            sys.exit(1)

        result = subprocess.run(
            ["diff", "-rq", str(SYNC_DIR), str(tmp_sync)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print("_sync/ is out of date. Run: make build")
            print(result.stdout)
            sys.exit(1)
        else:
            print("_sync/ is up to date.")


def main():
    parser = argparse.ArgumentParser(description="Build Metabase serialization YAML from SQL transforms")
    parser.add_argument("--check", action="store_true", help="Check if _sync/ is up to date (CI mode)")
    parser.add_argument("--domain", help="Build only a specific domain")
    args = parser.parse_args()

    config = load_config()

    if args.check:
        check_mode(config)
        return

    built, errors = build_all(config, domain_filter=args.domain)

    for e in errors:
        print(e)

    domain_msg = f" (domain: {args.domain})" if args.domain else ""
    print(f"\n  Built {built} files in _sync/{domain_msg}")


if __name__ == "__main__":
    main()
