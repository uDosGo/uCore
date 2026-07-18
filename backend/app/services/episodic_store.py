"""Episodic correction log — append-only JSONL store.

Durable history of corrections, lessons, decisions, and observations
recorded during the project lifecycle. Used by brain_sync to include
recent entries in private wisdom synthesis.

Default store: <PROJECT_ROOT>/.episodic/corrections.jsonl
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.settings import settings

PROJECT_ROOT = settings.udos_root / "uCore"
EPISODIC_DIR = PROJECT_ROOT / ".episodic"
EPISODIC_LOG = EPISODIC_DIR / "corrections.jsonl"

ENTRY_TYPES = frozenset(
    {"correction", "lesson", "decision", "observation"},
)
SEVERITIES = frozenset({"low", "medium", "high"})


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def append_entry(
    *,
    entry_type: str,
    description: str,
    context: str = "",
    severity: str = "low",
    tags: list[str] | None = None,
    source: str = "manual",
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Append one structured entry to the episodic log."""
    if entry_type not in ENTRY_TYPES:
        raise ValueError(
            f"Invalid type '{entry_type}'; "
            f"must be one of {sorted(ENTRY_TYPES)}",
        )
    if severity not in SEVERITIES:
        raise ValueError(
            f"Invalid severity '{severity}'; "
            f"must be one of {sorted(SEVERITIES)}",
        )
    entry: dict[str, Any] = {
        "timestamp": _utc_now(),
        "type": entry_type,
        "description": description.strip(),
        "context": context.strip(),
        "severity": severity,
        "tags": tags or [],
        "source": source,
    }
    target = log_path or EPISODIC_LOG
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    return entry


def read_entries(
    hours: int = 24,
    entry_type: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    log_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Read entries from the episodic log, newest-first."""
    target = log_path or EPISODIC_LOG
    if not target.exists():
        return []
    cutoff = (
        datetime.now(UTC) - timedelta(hours=hours)
    ).isoformat()
    entries: list[dict[str, Any]] = []
    with target.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("timestamp", "") < cutoff:
                continue
            if entry_type and record.get("type") != entry_type:
                continue
            if severity and record.get("severity") != severity:
                continue
            entries.append(record)
    entries.reverse()
    return entries[:limit]


def summarize_entries(
    hours: int = 24,
    log_path: Path | None = None,
) -> str | None:
    """Return a markdown summary of recent episodic entries."""
    entries = read_entries(hours=hours, limit=30, log_path=log_path)
    if not entries:
        return None
    lines = [f"## Episodic Log (last {hours}h)", ""]
    by_type: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        by_type.setdefault(e.get("type", "unknown"), []).append(e)
    for etype, items in sorted(by_type.items()):
        lines.append(f"### {etype.title()}s ({len(items)})")
        for item in items[:5]:
            ts = str(item.get("timestamp", ""))[:19]
            sev = item.get("severity", "low")
            desc = str(item.get("description", ""))[:120]
            lines.append(f"- [{ts}] [{sev}] {desc}")
        lines.append("")
    return "\n".join(lines).rstrip()
