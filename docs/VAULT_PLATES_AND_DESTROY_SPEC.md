# Vault Plates & Enhanced DESTROY/REBUILD Specification

> **Version:** 2.0  
> **Status:** Active  
> **Scope:** Vault topology, vault seed plates, transport pipeline, vault discovery, interactive DESTROY, distribution alignment

## 1. Philosophy

The DESTROY/REBUILD protocol must be able to:
1. **Discover** all user data across vault layers (User, Shared, Global, Code, Public)
2. **Dry-run** identify everything before any destructive action
3. **Offer choices** — Destroy & Rebuild, Destroy User Data Only, Destroy Installation & Data
4. **Spool** out archives/backups for later recovery
5. **Break off Nuggets** for reuse in another place/time/context
6. **Rebuild** from distribution packages (GitHub uCode/uCore)

## 2. Vault Topology

From `vault_file_discovery.py` and `skill_vault_discovery.py`:

| Layer | Path | Purpose | Permissions | Plate |
|-------|------|---------|-------------|-------|
| **user** | `~/Vault/` | Personal vault (one per user) | Read/Write | `vault.user_vault_seed` |
| **shared** | `~/Shared/` | Shared vaults (team workspaces) | Read/Write (permission check) | `vault.shared_workspace_seed` |
| **global** | `~/Public/global-knowledge/` | Global knowledge bank | Read-only | `vault.global_knowledge_seed` |
| **code** | `~/Code/` | Dev repos (uCore, uDocs, etc.) | Read/Write (dev) | (no plate — git-managed) |
| **public** | `~/Public/doc-sites/` | Published doc sites | Publish-only | `vault.public_publishing_framework` |

### Additional Operational Paths

| Path | Purpose | Plate |
|------|---------|-------|
| `~/Public/#transport/` | File transport pipeline (incoming/queue/outgoing/processed/failed) | `vault.transport_pipeline` |
| `~/Public/learning/` | Learning resources and tutorials | (ad-hoc) |
| `~/.ucore/` | uCore config, logs, indices | (managed by system) |

## 3. Vault Plates

Plate domain: `vault` (added to PlateMeta domain Literal)

### 3.1 User Vault Seed Plate — `vault.user_vault_seed`

**File:** `plates/vault/user_vault_seed.yaml` (v2.0.0)

Mirrors the real on-disk `~/Vault/` structure with 15 directories:

| Category | Directories |
|----------|-------------|
| **Operational** | `@inbox/` (pending/processed/failed), `@groovebox/` (creative workspace) |
| **Core Knowledge** | `knowledge/` (concepts/insights/research), `binders/` (active/completed/on-hold/templates), `missions/` (active/completed/templates), `tasks/`, `daily/`, `journals/` |
| **People & Agents** | `people/`, `agents/` |
| **Assets** | `attachments/`, `scripts/`, `security/` |
| **Templates & Dev** | `templates/`, `dev/` |

### 3.2 Shared Workspace Vault Plate — `vault.shared_workspace_seed`

**File:** `plates/vault/shared_workspace_seed.yaml` (v1.0.0)

Template-based structure for team workspaces under `~/Shared/`:

```
{workspace_name}/
├── Projects/
├── Knowledge/
├── Assets/
└── Archive/
```

### 3.3 Public Publishing Framework Plate — `vault.public_publishing_framework`

**File:** `plates/vault/public_publishing_framework.yaml` (v1.0.0)

Template-based structure for published doc sites under `~/Public/doc-sites/`:

```
{site_name}/
├── docs/
├── assets/
└── _config.yml
```

### 3.4 Global Knowledge Seed Plate — `vault.global_knowledge_seed`

**File:** `plates/vault/global_knowledge_seed.yaml` (v1.0.0)

Read-only reference vault under `~/Public/global-knowledge/` with 18 directories:

| Category | Directories |
|----------|-------------|
| **Life Domains** | water, fire, shelter, food, medical, skills, survival, wellbeing, community, communication, tech, making, reference, navigation, learning |
| **System** | categories, contributor, bin |

### 3.5 Transport Pipeline Plate — `vault.transport_pipeline`

**File:** `plates/vault/transport_pipeline.yaml` (v1.0.0)

Operational file staging pipeline under `~/Public/#transport/`:

```
incoming/  →  queue/  →  processing  →  outgoing/  →  delivered
                ↓                          ↓
           failed/                    processed/
```

## 4. Vault Discovery Skill

**File:** `backend/app/skills/builtin/skill_vault_discovery.py`

`VaultDiscoverySkill(BaseSkill)` that:
1. Scans all 5 vault layers (user, shared, global, code, public)
2. Reports file counts, sizes, extensions, and structure per layer
3. Identifies uCore-specific data (configs, logs, plates, spool archives)
4. Dry-run mode (default) for safe identification
5. Nugget extraction — breaks off reusable components as `.nugget.json` manifests

### API

```python
# Dry-run: identify everything
result = await vault_discovery_skill.run(dry_run=True)

# Full scan with Nugget extraction
result = await vault_discovery_skill.run(
    dry_run=False,
    extract_nuggets=True,
    nugget_output_dir="~/Nuggets/"
)
```

