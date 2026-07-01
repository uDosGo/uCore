#!/usr/bin/env python3
"""Map configured vault sources to real AppFlowy workspace IDs.

Usage:
  python scripts/appflowy_workspace_map.py
  python scripts/appflowy_workspace_map.py --config ~/.ucore/sync_config.yaml
  python scripts/appflowy_workspace_map.py --write

Notes:
- Uses existing AppFlowy workspaces discovered from local databases.
- Matches by source.workspace name first, then source.name.
- If no match exists, leaves workspace_id untouched.
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
        description="Map vault sources to AppFlowy workspace IDs",
    )
    parser.add_argument(
        "--config",
        default="~/.ucore/sync_config.yaml",
        help="Path to sync config YAML",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write mapped workspace_id values back to config file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    load_config = importlib.import_module("app.af_manager.config").load_config
    list_workspaces = importlib.import_module(
        "app.knowledge.appflowy"
    ).list_workspaces

    config_path = Path(args.config).expanduser()
    config = load_config(str(config_path))
    sources = config.get("sources", [])
    workspaces = list_workspaces()

    by_name: dict[str, dict] = {}
    for ws in workspaces:
        name = str(ws.get("name") or "").strip().lower()
        if name and name not in by_name:
            by_name[name] = ws

    mapped = []
    unmatched = []

    for source in sources:
        desired_name = str(
            source.get("workspace")
            or source.get("name")
            or ""
        ).strip()
        candidate = by_name.get(desired_name.lower()) if desired_name else None

        if candidate:
            source["workspace_id"] = str(candidate.get("id") or "")
            source["workspace"] = str(candidate.get("name") or desired_name)
            mapped.append(
                {
                    "source": source.get("name"),
                    "workspace": source.get("workspace"),
                    "workspace_id": source.get("workspace_id"),
                    "source_type": candidate.get("source"),
                }
            )
        else:
            unmatched.append(
                {
                    "source": source.get("name"),
                    "workspace_hint": (
                        source.get("workspace")
                        or source.get("name")
                    ),
                }
            )

    if args.write:
        try:
            import yaml  # type: ignore

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                yaml.safe_dump(config, sort_keys=False),
                encoding="utf-8",
            )
            write_status = "written"
        except Exception as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 2
    else:
        write_status = "dry-run"

    print(
        json.dumps(
            {
                "status": "ok",
                "mode": write_status,
                "config_path": str(config_path),
                "workspace_count": len(workspaces),
                "mapped_count": len(mapped),
                "unmatched_count": len(unmatched),
                "mapped": mapped,
                "unmatched": unmatched,
                "note": (
                    "Install appflowy-cli if you want scripted "
                    "workspace creation; "
                    "currently only existing workspaces are mapped."
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
