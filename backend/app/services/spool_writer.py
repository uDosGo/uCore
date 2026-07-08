"""spool_writer — Write structured log entries to uCore spool.

Provides a simple interface for skills and snacks to write to the spool
for audit trails and activity tracking.

Spec: docs/SPOOL_SPEC.md
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

LOG_DIR = Path.home() / ".ucore" / "logs"


def write_spool(
    level: str = "INFO",
    module: str = "unknown",
    message: str = "",
    tags: list[str] | None = None,
) -> None:
    """Write a structured log entry to the spool.

    Args:
        level: Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)
        module: Module name for categorization
        message: Log message content
        tags: Optional list of tags for filtering
    """
    log_dir = LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
    tag_str = " ".join(f"[{t}]" for t in (tags or []))
    log_line = f"{timestamp} [{level}] {module}: {message} {tag_str}\n"

    # Append to main log
    log_file = log_dir / "spool.log"
    existing = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    log_file.write_text(existing + log_line, encoding="utf-8")

    # Also append to module-specific log
    module_log = log_dir / f"{module}.log"
    existing_mod = module_log.read_text(encoding="utf-8") if module_log.exists() else ""
    module_log.write_text(existing_mod + log_line, encoding="utf-8")


def write_spool_batch(
    entries: list[dict[str, str]],
) -> int:
    """Write multiple log entries at once.

    Args:
        entries: List of {level, module, message, tags} dicts

    Returns:
        Number of entries written
    """
    log_dir = LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
    lines = []

    for entry in entries:
        level = entry.get("level", "INFO")
        module = entry.get("module", "unknown")
        message = entry.get("message", "")
        tags = entry.get("tags", [])
        tag_str = " ".join(f"[{t}]" for t in tags)
        lines.append(f"{timestamp} [{level}] {module}: {message} {tag_str}\n")

    if lines:
        log_file = log_dir / "spool.log"
        log_file.write_text("".join(lines), encoding="utf-8")

    return len(lines)
