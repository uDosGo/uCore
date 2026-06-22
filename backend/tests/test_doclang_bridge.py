from __future__ import annotations

import json
from pathlib import Path

from app.services.doclang_bridge import (
    build_doclang_document,
    export_vault_to_doclang_context,
    render_ai_context,
)


def test_build_doclang_document_includes_frontmatter_and_spatial_fields():
    record = {
        "rel_path": "places/brisbane/note.md",
        "name": "Brisbane Note",
        "tags": ["city"],
        "modified": "2026-06-21T00:00:00Z",
        "frontmatter": {
            "title": "Brisbane Note",
            "tags": ["travel", "brisbane"],
            "aliases": ["BNE Note"],
            "ucode": "L340ABC",
            "location": "Brisbane",
            "binder": "places",
        },
        "body": "## Summary\nVisit [[South Bank|riverwalk]] soon.",
    }

    envelope = build_doclang_document(record)
    doc = envelope["document"]

    assert doc["title"] == "Brisbane Note"
    assert doc["filesystem"]["binder"] == "places"
    assert doc["location"]["ucode"] == "L340ABC"
    assert doc["wiki_links"]["outbound"][0]["target"] == "South Bank"
    assert "travel" in doc["tags"]
    assert "city" in doc["tags"]


def test_render_ai_context_compacts_doclang_fields():
    envelope = {
        "document": {
            "title": "Vault Integration",
            "doc_type": "guide",
            "source_system": "vault",
            "source_path": "technical/vault.md",
            "status": "published",
            "tags": ["vault", "guide"],
            "filesystem": {"binder": "technical", "spatial_path": None},
            "location": {"label": "Brisbane", "ucode": "L340XYZ"},
            "wiki_links": {"outbound": [{"target": "MCP", "label": None}]},
            "sections": [
                {
                    "heading": "Summary",
                    "content": "Useful context for AI.",
                    "level": 2,
                }
            ],
        }
    }

    context = render_ai_context(envelope)

    assert "TITLE: Vault Integration" in context
    assert "LOCATION_UCODE: L340XYZ" in context
    assert "WIKI_LINKS: MCP" in context
    assert "- Summary: Useful context for AI." in context


def test_export_vault_to_doclang_context_writes_jsonl(tmp_path: Path):
    source_dir = tmp_path / "vault"
    source_dir.mkdir(parents=True)
    note = source_dir / "example.md"
    note.write_text(
        (
            "---\n"
            "title: Example\n"
            "tags: [guide]\n"
            "---\n"
            "## Summary\n"
            "Hello [[World]].\n"
        ),
        encoding="utf-8",
    )

    out_file = tmp_path / "doclang.jsonl"
    result = export_vault_to_doclang_context(
        source_dir=str(source_dir),
        output_path=str(out_file),
    )

    assert result["count"] == 1
    payload = json.loads(out_file.read_text(encoding="utf-8").strip())
    assert payload["doclang"]["document"]["title"] == "Example"
    assert "TITLE: Example" in payload["ai_context"]
