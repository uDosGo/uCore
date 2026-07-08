"""DocLang Bridge — Export vault/AppFlowy/canonical docs into unified DocLang + AI context format.

Follows the spec at docs/DOCLANG_BRIDGE_EXPORT_SPEC.md.

Usage:
    from app.services.doclang_bridge import export_vault_to_doclang_context
    result = export_vault_to_doclang_context(source_dir="/path/to/vault")
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.doclang_bridge")

WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def extract_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    """Extract YAML front matter from markdown text.
    Returns (frontmatter_dict, remaining_body)."""
    frontmatter: dict[str, Any] = {}
    match = FRONTMATTER_RE.match(markdown)
    if not match:
        return frontmatter, markdown

    try:
        import yaml
        parsed = yaml.safe_load(match.group(1))
        if isinstance(parsed, dict):
            frontmatter = parsed
    except Exception:
        # Try JSON as fallback
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                frontmatter = parsed
        except Exception:
            pass

    return frontmatter, markdown[match.end():]


def extract_wiki_links(body: str) -> list[dict[str, str | None]]:
    """Extract wiki-style [[links]] from markdown body."""
    links: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for match in WIKI_LINK_RE.finditer(body):
        target = match.group(1).strip()
        label = match.group(2).strip() if match.group(2) else None
        key = f"{target}|{label}"
        if key not in seen:
            seen.add(key)
            links.append({"target": target, "label": label})
    return links


def extract_sections(body: str) -> list[dict[str, Any]]:
    """Split markdown body into heading-demarcated sections."""
    sections: list[dict[str, Any]] = []
    lines = body.split("\n")
    current_id = "summary"
    current_heading: str | None = None
    current_level = 0
    current_lines: list[str] = []
    heading_count = 0

    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            # Flush previous section
            if current_lines or current_id:
                sections.append({
                    "id": current_id,
                    "heading": current_heading,
                    "level": current_level,
                    "content": "\n".join(current_lines).strip(),
                })
            heading_count += 1
            hashes = m.group(1)
            current_level = len(hashes)
            current_heading = m.group(2).strip()
            current_id = _slugify(current_heading) if current_heading else f"section-{heading_count}"
            current_lines = []
        else:
            current_lines.append(line)

    # Flush final section
    sections.append({
        "id": current_id,
        "heading": current_heading,
        "level": current_level,
        "content": "\n".join(current_lines).strip(),
    })

    return sections


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _extract_folder_tags(relative_path: Path) -> list[str]:
    """Derive tags from folder path components."""
    tags: list[str] = []
    for part in relative_path.parts[:-1]:  # Skip the filename
        if part and not part.startswith("."):
            tags.append(part.lower())
    return tags


def _derive_binder(relative_path: Path) -> str:
    """Derive binder (top-level folder) from path."""
    parts = relative_path.parts
    if len(parts) > 1:
        return parts[0]
    return "root"


def export_document(
    file_path: Path,
    source_dir: Path,
    *,
    extra_tags: list[str] | None = None,
) -> dict[str, Any]:
    """Export a single markdown document into DocLang envelope."""
    body = file_path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body_text = extract_frontmatter(body)
    relative = file_path.relative_to(source_dir)
    source_path = str(relative).replace("\\", "/")
    doc_id = f"vault:{source_path}"

    # Normalize fields from frontmatter
    title = str(frontmatter.get("title", file_path.stem))
    doc_type = str(frontmatter.get("type") or frontmatter.get("doc_type", "note"))
    status = str(frontmatter.get("status", "published"))
    tags = _normalize_tags(frontmatter.get("tags", []))
    tags.extend(_extract_folder_tags(relative))
    if extra_tags:
        tags.extend(extra_tags)
    # Deduplicate while preserving order
    seen_tags: set[str] = set()
    unique_tags: list[str] = []
    for t in tags:
        if t not in seen_tags:
            seen_tags.add(t)
            unique_tags.append(t)
    tags = unique_tags

    aliases = _normalize_tags(frontmatter.get("aliases", []))
    workspace = str(frontmatter.get("workspace") or source_dir.name)
    wiki_links = extract_wiki_links(body_text)
    sections = extract_sections(body_text)

    # Location
    location: dict[str, Any] | None = None
    ucode_val = frontmatter.get("ucode")
    lat_val = frontmatter.get("lat")
    lon_val = frontmatter.get("lon")
    if ucode_val or lat_val is not None or lon_val is not None:
        location = {
            "label": str(frontmatter.get("location_label", "")),
            "ucode": str(ucode_val) if ucode_val else None,
            "lat": float(lat_val) if lat_val is not None else None,
            "lon": float(lon_val) if lon_val is not None else None,
            "layer": int(frontmatter.get("layer", 0)),
            "zoom_level": int(frontmatter.get("zoom_level", 340)),
        }

    # Filesystem
    filesystem = {
        "binder": frontmatter.get("binder") or _derive_binder(relative),
        "container": frontmatter.get("container", "personal"),
        "folder_tags": _extract_folder_tags(relative),
        "spatial_path": frontmatter.get("spatial_path"),
    }

    # Timestamps
    stat = file_path.stat()
    created_at = frontmatter.get("created") or frontmatter.get("created_at") or _iso(stat.st_ctime)
    updated_at = frontmatter.get("updated") or frontmatter.get("updated_at") or _iso(stat.st_mtime)

    return {
        "doclang_version": "0.1",
        "document": {
            "id": doc_id,
            "canonical_id": doc_id,
            "title": title,
            "doc_type": doc_type,
            "status": status,
            "source_system": "vault",
            "source_workspace": workspace,
            "source_path": source_path,
            "created_at": created_at,
            "updated_at": updated_at,
            "tags": tags,
            "aliases": aliases,
            "wiki_links": {"outbound": wiki_links},
            "location": location,
            "filesystem": filesystem,
            "frontmatter": frontmatter,
            "sections": sections,
            "body_markdown": body_text,
        },
    }


def _normalize_tags(raw: Any) -> list[str]:
    """Normalize tags to a list of strings."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(t) for t in raw]
    return [str(raw)]


