#!/usr/bin/env python3
"""uCore secret-store CLI.

Usage examples:
  python scripts/udos_secret.py list
  python scripts/udos_secret.py set OPENROUTER_API_KEY sk-xxx
  python scripts/udos_secret.py get OPENROUTER_API_KEY
  python scripts/udos_secret.py delete OPENROUTER_API_KEY
  python scripts/udos_secret.py sync-env --target backend/.env
  python scripts/udos_secret.py audit --limit 50
  python scripts/udos_secret.py sync-github --repository owner/repo
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE_URL = os.environ.get("UCORE_URL", "http://localhost:8484")


def request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = DEFAULT_BASE_URL.rstrip("/")
    url = f"{base}{path}"
    if query:
        params = urllib.parse.urlencode(
            {k: v for k, v in query.items() if v is not None}
        )
        if params:
            url = f"{url}?{params}"

    body_bytes = None
    headers = {
        "Accept": "application/json",
        "X-Actor": "udos-secret-cli",
    }
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url,
        method=method,
        data=body_bytes,
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        details = (
            exc.read().decode("utf-8", errors="replace")
            if exc.fp
            else ""
        )
        try:
            parsed = json.loads(details) if details else {}
            message = parsed.get("error") or details or str(exc)
        except json.JSONDecodeError:
            message = details or str(exc)
        raise RuntimeError(f"HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from exc


def cmd_list(args: argparse.Namespace) -> int:
    data = request_json("GET", "/api/secrets")
    secrets = data.get("secrets", [])
    if not secrets:
        print("No secrets stored.")
        return 0

    for row in secrets:
        print(f"{row.get('name', '')}: {row.get('masked', '')}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    data = request_json("GET", f"/api/secrets/{args.key}")
    value = data.get("value")
    if value is None:
        print(f"Secret {args.key} not found.", file=sys.stderr)
        return 1
    print(value)
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    data = request_json(
        "POST",
        f"/api/secrets/{args.key}",
        payload={"value": args.value},
    )
    print(f"Saved {data.get('name', args.key)} ({data.get('masked', '****')})")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    data = request_json("DELETE", f"/api/secrets/{args.key}")
    print(f"Deleted {data.get('name', args.key)}")
    return 0


def cmd_sync_env(args: argparse.Namespace) -> int:
    if args.target:
        payload = {"target": args.target, "only_missing": not args.overwrite}
        data = request_json("POST", "/api/secrets/export-env", payload=payload)
        print(
            f"Exported to {data.get('target')} "
            f"| added={data.get('added_count', 0)} "
            f"updated={data.get('updated_count', 0)}"
        )
        return 0

    data = request_json("POST", "/api/secrets/import-env")
    print(
        f"Imported {data.get('imported_count', 0)} keys "
        "from env/dotenv into store "
        f"(total={data.get('count', 0)})"
    )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    data = request_json(
        "GET",
        "/api/secrets/audit",
        query={"limit": args.limit},
    )
    events = data.get("events", [])
    if not events:
        print("No audit events recorded.")
        return 0

    for event in events:
        ts = event.get("timestamp", "")
        action = event.get("action", "")
        key = event.get("key", "")
        actor = event.get("actor", "")
        print(f"{ts} | {action:<10} | {key:<32} | {actor}")
    return 0


def cmd_sync_github(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {}
    if args.repository:
        payload["repository"] = args.repository
    if args.values_json:
        try:
            payload["secret_values"] = json.loads(args.values_json)
        except json.JSONDecodeError as exc:
            print(f"Invalid --values-json payload: {exc}", file=sys.stderr)
            return 2

    data = request_json("POST", "/api/secrets/sync-github", payload=payload)
    print(
        f"GitHub listed={data.get('listed_count', 0)} "
        f"imported={data.get('imported_count', 0)} "
        f"missing={data.get('missing_values_count', 0)}"
    )
    note = data.get("note")
    if note:
        print(note)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="uCore secret store CLI")
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Override API base URL "
            "(default: UCORE_URL or http://localhost:8484)"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_list = subparsers.add_parser("list", help="List stored secrets (masked)")
    p_list.set_defaults(func=cmd_list)

    p_get = subparsers.add_parser("get", help="Get a secret value")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_get)

    p_set = subparsers.add_parser("set", help="Set a secret value")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_set)

    p_delete = subparsers.add_parser("delete", help="Delete a secret")
    p_delete.add_argument("key")
    p_delete.set_defaults(func=cmd_delete)

    p_sync_env = subparsers.add_parser(
        "sync-env",
        help=(
            "Import env/dotenv into store, "
            "or export store to dotenv via --target"
        ),
    )
    p_sync_env.add_argument(
        "--target",
        default=None,
        help="Dotenv target path for export",
    )
    p_sync_env.add_argument(
        "--overwrite",
        action="store_true",
        help="When exporting to dotenv target, overwrite existing keys",
    )
    p_sync_env.set_defaults(func=cmd_sync_env)

    p_audit = subparsers.add_parser("audit", help="Show recent audit events")
    p_audit.add_argument("--limit", type=int, default=50)
    p_audit.set_defaults(func=cmd_audit)

    p_sync_gh = subparsers.add_parser(
        "sync-github",
        help="Sync GitHub secret names and import values from env/payload",
    )
    p_sync_gh.add_argument(
        "--repository",
        default=None,
        help="owner/repo for gh secret list",
    )
    p_sync_gh.add_argument(
        "--values-json",
        default=None,
        help='JSON object of secret values, e.g. {"OPENROUTER_API_KEY":"..."}',
    )
    p_sync_gh.set_defaults(func=cmd_sync_github)

    return parser


def main() -> int:
    global DEFAULT_BASE_URL

    parser = build_parser()
    args = parser.parse_args()

    if args.base_url:
        DEFAULT_BASE_URL = args.base_url

    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
