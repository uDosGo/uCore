#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Import configured vaults into AppFlowy workspaces and build local index.

Usage:
  python scripts/appflowy_import_workspaces.py
    python scripts/appflowy_import_workspaces.py \
        --config ~/.ucore/sync_config.yaml
  python scripts/appflowy_import_workspaces.py --source "Global Vault"
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import vault sources into mapped AppFlowy workspaces",
    )
    parser.add_argument(
        "--config",
        default="~/.ucore/sync_config.yaml",
        help="Sync config path",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Optional source name filter",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_config = importlib.import_module(
        "app.af_manager.config"
    ).load_config
    run_import = importlib.import_module(
        "app.af_manager.sync"
    ).run_import

    config = load_config(args.config)

    source_filter = args.source.strip()
    if source_filter:
        sources = config.get("sources", [])
        matched = [s for s in sources if s.get("name") == source_filter]
        if not matched:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": f"source not found: {source_filter}",
                        "available_sources": [s.get("name") for s in sources],
                    },
                    indent=2,
                )
            )
            return 2
        config["sources"] = matched

    summary = run_import(config)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
