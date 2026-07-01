from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "task"


def render_task_markdown(
    *,
    title: str,
    source: str,
    source_id: str,
    status: str,
    body: str,
    metadata: dict[str, Any],
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# {title}",
        "",
        f"- status: {status}",
        f"- source: {source}",
        f"- source_id: {source_id}",
        f"- synced_at: {timestamp}",
        "",
        "## Summary",
        body or "No summary available.",
    ]

    extra_meta = {
        key: value
        for key, value in metadata.items()
        if key not in {"title", "name", "status", "id", "uuid", "description", "notes"}
    }
    if extra_meta:
        lines.extend(["", "## Metadata"])
        for key, value in extra_meta.items():
            lines.append(f"- {key}: {value}")

    lines.append("")
    return "\n".join(lines)


def export_rows_to_tasker(
    rows: list[dict[str, Any]],
    *,
    tasker_dir: str,
    board: str = "inbox",
    title_field: str = "title",
    body_fields: list[str] | None = None,
    status_field: str = "status",
    id_field: str = "id",
    source: str = "appflowy",
    dry_run: bool = False,
) -> dict[str, Any]:
    body_fields = body_fields or ["description", "notes", "content"]
    out_dir = Path(tasker_dir).expanduser() / board
    exported: list[dict[str, Any]] = []

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(rows, start=1):
        title = str(row.get(title_field) or row.get("name") or f"Task {index}").strip()
        source_id = str(row.get(id_field) or row.get("uuid") or index)
        status = str(row.get(status_field) or "todo").strip().lower()

        body_parts: list[str] = []
        for field in body_fields:
            value = row.get(field)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                body_parts.append(f"{field}: {text}")
        body = "\n\n".join(body_parts)

        filename = f"{status}-{slugify(title)}-{slugify(source_id)}.md"
        path = out_dir / filename
        content = render_task_markdown(
            title=title,
            source=source,
            source_id=source_id,
            status=status,
            body=body,
            metadata=row,
        )
        if not dry_run:
            path.write_text(content, encoding="utf-8")
        exported.append(
            {
                "title": title,
                "status": status,
                "source_id": source_id,
                "file": str(path),
            },
        )

    return {
        "tasker_dir": str(Path(tasker_dir).expanduser()),
        "board": board,
        "count": len(exported),
        "exports": exported,
        "dry_run": dry_run,
    }
