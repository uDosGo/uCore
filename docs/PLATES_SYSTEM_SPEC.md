# uCore Plates System Specification

> **Version:** 1.0  
> **Status:** Draft  
> **Scope:** Skills, Snacks, MCP Tools, Hivemind Patterns, Variables/Secrets, CSS/USX  
> **Naming:** "Plates" — canonical, versioned, recoverable blueprints (like printing plates)

## 1. Philosophy

A **Plate** in uCore is a **canonical, versioned, recoverable blueprint** for any system component. Plates serve three purposes:

1. **Scaffolding** — Generate new components from a known-good starting point
2. **Validation** — Detect drift between running state and canonical plate
3. **DESTROY/REBUILD** — On corruption/hallucination, salvage key items and restore from plate

## 2. Existing Standards We Leverage

| Domain | Plate Mechanism | Standard |
|--------|----------------|----------|
| **Python Skills** | `BaseSkill` + `SkillMeta` (Pydantic) | Pydantic `BaseModel` for schema enforcement |
| **Python Projects** | **Cookiecutter** — `cookiecutter gh:ucore/skill-plate` | Cookiecutter (de facto Python standard) |
| **MCP Tools** | `input_schema` dicts (JSON Schema) → **OpenAPI/Swagger** | [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0) |
| **MCP Registry** | **OpenAPI/Swagger spec** auto-generated from `TOOL_HANDLERS` | OpenAPI 3.1 + MCP Specification |
| **CSS/USX** | CSS Custom Properties (`--usx-*`, `--pico-*`) | CSS Variables (W3C standard) |
| **Snacks** | `SnackMeta` (Pydantic) | Same pattern as `SkillMeta` |
| **Secrets/Variables** | `.env.example` + `config/*.example.yaml` | 12-Factor App methodology |
| **Hivemind Patterns** | YAML workflow definitions | n8n / Roundtable workflow format |

## 3. Plate Anatomy

Every plate has:

```yaml
# plate.yaml (canonical definition)
plate:
  id: "skill.recover_port_conflict"    # Unique identifier
  version: "1.0.0"                     # SemVer
  domain: "skill"                      # skill | snack | mcp | hivemind | secret | css
  description: "Detect and resolve port conflicts"
  schema:                              # Pydantic/JSON Schema validation
    type: object
    properties:
      port: { type: integer, default: 8484 }
  source: "builtin"                    # builtin | user | community
  checksum: "sha256-..."               # For drift detection
  dependencies: []                     # Other plates this depends on
  destroy:                             # DESTROY/REBUILD protocol
    salvage_keys: ["port", "timeout"]  # What to preserve on corruption
    rebuild_command: "cookiecutter gh:ucore/skill-plate --no-input"
```

## 4. Plate Registry

Plates are stored in `plates/`:

```
plates/
├── README.md
├── destroy/                          # DESTROY/REBUILD plates
│   ├── README.md
│   ├── skill_recover_port_conflict.yaml
│   ├── skill_diagnose_system.yaml
│   └── ...
├── skills/                           # Skill plates
│   ├── skill_plate.py                # Cookiecutter template: skill scaffold
│   └── ...
├── snacks/                           # Snack plates
├── mcp/                              # MCP tool plates
├── hivemind/                         # Hivemind workflow plates
├── secrets/                          # Variable/secret plates
└── css/                              # CSS/USX theme plates
```

## 5. OpenAPI/Swagger MCP Registry

The MCP tool registry (`TOOL_HANDLERS`) auto-generates an **OpenAPI 3.1 spec** at `/api/mcp/openapi.json`:

```yaml
openapi: "3.1.0"
info:
  title: "uCore MCP API"
  version: "1.0.0"
  description: "Auto-generated from TOOL_HANDLERS registry"
servers:
  - url: "http://localhost:8484"
    description: "uCore Backend"
paths:
  /api/mcp/discover:
    get:
      summary: "List all available MCP tools"
      operationId: "handle_mcp_discover"
      responses:
        "200":
          description: "Tool list"
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ToolDefinition"
  /api/mcp/call:
    post:
      summary: "Call an MCP tool"
      operationId: "handle_mcp_call"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/MCPCallRequest"
      responses:
        "200":
          description: "Tool response"
components:
  schemas:
    ToolDefinition:
      type: object
      properties:
        name: { type: string }
        description: { type: string }
        input_schema: { type: object }
    MCPCallRequest:
      type: object
      properties:
        name: { type: string }
        arguments: { type: object }
```

