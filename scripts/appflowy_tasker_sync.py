#!/usr/bin/env python3
"""Export AppFlowy/local workflow rows into Tasker-style Markdown files.

Usage:
  python scripts/appflowy_tasker_sync.py \
    --db database \
    --sql "SELECT * FROM row_table LIMIT 20" \
    --tasker-dir .tasker \
    --board inbox
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.knowledge.local_first import discover_databases, run_query  # noqa: E402
from app.services.tasker_bridge import export_rows_to_tasker  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export AppFlowy tasks to Markdown-first Tasker files")
    parser.add_argument("--db", default="database", help="Known DB key or absolute sqlite path")
    parser.add_argument("--sql", default="SELECT * FROM row_table LIMIT 20", help="Read-only SQL query")
    parser.add_argument("--tasker-dir", default=str(PROJECT_ROOT / ".tasker"), help="Destination .tasker directory")
    parser.add_argument("--board", default="inbox", help="Board/folder name")
    parser.add_argument("--title-field", default="title", help="Column used for task title")
    parser.add_argument("--body-fields", default="description,notes,content", help="Comma-separated body columns")
    parser.add_argument("--status-field", default="status", help="Column used for task status")
    parser.add_argument("--id-field", default="id", help="Column used for task identifier")
    parser.add_argument("--dry-run", action="store_true", help="Preview exports without writing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dbs = discover_databases()
    db_path = dbs.get(args.db, args.db)
    result = run_query(db_path=db_path, sql=args.sql, params=[], write=False)
    exported = export_rows_to_tasker(
        result.get("rows", []),
        tasker_dir=args.tasker_dir,
        board=args.board,
        title_field=args.title_field,
        body_fields=[part.strip() for part in args.body_fields.split(",") if part.strip()],
        status_field=args.status_field,
        id_field=args.id_field,
        source="appflowy",
        dry_run=args.dry_run,
    )
    print(json.dumps({"db": args.db, "db_path": db_path, **exported}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
