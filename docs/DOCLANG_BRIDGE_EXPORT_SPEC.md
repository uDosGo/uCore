# DocLang Bridge Export Spec

Date: 2026-06-21
Status: Active local-first spec
Owner: uCore / uDocs migration track

## Goal

Define one normalized export format that can be produced from:

- AppFlowy local/cloud workspaces
- Vault markdown files
- Canonical engineering docs

The format must stay simple enough for local-first generation while being
structured enough for efficient AI ingestion, retrieval, and future transform
steps.

## Scope

This spec defines the canonical intermediate document shape for:

- document metadata
- front matter normalization
- wiki-link extraction
- location tagging
- spatial filesystem tagging
- body segmentation for later transforms

This spec does not define transport, embeddings, or cloud indexing.

## Design Constraints

1. Markdown remains the durable authoring format.
2. Export output must be deterministic from the same source state.
3. Stable identifiers matter more than pretty rendering.
4. Front matter is preferred over ad hoc inline conventions when both exist.
5. Spatial and wiki semantics must survive export without custom parsers in the
   consumer.

## Canonical Output Shape

The bridge export format is JSON with one top-level document envelope per
source document.

```json
{
  "doclang_version": "0.1",
  "document": {
    "id": "vault:technical/mcp/protocol.md",
    "canonical_id": "vault:technical/mcp/protocol.md",
    "title": "MCP Protocol",
    "doc_type": "spec",
    "status": "published",
    "source_system": "vault",
    "source_workspace": "personal",
    "source_path": "technical/mcp/protocol.md",
    "created_at": "2026-06-21T00:00:00Z",
    "updated_at": "2026-06-21T12:00:00Z",
    "tags": ["mcp", "protocol", "technical"],
    "aliases": ["Model Context Protocol"],
    "wiki_links": {
      "outbound": [
        {"target": "MCP Server", "label": null},
        {"target": "OpenRouter", "label": "routing"}
      ]
    },
    "location": {
      "label": "Brisbane",
      "ucode": "L340...",
      "lat": -27.4698,
      "lon": 153.0251,
      "layer": 0,
      "zoom_level": 340
    },
    "filesystem": {
      "binder": "technical",
      "container": "personal",
      "folder_tags": ["technical", "mcp"],
      "spatial_path": null
    },
    "frontmatter": {},
    "sections": [
      {
        "id": "summary",
        "heading": "Summary",
        "level": 2,
        "content": "..."
      }
    ],
    "body_markdown": "# MCP Protocol\n..."
  }
}
```

## Required Fields

Every exported document must include:

- `doclang_version`
- `document.id`
- `document.canonical_id`
- `document.title`
- `document.source_system`
- `document.source_path`
- `document.tags`
- `document.sections`
- `document.body_markdown`

## Identifier Rules

### `id`

`id` is the concrete exported identity from the current source.

Examples:

- `vault:technical/mcp/protocol.md`
- `appflowy:workspace_123:doc_456`
- `udocs:architecture/overview.md`

### `canonical_id`

`canonical_id` is the stable cross-system identity for merged or mirrored
documents.

Rules:

1. Prefer the vault-relative path for markdown-canonical documents.
2. Prefer the AppFlowy object id for AppFlowy-native documents.
3. If both systems mirror the same document, keep one canonical id and record
   the other ids in metadata.

## Front Matter Normalization

When a source document has YAML front matter, preserve the raw values under
`document.frontmatter`, then normalize the following keys when present:

| Front matter key | Canonical field |
|---|---|
| `title` | `document.title` |
| `status` | `document.status` |
| `type` or `doc_type` | `document.doc_type` |
| `tags` | `document.tags` |
| `aliases` | `document.aliases` |
| `created` or `created_at` | `document.created_at` |
| `updated` or `updated_at` | `document.updated_at` |
| `workspace` | `document.source_workspace` |
| `binder` | `document.filesystem.binder` |
| `container` | `document.filesystem.container` |
| `ucode` | `document.location.ucode` |
| `lat` | `document.location.lat` |
| `lon` | `document.location.lon` |
| `layer` | `document.location.layer` |
| `zoom_level` | `document.location.zoom_level` |

