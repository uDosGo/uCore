from __future__ import annotations
import glob
import os
from pathlib import Path
from typing import Dict, List
from app.skills.state import read_state


def _tail_lines(path: Path, max_lines: int = 200) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return [l.rstrip("\n") for l in lines[-max_lines:]]
    except Exception:
        return []


def recent_errors_from_logs(log_dir: Path | None = None, max_entries: int = 50) -> List[Dict]:
    if log_dir is None:
        log_dir = Path.home() / ".ucore" / "logs"
    out: List[Dict] = []
    if not log_dir.exists():
        return out
    # examine all .log and .err files
    patterns = ["*.log", "*.err", "*.stderr", "*.out"]
    for pat in patterns:
        for p in sorted(glob.glob(str(log_dir / pat))):
            path = Path(p)
            lines = _tail_lines(path, max_lines=200)
            # collect lines that look like errors
            for ln in reversed(lines):
                if "ERROR" in ln or "Exception" in ln or "Traceback" in ln or "CRITICAL" in ln:
                    out.append({"file": path.name, "line": ln})
                    if len(out) >= max_entries:
                        return out
    return out


def get_health_summary() -> Dict:
    """Return a small health summary combining skill-state and recent errors."""
    state = read_state()
    errors = recent_errors_from_logs()
    return {
        "ok": len(errors) == 0,
        "recent_errors": errors[:50],
        "skill_state_summary": state,
    }
