#!/usr/bin/env python3
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
        description="Export vault markdown into DocLang + AI context JSONL",
    )
    parser.add_argument("--source-dir", required=True, help="Vault source dir")
    parser.add_argument(
        "--output-path",
        default=str(PROJECT_ROOT / "tmp" / "doclang-context.jsonl"),
        help="Output JSONL path",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Optional extra tag to apply to all documents",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    doclang_bridge = importlib.import_module("app.services.doclang_bridge")

    result = doclang_bridge.export_vault_to_doclang_context(
        source_dir=args.source_dir,
        output_path=args.output_path,
        tags=args.tag,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
