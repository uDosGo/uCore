# Vendor — Distribution Packages for uCore

This directory contains distribution packages and source definitions
for the uCore ecosystem. It supports the DistributionSystem and
PackageManager services for install, update, and repair operations.

## Structure

```
vendor/
├── README.md              # This file
├── lock.yaml              # Locked refs for deterministic installs
├── dist/                  # Distribution packages
│   ├── ucore-core/        # Core backend distribution
│   ├── ucore-frontend/    # Frontend distribution
│   └── ucore-plates/      # Canonical plates distribution
└── sources.yaml           # Source definitions (GitHub, npm, pip)
```

## Distribution Packages

| Package | Description | Source |
|---------|-------------|--------|
| `ucore-core` | Core backend services | GitHub: uDosGo/uCore |
| `ucore-frontend` | Frontend UI | GitHub: uDosGo/uCore |
| `ucore-plates` | Canonical plates | GitHub: uDosGo/uCore |

## Usage

The DistributionSystem (`backend/app/services/distribution_system/`)
uses this directory to:

1. **Install** — Pull packages from GitHub and extract to vendor/dist/
2. **Update** — Check for newer versions and upgrade
3. **Repair** — Reinstall corrupted packages from cached distributions
4. **Destroy** — Remove packages with SPOOL archiving

## Source Definitions

See `sources.yaml` for the canonical source definitions including
GitHub repository URLs, release tags, and checksums.

## Lock And Sync

For consistent one-click installs, vendor modules are locked in `lock.yaml`
and synced via `scripts/vendor_sync.sh`.

Examples:

```bash
# Refresh lock from sources and validate consistency
./scripts/vendor_sync.sh --refresh-lock --check

# Install locked pip modules (snackmachine, udos-agents, etc.)
./scripts/vendor_sync.sh --install-python --check
```