**Benefits:**
- Swagger UI at `/api/mcp/docs` for interactive testing
- Auto-generated client SDKs for any language
- MCP-compatible discovery endpoint
- Versioned API surface for drift detection

## 6. Cookiecutter for Skill Plates

Skill scaffolding uses Cookiecutter:

```bash
# Generate a new skill from the canonical plate
cookiecutter gh:ucore/skill-plate
# Prompts: skill_id, description, category, params...

# Or from a local plate
cookiecutter plates/skills/skill_plate/
```

The Cookiecutter plate template:

```
skill_plate/
├── cookiecutter.json                  # Prompts and defaults
├── {{cookiecutter.skill_id}}/
│   ├── __init__.py
│   ├── {{cookiecutter.skill_id}}.py   # BaseSkill subclass
│   ├── test_{{cookiecutter.skill_id}}.py
│   └── plate.yaml                     # Auto-generated plate definition
└── hooks/
    ├── pre_gen_project.py             # Validate skill_id uniqueness
    └── post_gen_project.py            # Register in registry, run tests
```

## 7. Pydantic BaseModel for Plate Validation

Extend the existing `BaseSkill`/`SkillMeta` pattern for all plates:

```python
from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime


class PlateMeta(BaseModel):
    """Canonical plate metadata — extends SkillMeta pattern."""
    id: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    domain: Literal["skill", "snack", "mcp", "hivemind", "secret", "css"]
    description: str = ""
    schema: dict[str, Any] = {}
    source: Literal["builtin", "user", "community"] = "builtin"
    checksum: str = ""
    dependencies: list[str] = []
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)


class DestroyRebuildConfig(BaseModel):
    """DESTROY/REBUILD protocol configuration."""
    salvage_keys: list[str] = []
    rebuild_command: str = ""
    backup_before_destroy: bool = True
```

## 8. Plate Refresh Engine

Located at `backend/plate_refresh/`, the engine:

1. **Renders** plates with context substitution (`$DATE`, `$VERSION`, etc.)
2. **Validates** output against Pydantic schema
3. **Detects drift** by comparing checksums
4. **Salvages** key state from corrupted instances before rebuild

```python
# Example usage
from plate_refresh.refresh import render_plates, validate_plate

# Render all plates
render_plates({"DATE": "2026-06-30", "VERSION": "1.0.0"})

# Validate a specific plate
report = validate_plate("skill.recover_port_conflict")
if report["drift_detected"]:
    salvage_and_rebuild(report)
```

## 9. DESTROY/REBUILD Protocol

When corruption or hallucination is detected:

```
1. DETECT   → Run integrity checks (mcp_guardrails, skill_audit)
2. SALVAGE  → Extract key state from corrupted instance
              - Skills: meta.id, meta.params, current state from state.py
              - Snacks: snack_id, config values
              - Secrets: variable names (NOT values — re-prompt user)
              - CSS: custom property values
3. BACKUP   → Full file backup to plates/.backups/<domain>/ before destruction
4. ARCHIVE  → Compress essence into MCP-formatted SPOOL record
              (gzip-compressed JSON in ~/.ucore/logs/plate_*.spool.json.gz)
5. DESTROY  → Remove corrupted instance
6. REBUILD  → Materialize from plate with salvaged state
              - Skills: cookiecutter gh:ucore/skill-plate --no-input
              - MCP: regenerate from OpenAPI spec
7. VERIFY   → Run validation checks, report success/failure
```

### ARCHIVE/COMPOST/BACKUP → SPOOL Pipeline

The SPOOL archive is the key innovation that connects DESTROY/REBUILD to
knowledge preservation. When a component is destroyed, its essence is
compressed into a gzip'd JSON record that preserves:

1. **Plate metadata** — id, version, domain, description, checksum
2. **Salvaged state** — keys preserved from corruption (config, params)
3. **Lessons learned** — from `plate.lessons` field (wisdom from failures)
4. **Backup reference** — path to full YAML backup
5. **Rebuild output** — stdout from rebuild command
6. **Schema** — the component's JSON schema

This enables three critical use cases:

| Use Case | How SPOOL Archives Help |
|----------|------------------------|
| **Legacy/archival records** | gzip-compressed JSON is tiny vs .git bloat. A year of archives fits in KB. |
| **Avoid re-developing deprecated skills** | Search spool archives by plate_id to find previous implementations, schemas, and lessons. |
| **Learning from failures** | Each archive includes `lessons[]` — wisdom captured from what went wrong and how it was fixed. |

