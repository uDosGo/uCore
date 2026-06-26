from __future__ import annotations

import glob
from pathlib import Path

from app.skills.state import read_state


def _clean_and_truncate_line(line: str, max_len: int = 150) -> str:
    """Truncate the line to a safe length and redact secret/token patterns."""
    # Simple redaction for common authorization/token values if any
    import re
    # Match strings resembling bearer tokens, api keys, password/secret strings
    # Redact Authorization header or passwords or any other standard credential strings
    redacted = re.sub(
        r'(?i)(token|bearer|auth|authorization|api_key|password|secret|key)\s*[:= ]\s*["\']?[a-zA-Z0-9_\.\-]{8,150}["\']?',
        r'\1: "[REDACTED]"',
        line
    )
    if len(redacted) > max_len:
        return redacted[:max_len] + "..."
    return redacted


def _tail_lines(path: Path, max_lines: int = 200) -> list[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            return [l.rstrip("\n") for l in lines[-max_lines:]]
    except Exception:
        return []


def recent_errors_from_logs(log_dir: Path | None = None, max_entries: int = 50) -> list[dict]:
    if log_dir is None:
        log_dir = Path.home() / ".ucore" / "logs"
    out: list[dict] = []
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
                    cleaned = _clean_and_truncate_line(ln)
                    out.append({"file": path.name, "line": cleaned})
                    if len(out) >= max_entries:
                        return out
    return out


def get_health_summary() -> dict:
    """Return a small health summary combining skill-state and recent errors."""
    state = read_state()
    errors = recent_errors_from_logs()
    return {
        "ok": len(errors) == 0,
        "recent_errors": errors[:50],
        "skill_state_summary": state,
    }
