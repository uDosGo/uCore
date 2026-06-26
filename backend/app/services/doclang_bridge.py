from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.af_manager.sync import scan_vault

WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return slug.strip("-") or "section"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def extract_wiki_links(markdown: str) -> list[dict[str, str | None]]:
    links: list[dict[str, str | None]] = []
    for match in WIKI_LINK_RE.finditer(markdown):
        links.append(
            {
                "target": match.group(1).strip(),
                "label": match.group(2).strip() if match.group(2) else None,
            },
        )
    return links


def split_markdown_sections(markdown: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_heading: str | None = None
    current_level = 0
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        content = "\n".join(buffer).strip()
        if not content and current_heading is None:
            return
        section_id = _slugify(current_heading or "body")
        sections.append(
            {
                "id": section_id,
                "heading": current_heading,
                "level": current_level,
                "content": content,
            },
        )
        buffer = []

    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            current_level = len(match.group(1))
            current_heading = match.group(2).strip()
            continue
        buffer.append(line)

    flush()

    if not sections:
        sections.append(
            {
                "id": "body",
                "heading": None,
                "level": 0,
                "content": markdown.strip(),
            },
        )

    return sections


def build_doclang_document(
    record: dict[str, Any],
    *,
    source_system: str = "vault",
    source_workspace: str | None = None,
) -> dict[str, Any]:
    frontmatter = dict(record.get("frontmatter") or {})
    rel_path = str(record.get("rel_path") or record.get("source_path") or "")
    path_obj = Path(rel_path)
    folder_parts = [
        part for part in path_obj.parent.parts if part not in {".", ""}
    ]
    binder = frontmatter.get("binder")
    if binder is None and folder_parts:
        binder = folder_parts[0]
    tags = list(
        dict.fromkeys(
            _as_list(frontmatter.get("tags"))
            + _as_list(record.get("tags")),
        ),
    )
    aliases = _as_list(frontmatter.get("aliases"))
    body_markdown = str(
        record.get("body") or record.get("body_markdown") or "",
    )
    wiki_links = extract_wiki_links(body_markdown)
    document_id = (
        f"{source_system}:{rel_path or record.get('name', 'document')}"
    )
    title = frontmatter.get("title") or record.get("name") or "Untitled"
    doc_type = (
        frontmatter.get("doc_type") or frontmatter.get("type") or "note"
    )
    created_at = (
        frontmatter.get("created") or frontmatter.get("created_at")
    )
    updated_at = (
        frontmatter.get("updated")
        or frontmatter.get("updated_at")
        or record.get("modified")
    )

    location: dict[str, Any] | None = None
    if any(
        key in frontmatter
        for key in ("ucode", "lat", "lon", "layer", "zoom_level", "location")
    ):
        location = {
            "label": frontmatter.get("location"),
            "ucode": frontmatter.get("ucode"),
            "lat": frontmatter.get("lat"),
            "lon": frontmatter.get("lon"),
            "layer": frontmatter.get("layer"),
            "zoom_level": frontmatter.get("zoom_level"),
        }

    document = {
        "doclang_version": "0.1",
        "document": {
            "id": document_id,
            "canonical_id": document_id,
            "title": title,
            "doc_type": doc_type,
            "status": frontmatter.get("status") or "active",
            "source_system": source_system,
            "source_workspace": source_workspace,
            "source_path": rel_path,
            "created_at": created_at,
            "updated_at": updated_at,
            "tags": tags,
            "aliases": aliases,
            "wiki_links": {"outbound": wiki_links},
            "location": location,
            "filesystem": {
                "binder": binder,
                "container": frontmatter.get("container"),
                "folder_tags": folder_parts,
                "spatial_path": (
                    "/".join(folder_parts) if folder_parts else None
                ),
            },
            "frontmatter": frontmatter,
            "sections": split_markdown_sections(body_markdown),
            "body_markdown": body_markdown,
        },
    }
    return document


def render_ai_context(document_envelope: dict[str, Any]) -> str:
    doc = document_envelope["document"]
    lines = [
        f"TITLE: {doc['title']}",
        f"DOC_TYPE: {doc['doc_type']}",
        f"SOURCE: {doc['source_system']}::{doc['source_path']}",
        f"STATUS: {doc['status']}",
    ]

    if doc.get("tags"):
        lines.append(f"TAGS: {', '.join(doc['tags'])}")

    filesystem = doc.get("filesystem") or {}
    if filesystem.get("binder"):
        lines.append(f"BINDER: {filesystem['binder']}")
    if filesystem.get("spatial_path"):
        lines.append(f"SPATIAL_PATH: {filesystem['spatial_path']}")

    location = doc.get("location") or {}
    if location.get("ucode"):
        lines.append(f"LOCATION_UCODE: {location['ucode']}")
    if location.get("label"):
        lines.append(f"LOCATION_LABEL: {location['label']}")

    outbound = doc.get("wiki_links", {}).get("outbound", [])
    if outbound:
        rendered_links = []
        for link in outbound:
            if link.get("label"):
                rendered_links.append(f"{link['target']}|{link['label']}")
            else:
                rendered_links.append(str(link["target"]))
        lines.append(f"WIKI_LINKS: {', '.join(rendered_links)}")

    lines.append("SECTIONS:")
    for section in doc.get("sections", []):
        heading = section.get("heading") or "Body"
        content = str(section.get("content") or "").strip()
        compact = re.sub(r"\s+", " ", content)
        lines.append(f"- {heading}: {compact[:400]}")

    return "\n".join(lines) + "\n"


def export_vault_to_doclang_context(
    *,
    source_dir: str,
    output_path: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    records = scan_vault(source_dir, tags=tags)
    out_file = Path(output_path).expanduser()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    exported = 0
    with out_file.open("w", encoding="utf-8") as f:
        for record in records:
            envelope = build_doclang_document(record)
            payload = {
                "doclang": envelope,
                "ai_context": render_ai_context(envelope),
            }
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
            exported += 1

    return {
        "source_dir": str(Path(source_dir).expanduser()),
        "output_path": str(out_file),
        "count": exported,
    }