def _iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def build_doclang_document(record: dict[str, Any]) -> dict[str, Any]:
    """Build a DocLang envelope from a vault record dict."""
    frontmatter = record.get("frontmatter", {})
    body = record.get("body", "")
    rel_path = record.get("rel_path", "")
    name = record.get("name", "")
    tags_raw = record.get("tags", [])
    modified = record.get("modified", "")

    # Extract wiki links from body
    wiki_links = extract_wiki_links(body)

    # Extract sections from body
    sections = extract_sections(body)

    # Build tags: combine frontmatter tags + record tags
    fm_tags = _normalize_tags(frontmatter.get("tags", []))
    rec_tags = _normalize_tags(tags_raw)
    all_tags: list[str] = []
    seen_tags: set[str] = set()
    for t in fm_tags + rec_tags:
        if t not in seen_tags:
            seen_tags.add(t)
            all_tags.append(t)

    # Title: prefer frontmatter title, then record name
    title = str(frontmatter.get("title", name or ""))

    # Location
    location: dict[str, Any] | None = None
    ucode_val = frontmatter.get("ucode")
    loc_label = frontmatter.get("location", "")
    if ucode_val or loc_label:
        location = {
            "label": str(loc_label),
            "ucode": str(ucode_val) if ucode_val else None,
            "lat": None,
            "lon": None,
            "layer": int(frontmatter.get("layer", 0)),
            "zoom_level": int(frontmatter.get("zoom_level", 340)),
        }

    # Filesystem
    binder = frontmatter.get("binder", "")
    filesystem = {
        "binder": binder,
        "container": frontmatter.get("container", "personal"),
        "folder_tags": [],
        "spatial_path": frontmatter.get("spatial_path"),
    }

    return {
        "doclang_version": "0.1",
        "document": {
            "id": f"vault:{rel_path}" if rel_path else "",
            "canonical_id": f"vault:{rel_path}" if rel_path else "",
            "title": title,
            "doc_type": str(frontmatter.get("type") or frontmatter.get("doc_type", "note")),
            "status": str(frontmatter.get("status", "published")),
            "source_system": "vault",
            "source_workspace": "",
            "source_path": rel_path,
            "created_at": modified,
            "updated_at": modified,
            "tags": all_tags,
            "aliases": _normalize_tags(frontmatter.get("aliases", [])),
            "wiki_links": {"outbound": wiki_links},
            "location": location,
            "filesystem": filesystem,
            "frontmatter": frontmatter,
            "sections": sections,
            "body_markdown": body,
        },
    }


def render_ai_context(envelope: dict[str, Any]) -> str:
    """Render a DocLang envelope into a compact AI-friendly text block."""
    doc = envelope.get("document", envelope.get("doclang", {}).get("document", envelope))
    if not isinstance(doc, dict):
        return ""
    lines: list[str] = []
    title = doc.get("title", "")
    if title:
        lines.append(f"TITLE: {title}")
    doc_type = doc.get("doc_type", "")
    if doc_type:
        lines.append(f"TYPE: {doc_type}")
    status = doc.get("status", "")
    if status:
        lines.append(f"STATUS: {status}")
    src = doc.get("source_path", doc.get("source_system", ""))
    if src:
        lines.append(f"SOURCE: {src}")
    tags = doc.get("tags", [])
    if tags:
        lines.append(f"TAGS: {', '.join(tags)}")
    location = doc.get("location")
    if location and isinstance(location, dict):
        ucode = location.get("ucode")
        if ucode:
            lines.append(f"LOCATION_UCODE: {ucode}")
        label = location.get("label")
        if label:
            lines.append(f"LOCATION_LABEL: {label}")
    wiki = doc.get("wiki_links", {}).get("outbound", [])
    if wiki:
        targets = [w.get("target", "") for w in wiki if w.get("target")]
        if targets:
            lines.append(f"WIKI_LINKS: {', '.join(targets)}")
    sections = doc.get("sections", [])
    for s in sections:
        heading = s.get("heading", "")
        content = s.get("content", "")
        if heading and content:
            lines.append(f"- {heading}: {content}")
        elif content:
            lines.append(f"  {content}")
    return "\n".join(lines)


def export_vault_to_doclang_context(
    source_dir: str,
    output_path: str,
    *,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Export all markdown files in source_dir to DocLang + AI context JSONL.

    Returns a dict with export summary."""
    source = Path(source_dir).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if not source.is_dir():
        return {"error": f"Source directory not found: {source}", "count": 0}

    exported = 0
    skipped = 0
    errors = 0

    with output.open("w", encoding="utf-8") as out:
        for md_file in sorted(source.rglob("*.md")):
            rel = md_file.relative_to(source)
            if any(p.startswith(".") for p in rel.parts):
                skipped += 1
                continue

            try:
                doc = export_document(md_file, source, extra_tags=tags)
                ai_ctx = render_ai_context(doc)
                payload = {"doclang": doc, "ai_context": ai_ctx}
                out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                exported += 1
            except Exception as exc:
                log.warning("Failed to export %s: %s", rel, exc)
                errors += 1

    return {
        "source_dir": str(source),
        "output_path": str(output),
        "count": exported,
        "documents_exported": exported,
        "documents_skipped": skipped,
        "export_errors": errors,
    }
