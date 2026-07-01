#!/usr/bin/env python3
"""Bidirectional markdown sync for AppFlowy-adjacent vault containers.

Usage:
  python scripts/appflowy_vault_sync.py --config config/vault-sync.yaml --dry-run
  python scripts/appflowy_vault_sync.py --config config/vault-sync.yaml

This tool is intentionally conservative:
- Only syncs markdown files.
- Tracks per-file hashes in a state file.
- Detects two-sided edits and writes conflict files instead of overwriting.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import shutil

import yaml

EXCLUDED_DIRS = {".git", "node_modules", ".venv", "venv", ".obsidian", ".trash"}


@dataclass
class Action:
    container_id: str
    kind: str
    rel_path: str
    detail: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expand(path_text: str) -> Path:
    return Path(os.path.expanduser(path_text)).resolve()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_included(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) for p in patterns)


def walk_markdown(root: Path, include: list[str]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not root.exists():
        return found

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        base = Path(current_root)
        for name in files:
            if not name.lower().endswith((".md", ".markdown")):
                continue
            p = base / name
            rel = p.relative_to(root).as_posix()
            if is_included(rel, include):
                found[rel] = p
    return found


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {"version": 1, "files": {}}
    with state_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "files" not in data:
        data["files"] = {}
    return data


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_conflict(base: Path, rel: str, source_label: str, source_file: Path, dry_run: bool) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rel_path = Path(rel)
    conflict_name = f"{rel_path.stem}.conflict-{source_label}.{stamp}{rel_path.suffix}"
    conflict_rel = rel_path.with_name(conflict_name)
    target = base / conflict_rel
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    return conflict_rel.as_posix()


def sync_container(container: dict[str, Any], state: dict[str, Any], dry_run: bool) -> list[Action]:
    cid = container["id"]
    left = expand(container["left"])
    right = expand(container["right"])
    include = container.get("include", ["**/*.md", "**/*.markdown"])
    mode = container.get("mode", "bidirectional")

    left_map = walk_markdown(left, include)
    right_map = walk_markdown(right, include)
    rels = sorted(set(left_map) | set(right_map))

    actions: list[Action] = []
    files_state = state.setdefault("files", {})

    for rel in rels:
        key = f"{cid}:{rel}"
        prev = files_state.get(key, {})
        left_file = left_map.get(rel)
        right_file = right_map.get(rel)

        left_hash = file_hash(left_file) if left_file and left_file.exists() else None
        right_hash = file_hash(right_file) if right_file and right_file.exists() else None
        prev_left = prev.get("left_hash")
        prev_right = prev.get("right_hash")

        # Both missing should not happen because rel was union of discovered files.
        if left_hash is None and right_hash is None:
            continue

        if left_hash is None and right_hash is not None:
            if mode in ("bidirectional", "right_to_left"):
                dest = left / rel
                copy_file(right_file, dest, dry_run)
                actions.append(Action(cid, "copy", rel, "right -> left"))
                left_hash = right_hash
            else:
                actions.append(Action(cid, "skip", rel, "left missing, mode blocks copy"))

        elif right_hash is None and left_hash is not None:
            if mode in ("bidirectional", "left_to_right"):
                dest = right / rel
                copy_file(left_file, dest, dry_run)
                actions.append(Action(cid, "copy", rel, "left -> right"))
                right_hash = left_hash
            else:
                actions.append(Action(cid, "skip", rel, "right missing, mode blocks copy"))

        elif left_hash == right_hash:
            actions.append(Action(cid, "noop", rel, "already in sync"))

        else:
            left_changed = prev_left is not None and left_hash != prev_left
            right_changed = prev_right is not None and right_hash != prev_right

            if mode == "left_to_right":
                copy_file(left_file, right / rel, dry_run)
                right_hash = left_hash
                actions.append(Action(cid, "copy", rel, "left -> right (mode)"))
            elif mode == "right_to_left":
                copy_file(right_file, left / rel, dry_run)
                left_hash = right_hash
                actions.append(Action(cid, "copy", rel, "right -> left (mode)"))
            elif left_changed and right_changed:
                left_conflict = write_conflict(left, rel, "right", right_file, dry_run)
                right_conflict = write_conflict(right, rel, "left", left_file, dry_run)
                actions.append(Action(cid, "conflict", rel, f"wrote {left_conflict} and {right_conflict}"))
            elif left_changed and not right_changed:
                copy_file(left_file, right / rel, dry_run)
                right_hash = left_hash
                actions.append(Action(cid, "copy", rel, "left changed -> right"))
            elif right_changed and not left_changed:
                copy_file(right_file, left / rel, dry_run)
                left_hash = right_hash
                actions.append(Action(cid, "copy", rel, "right changed -> left"))
            else:
                # No historical state yet; newest file wins.
                left_mtime = left_file.stat().st_mtime
                right_mtime = right_file.stat().st_mtime
                if left_mtime >= right_mtime:
                    copy_file(left_file, right / rel, dry_run)
                    right_hash = left_hash
                    actions.append(Action(cid, "copy", rel, "bootstrap newest left -> right"))
                else:
                    copy_file(right_file, left / rel, dry_run)
                    left_hash = right_hash
                    actions.append(Action(cid, "copy", rel, "bootstrap newest right -> left"))

        files_state[key] = {
            "container": cid,
            "rel_path": rel,
            "left_hash": left_hash,
            "right_hash": right_hash,
            "synced_at": utc_now(),
        }

    return actions


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bidirectional vault markdown sync")
    p.add_argument("--config", default="config/vault-sync.yaml", help="Path to YAML config")
    p.add_argument("--dry-run", action="store_true", help="Show actions without writing files")
    p.add_argument("--summary-only", action="store_true", help="Print only action counts")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(f"Config not found: {cfg_path}")
        print("Copy config/vault-sync.example.yaml to config/vault-sync.yaml and edit paths.")
        return 2

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    state_file = expand(cfg.get("state_file", "~/.ucore/vault-sync-state.json"))
    containers = cfg.get("containers", [])
    if not containers:
        print("No containers configured.")
        return 2

    state = load_state(state_file)
    all_actions: list[Action] = []

    for container in containers:
        if not all(k in container for k in ("id", "left", "right")):
            print(f"Skipping invalid container config: {container}")
            continue
        actions = sync_container(container, state, args.dry_run)
        all_actions.extend(actions)

    if not args.dry_run:
        save_state(state_file, state)

    counts: dict[str, int] = {}
    for a in all_actions:
        counts[a.kind] = counts.get(a.kind, 0) + 1

    print("Sync complete")
    print(f"dry_run={args.dry_run}")
    print("counts:", counts)

    if not args.summary_only:
        for a in all_actions:
            print(f"[{a.container_id}] {a.kind:8s} {a.rel_path} :: {a.detail}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