### Output

```json
{
  "vaults": {
    "user": { "path": "~/Vault/", "files": 42, "size_bytes": 1048576 },
    "shared": { "path": "~/Shared/", "files": 156, "size_bytes": 5242880 },
    "global": { "path": "~/Public/global-knowledge/", "files": 89, "size_bytes": 2097152 },
    "code": { "path": "~/Code/", "files": 1200, "size_bytes": 104857600 },
    "public": { "path": "~/Public/doc-sites/", "files": 12, "size_bytes": 524288 }
  },
  "ucore_data": {
    "config": { "path": "~/.ucore/", "files": 8 },
    "logs": { "path": "~/.ucore/logs/", "files": 15 },
    "plates": { "path": "plates/", "files": 6 },
    "spool_archives": { "path": "~/.ucore/logs/", "count": 2 }
  },
  "nuggets": [
    { "id": "nugget.vault.user.001", "source": "~/Vault/Knowledge/", "files": 5 }
  ],
  "total_files": 1499,
  "total_size_bytes": 113246208,
  "dry_run": true
}
```

## 5. Enhanced DESTROY Interactive Options

When DESTROY is invoked, the user is presented with options:

```
╔══════════════════════════════════════════════════════╗
║           uCore DESTROY/REBUILD UTILITY              ║
╚══════════════════════════════════════════════════════╝

Running vault discovery (dry-run)...
  Found 1499 files across 5 vault layers
  uCore data: 8 config files, 15 logs, 6 plates, 2 spool archives

Select an option:

  [1] Dry-run only (identify everything, no changes)
  [2] Destroy & Rebuild (reset corrupted components, keep user data)
  [3] Destroy User Data Only (remove ~/Vault/, keep installation)
  [4] Destroy Installation & Data (complete uninstall)
  [5] Break off Nuggets (extract reusable components, then rebuild)
  [6] Cancel

Enter choice [1-6]:
```

### Option Details

| Option | Action |
|--------|--------|
| **1. Dry-run** | Run vault discovery, report findings, no changes |
| **2. Destroy & Rebuild** | Run DESTROY/REBUILD protocol on corrupted plates, keep user vault data intact |
| **3. Destroy User Data** | Backup ~/Vault/ to SPOOL, remove ~/Vault/ contents, keep installation |
| **4. Destroy All** | Full uninstall: remove ~/Vault/, ~/.ucore/, plates/, stop services |
| **5. Nuggets** | Extract reusable components from vaults as Nuggets, then optionally rebuild |
| **6. Cancel** | Exit without changes |

## 6. Distribution & Packaging Alignment

### Existing Systems

| System | Location | Status |
|--------|----------|--------|
| **DistributionSystem** | `backend/app/services/distribution_system/distribution_system.py` | ✅ Implemented |
| **PackageManager** | `backend/app/services/distribution_system/package_manager.py` | ✅ Implemented |
| **install-root.sh** | `scripts/install-root.sh` | Sets UDOS_ROOT env var |
| **ucore_startup.sh** | `scripts/ucore_startup.sh` | Starts services at login |

### Vendor Structure

```
vendor/
├── README.md
├── dist/                    # Distribution packages
│   ├── ucore-core/          # Core backend
│   ├── ucore-frontend/      # Frontend
│   └── ucore-plates/        # Canonical plates
└── sources.yaml             # Source definitions (GitHub, npm, pip)
```

### Source Definitions

4 sources in `vendor/sources.yaml`, all pointing to `github.com/uDosGo/uCore.git`:
- `ucore-core` — backend/
- `ucore-frontend` — frontend/
- `ucore-plates` — plates/
- `ucore-vendor` — vendor/

## 7. Implementation Status

### Phase 1: Vault Plates ✅ Complete
- [x] Add "vault" domain to PlateMeta domain Literal
- [x] Create user vault seed plate (v2.0.0 — 15 directories matching real ~/Vault/)
- [x] Create shared workspace vault plate
- [x] Create public publishing framework plate
- [x] Create global knowledge seed plate (new — 18 directories)
- [x] Create transport pipeline plate (new — 5-stage pipeline)

### Phase 2: Vault Discovery Skill ✅ Complete
- [x] Create vault_discovery skill (BaseSkill subclass)
- [x] Implement dry-run mode
- [x] Implement Nugget extraction
- [x] Integrate with vault_file_discovery.py

### Phase 3: Enhanced DESTROY CLI ✅ Complete
- [x] Add interactive menu to plate_refresh CLI
- [x] Implement all 6 DESTROY options
- [x] Wire SPOOL archiving for each option
- [x] Add confirmation prompts

### Phase 4: Distribution Alignment ✅ Complete
- [x] Create vendor/ directory structure
- [x] Wire DistributionSystem to GitHub pulls
- [x] Wire PackageManager to plate system
- [x] Create install/update/repair CLI commands

### Phase 5: Verification & Monitoring ✅ Complete
- [x] Create verification engine (95% pass rate, security, dogfooding)
- [x] Create monitoring system (usage tracking, audit trail, health checks)
- [x] Wire --verify and --promote flags to refresh.py CLI
- [x] Wire --monitor and --audit flags to refresh.py CLI