Normalization rules:

1. String lists may be authored as a single string or an array; export as an
   array.
2. Unknown front matter keys stay in `document.frontmatter`.
3. Export does not discard source front matter even if normalized fields exist.

## Wiki Link Rules

Wiki-style links must be extracted into structured form.

Supported patterns:

- `[[Target]]`
- `[[Target|Label]]`
- `[[folder/target]]`

Export shape:

```json
{
  "wiki_links": {
    "outbound": [
      {"target": "Target", "label": null},
      {"target": "folder/target", "label": "Label"}
    ]
  }
}
```

Rules:

1. Keep the raw target, not just a rendered label.
2. Do not resolve links during export.
3. Link resolution belongs to a later transform/indexing phase.

## Location Tagging

Location tagging is first-class in the bridge format.

The canonical location object is:

```json
{
  "label": "Brisbane",
  "ucode": "L340...",
  "lat": -27.4698,
  "lon": 153.0251,
  "layer": 0,
  "zoom_level": 340
}
```

Rules:

1. `ucode` is the preferred spatial identifier when available.
2. `lat` and `lon` are optional but should be exported when derivable.
3. `layer` and `zoom_level` should align with the existing GridUI spatial
   model.
4. Documents may omit `location` entirely if no spatial meaning exists.

## Spatial Filesystem Rules

Some knowledge layouts use folders as spatial or semantic carriers. Export both
semantic and spatial filesystem meaning explicitly.

`document.filesystem` fields:

- `binder`: top-level semantic collection or vault binder
- `container`: personal, shared, public, or other storage domain
- `folder_tags`: folder-derived tags from the relative path
- `spatial_path`: optional path string when folders encode a spatial hierarchy

Examples:

- `technical/mcp/protocol.md` -> `binder=technical`, `folder_tags=[technical,mcp]`
- `places/australia/brisbane/note.md` -> `spatial_path=places/australia/brisbane`

Rules:

1. Folder tags are additive, not authoritative.
2. Spatial meaning in paths must be copied into explicit metadata.
3. Consumers should not need to infer spatial semantics from raw paths alone.

## Section Extraction

Body markdown should be segmented into stable sections.

Each section includes:

- `id`: stable heading slug or synthetic identifier
- `heading`: heading text or `null`
- `level`: heading level or `0` for synthetic blocks
- `content`: markdown content for that section

Rules:

1. Keep section order stable.
2. Preserve original markdown in `body_markdown`.
3. Section extraction is for AI context windows and later transforms, not for
   replacing the source body.

## Source Mapping

### Vault markdown

Primary inputs:

- front matter
- relative filesystem path
- folder-derived tags
- wiki links in markdown body

### AppFlowy

Primary inputs:

- workspace id
- object id
- title
- document type
- best-effort text content

AppFlowy exports may have sparse front matter and should still emit the same
document envelope.

### Canonical docs

Primary inputs:

- repo-relative path
- markdown headings
- optional front matter
- explicit engineering metadata where available

## Minimal Export Contract For UDW-013

The first implementation only needs to guarantee:

1. one document envelope per source file/document
2. normalized core metadata
3. folder-tag extraction
4. front matter preservation
5. wiki-link extraction
6. optional spatial/location object
7. stable section list

## Follow-on Work

This spec is the prerequisite for:

- UDW-014 transform step for AI-efficient structured context
- better AppFlowy/vault document merge rules
- future doc indexing and retrieval pipelines
- wiki graph and spatial browsing features

## Initial Transformer

The first executable transform step is:

- `backend/app/services/doclang_bridge.py`
- `scripts/export_doclang_context.py`

Current output contract:

1. `doclang`: normalized document envelope
2. `ai_context`: compact text block optimized for AI ingestion

The initial exporter targets vault markdown sources and reuses the existing
vault scan/front matter pipeline.