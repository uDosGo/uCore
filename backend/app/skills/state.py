from __future__ import annotations

import json
import time
from pathlib import Path

_STATE_DIR = Path.home() / ".ucore"
_STATE_FILE = _STATE_DIR / "skill-state.json"


def _ensure_dir() -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)


def read_state() -> dict:
    _ensure_dir()
    if not _STATE_FILE.exists():
        return {}
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def update_skill_state(skill_key: str, data: dict) -> None:
    """Merge `data` into the stored state for `skill_key` and persist."""
    _ensure_dir()
    s = read_state()
    cur = s.get(skill_key, {})
    cur.update(data)
    cur["last_updated_ts"] = int(time.time())
    s[skill_key] = cur
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2, sort_keys=True)
    except Exception:
        # Best-effort persistence; don't raise in production flows
        pass
