#!/bin/bash
# vendor_sync.sh — Lock, validate, and install external vendor modules.
#
# Usage:
#   ./scripts/vendor_sync.sh --check
#   ./scripts/vendor_sync.sh --refresh-lock --check
#   ./scripts/vendor_sync.sh --refresh-lock --install-python --check

set -euo pipefail

UCORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCES_FILE="$UCORE_ROOT/vendor/sources.yaml"
LOCK_FILE="$UCORE_ROOT/vendor/lock.yaml"

REFRESH_LOCK=false
CHECK_ONLY=false
INSTALL_PYTHON=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --refresh-lock)
      REFRESH_LOCK=true
      shift
      ;;
    --check)
      CHECK_ONLY=true
      shift
      ;;
    --install-python)
      INSTALL_PYTHON=true
      shift
      ;;
    --help)
      cat <<EOF
Vendor module sync for uCore

Options:
  --refresh-lock   Re-resolve refs and rewrite vendor/lock.yaml
  --check          Validate lock and source consistency
  --install-python Install/upgrade locked pip vendor modules
  --help           Show this help
EOF
      exit 0
      ;;
    *)
      err "Unknown argument: $1"
      exit 2
      ;;
  esac
done

if [[ ! -f "$SOURCES_FILE" ]]; then
  err "Missing sources file: $SOURCES_FILE"
  exit 1
fi

if ! python - <<'PY' >/dev/null 2>&1
import yaml
PY
then
  err "PyYAML is required. Activate backend venv and install dependencies first."
  exit 1
fi

if [[ "$REFRESH_LOCK" == "true" ]]; then
  info "Refreshing vendor lock from sources..."
  export UCORE_ROOT
  python - <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import yaml

root = Path(os.environ["UCORE_ROOT"])
sources_file = root / "vendor" / "sources.yaml"
lock_file = root / "vendor" / "lock.yaml"

with sources_file.open("r", encoding="utf-8") as f:
    sources = (yaml.safe_load(f) or {}).get("sources", {})

modules: dict[str, dict[str, str]] = {}

for name in sorted(sources):
    src = sources[name] or {}
    module = {
        "type": str(src.get("type", "")),
        "url": str(src.get("url", "")),
        "ref": str(src.get("ref", "main")),
    }
    subpath = str(src.get("subpath", ""))
    if subpath:
        module["subpath"] = subpath

    resolved_ref = ""
    url = module["url"]
    ref = module["ref"]
    if url and url.startswith("https://"):
        try:
            out = subprocess.check_output(
                ["git", "ls-remote", url, ref],
                text=True,
                timeout=20,
            ).strip()
            if out:
                resolved_ref = out.split()[0]
        except Exception:
            resolved_ref = ""

    if not resolved_ref and len(ref) == 40:
        resolved_ref = ref

    if resolved_ref:
        module["resolved_ref"] = resolved_ref

    modules[name] = module

lock = {
    "version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "modules": modules,
}

with lock_file.open("w", encoding="utf-8") as f:
    yaml.safe_dump(lock, f, sort_keys=True)

print(f"Wrote lock: {lock_file}")
PY
  ok "Vendor lock refreshed"
fi

if [[ ! -f "$LOCK_FILE" ]]; then
  err "Missing lock file: $LOCK_FILE"
  err "Run: ./scripts/vendor_sync.sh --refresh-lock"
  exit 1
fi

if [[ "$CHECK_ONLY" == "true" || "$REFRESH_LOCK" == "true" ]]; then
  info "Validating lock consistency..."
  export UCORE_ROOT
  python - <<'PY'
from __future__ import annotations

from pathlib import Path
import os
import sys
import yaml

root = Path(os.environ["UCORE_ROOT"])
sources_file = root / "vendor" / "sources.yaml"
lock_file = root / "vendor" / "lock.yaml"

with sources_file.open("r", encoding="utf-8") as f:
    sources = (yaml.safe_load(f) or {}).get("sources", {})
with lock_file.open("r", encoding="utf-8") as f:
    lock = (yaml.safe_load(f) or {}).get("modules", {})

errors: list[str] = []
for name, src in sorted(sources.items()):
    if name not in lock:
        errors.append(f"missing module in lock: {name}")
        continue
    lm = lock[name] or {}
    for key in ("type", "url", "ref"):
        if str(src.get(key, "")) != str(lm.get(key, "")):
            errors.append(
                f"{name}: mismatch for {key} (sources={src.get(key)} lock={lm.get(key)})"
            )

for name in sorted(lock):
    if name not in sources:
        errors.append(f"stale module in lock: {name}")

if errors:
    print("Lock validation failed:")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("Lock validation passed")
PY
  ok "Vendor lock is consistent"
fi

if [[ "$INSTALL_PYTHON" == "true" ]]; then
  info "Installing locked pip vendor modules..."

  export UCORE_ROOT
  while IFS='|' read -r pkg_name pkg_url pkg_ref; do
    info "Installing $pkg_name from $pkg_ref"
    pip install --quiet --upgrade "$pkg_name @ git+$pkg_url@$pkg_ref" 2>&1 | tail -1
    ok "Installed $pkg_name"
  done < <(python - <<'PY'
from __future__ import annotations

from pathlib import Path
import os
import yaml

root = Path(os.environ["UCORE_ROOT"])
lock_file = root / "vendor" / "lock.yaml"

with lock_file.open("r", encoding="utf-8") as f:
  modules = (yaml.safe_load(f) or {}).get("modules", {})

for name in sorted(modules):
  mod = modules[name] or {}
  if mod.get("type") != "pip":
    continue
  url = str(mod.get("url", ""))
  if "github.com/uDosGo/" not in url:
    continue
  ref = str(mod.get("resolved_ref") or mod.get("ref") or "")
  if not url or not ref:
    continue
  print(f"{name}|{url}|{ref}")
PY
  )
fi

ok "Vendor sync complete"
