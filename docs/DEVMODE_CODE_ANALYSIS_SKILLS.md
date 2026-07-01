> **Canonical version:** `/Users/fredbook/Code/uDocs/guides/devmode-skills.md`
> This repo copy is kept for local reference; edits should be made in uDocs.

# DevMode Code Analysis Skills

Three new skills for code quality analysis and modularization planning.

## Skills Overview

| Skill ID | Name | Purpose |
|----------|------|---------|
| `duplicate-detector` | Duplicate Code Detector | Find duplicate functions, similar blocks, repeated imports |
| `dead-code-archiver` | Dead Code / Legacy Archiver | Identify unused code, legacy patterns, orphaned imports |
| `modularisation-planner` | Modularisation Planner | Assess large scripts (>1000 lines) for refactoring |

---

## 1. Duplicate Code Detector (`duplicate-detector`)

### Actions
- `scan` — Scan for duplicate code patterns
- `report` — Scan + generate recommendations
- `archive` — Save findings to timestamped JSON report

### Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | string | required | Action to perform |
| `target` | string | "" | Specific directory or file pattern |
| `min_lines` | int | 5 | Minimum lines for duplicate detection |
| `similarity_threshold` | float | 0.85 | Similarity threshold (0.0-1.0) |
| `dry_run` | bool | true | Preview without archiving |

### Detection Types
1. **Exact function duplicates** — Hash-based detection across files
2. **Similar code blocks** — Normalized whitespace comparison
3. **Duplicate imports** — Imports appearing in >3 files
4. **Repeated string literals** — Literals appearing in >3 files

### Example Usage
```bash
# Scan entire workspace
curl -X POST http://localhost:8484/api/skills/duplicate-detector/run \
  -H "Content-Type: application/json" \
  -d '{"action": "scan"}'

# Generate report
curl -X POST http://localhost:8484/api/skills/duplicate-detector/run \
  -d '{"action": "report", "target": "backend/app"}'
```

---

## 2. Dead Code / Legacy Archiver (`dead-code-archiver`)

### Actions
- `scan` — Scan for dead code and legacy patterns
- `report` — Scan + generate recommendations
- `archive` — Save findings to timestamped JSON report

### Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | string | required | Action to perform |
| `target` | string | "" | Specific directory to scan |
| `include_legacy` | bool | true | Include legacy pattern detection |
| `dry_run` | bool | true | Preview without archiving |

### Detection Types
1. **Unused functions** — Functions defined but never called
2. **Orphaned imports** — Imports that are never used
3. **Dead code paths** — Code after return/break/continue
4. **Legacy patterns** — Deprecated APIs and old patterns
5. **Unreferenced files** — Files not imported anywhere

### Legacy Patterns Detected
- `typing_extensions` imports (use `typing` instead)
- `requests` imports (consider `httpx` for async)
- `.format()` calls (use f-strings)
- `@asyncio.coroutine` decorator (use `async def`)
- `yield from` (use async/await)
- Old-style `super()` calls

### Example Usage
```bash
# Scan for dead code
curl -X POST http://localhost:8484/api/skills/dead-code-archiver/run \
  -d '{"action": "scan", "include_legacy": true}'

# Archive findings
curl -X POST http://localhost:8484/api/skills/dead-code-archiver/run \
  -d '{"action": "archive", "dry_run": false}'
```

---

## 3. Modularisation Planner (`modularisation-planner`)

### Actions
- `scan` — Scan for large scripts needing modularization
- `report` — Scan + generate recommendations
- `plan` — Generate detailed extraction plan

### Parameters
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | string | required | Action to perform |
| `target` | string | "" | Specific file or directory |
| `min_lines` | int | 1000 | Minimum lines to analyze |
| `output_format` | string | "json" | Output: "json" or "markdown" |

### Analysis Metrics
1. **Large functions** — Functions >100 lines
2. **Complex functions** — Cyclomatic complexity >10
3. **Missing docstrings** — Functions without documentation
4. **Import clusters** — Modules with >5 imports
5. **Class extraction candidates** — Classes >300 lines

### Priority Score (0-100)
- Large functions: +20 each (max 40)
- Complex functions: +15 each (max 30)
- Missing docstrings: +5 each (max 15)
- Import clusters: +10 each (max 10)
- Class extraction: +10 each (max 10)

### Example Usage
```bash
# Scan for large scripts
curl -X POST http://localhost:8484/api/skills/modularisation-planner/run \
  -d '{"action": "scan"}'

# Generate markdown plan
curl -X POST http://localhost:8484/api/skills/modularisation-planner/run \
  -d '{"action": "plan", "output_format": "markdown"}'
```

---

## Output Locations

- Duplicate reports: `tmp/duplicate_reports/duplicates_{timestamp}.json`
- Dead code archive: `tmp/dead_code_archive/dead_code_{timestamp}.json`

## Integration

All skills follow the `BaseSkill` pattern and are auto-discovered by the registry. They integrate with:
- Skill audit system
- DevMode operation logging
- Confirmation requirements for mutating actions