#### SPOOL Archive Format

```json
{
  "event": "plate.destroy",
  "timestamp": "2026-06-30T22:00:00+00:00",
  "plate": {
    "id": "skill.recover_port_conflict",
    "version": "1.0.0",
    "domain": "skill",
    "description": "Detect and resolve port conflicts",
    "source": "builtin",
    "checksum": "sha256-...",
    "dependencies": []
  },
  "salvaged": {
    "port": 8484,
    "timeout": 30
  },
  "lessons": [
    "Always check port 8484 before starting backend",
    "Use SO_REUSEADDR to avoid EADDRINUSE on restart"
  ],
  "backup": "plates/.backups/skill/skill.recover_port_conflict_20260630_220000.yaml",
  "rebuild_output": "Rebuilding 8484 for ucore-backend... OK",
  "errors": [],
  "schema": {
    "type": "object",
    "properties": {
      "port": { "type": "integer", "default": 8484 }
    }
  }
}
```

#### CLI Commands

```bash
# List all SPOOL archives
python -m plate_refresh.refresh --spool-list

# Filter by domain
python -m plate_refresh.refresh --spool-list --spool-domain skill

# Read a specific archive
python -m plate_refresh.refresh --spool-read ~/.ucore/logs/plate_skill.recover_port_conflict_20260630.spool.json.gz
```

#### Plate Configuration

Each plate can configure its SPOOL behavior:

```yaml
plate:
  id: "skill.recover_port_conflict"
  version: "1.0.0"
  domain: "skill"
  lessons:
    - "Always check port 8484 before starting backend"
    - "Use SO_REUSEADDR to avoid EADDRINUSE on restart"
  destroy:
    salvage_keys: ["port", "timeout"]
    rebuild_command: "echo Rebuilding $port for $service_name"
    backup_before_destroy: true
    spool_archive:
      enabled: true
      spool_dir: "~/.ucore/logs"
      compress_metadata: true
      include_source: false
      include_lessons: true
      max_spool_age_days: 365
```


### Agent Instructions (for .clinerules)

```
## Plates System Rules

1. Before modifying any component, check if a plate exists in `plates/`
2. If no plate exists, create one before making changes
3. On detecting corruption: run DESTROY/REBUILD protocol
4. After successful modification, promote to plate:
   - `plates/skills/` for new skills (via cookiecutter)
   - `plates/mcp/` for new MCP tools
   - Update version number on changes
5. Never delete a plate — archive with version suffix
```

## 10. Promotion Workflow

Users can promote working modifications to plates:

```
Working modification → Validate → Create/Update plate → Register in registry
```

```bash
# CLI example
ucore plate promote --from backend/app/skills/builtin/my_skill.py \
                    --to plates/skills/my_skill.yaml \
                    --version 1.1.0
```

## 11. Drift Detection

The `skill_audit` skill compares running instances against plates:

```python
report = await run_skill_by_id("skill_audit", scope="all")
# Returns:
#   - matched: components that match their plate
#   - drifted: components that differ (with diff)
#   - missing: plates with no running instance
#   - orphaned: instances with no plate
```

## 12. Integration Points

| System | Plate Role |
|--------|-----------|
| `backend/app/skills/registry.py` | Auto-discovers skills; plates define canonical set |
| `backend/app/skills/state.py` | Persists skill state; plates define default state shape |
| `backend/app/api/mcp_guardrails.py` | Validates MCP layer against expected plate |
| `backend/plate_refresh/refresh.py` | Renders plates to output |
| `plates/destroy/` | DESTROY/REBUILD recovery plates |
| `backend/app/api/mcp.py` | Auto-generates OpenAPI spec from TOOL_HANDLERS |
| `.clinerules` | Agent instructions for plate workflow |

## 13. Future Work

- [ ] Plate version migration (auto-upgrade on version mismatch)
- [ ] Community plate repository (shareable via git submodule)
- [ ] Plate diff viewer (visual comparison of drift)
- [ ] Auto-promote on successful test pass
- [ ] OpenAPI/Swagger UI at `/api/mcp/docs`
- [ ] Cookiecutter plate for `gh:ucore/skill-plate`
- [ ] Pydantic `PlateMeta` → `BaseSkill` auto-generation
