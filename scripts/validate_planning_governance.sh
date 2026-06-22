#!/usr/bin/env bash
set -euo pipefail

# Enforce planning governance:
# - Active planning is allowed only in:
#   - .tasker/UNIFIED_DEV_TASK_WORKFLOW.md
#   - .tasker/phases/*.md
#   - .tasker/backlog/*.md
# - Archived planning is allowed under docs/archive/plans/
# - Exception tag for temporary active task notes elsewhere:
#   - <!-- planning-governance: allow-active-tasks -->
# - Disallowed elsewhere: unchecked checklist tasks and task/backlog tables.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

allowed_file() {
  local path="$1"
  [[ "$path" == ".tasker/UNIFIED_DEV_TASK_WORKFLOW.md" ]] && return 0
  [[ "$path" == .tasker/phases/* ]] && return 0
  [[ "$path" == .tasker/backlog/* ]] && return 0
  [[ "$path" == docs/archive/plans/* ]] && return 0
  return 1
}

violations=0

while IFS= read -r file; do
  if allowed_file "$file"; then
    continue
  fi

  if grep -qiF '<!-- planning-governance: allow-active-tasks -->' "$file"; then
    echo "[ALLOW] Exception tag found in $file"
    continue
  fi

  found=0

  if grep -nE '^[[:space:]]*[-*][[:space:]]+\[[[:space:]]\][[:space:]]+' "$file" >/tmp/ucore_plan_check_1.txt 2>/dev/null; then
    if [[ -s /tmp/ucore_plan_check_1.txt ]]; then
      found=1
      echo "[FAIL] Unchecked task checklist found in $file"
      cat /tmp/ucore_plan_check_1.txt
    fi
  fi

  if grep -nE '^\|[[:space:]]*Task[[:space:]]*\|[[:space:]]*(Status|Priority)[[:space:]]*\|[[:space:]]*Description[[:space:]]*\|' "$file" >/tmp/ucore_plan_check_2.txt 2>/dev/null; then
    if [[ -s /tmp/ucore_plan_check_2.txt ]]; then
      found=1
      echo "[FAIL] Task table header found in $file"
      cat /tmp/ucore_plan_check_2.txt
    fi
  fi

  if [[ "$found" -eq 1 ]]; then
    violations=$((violations + 1))
  fi
done < <(git ls-files '*.md')

rm -f /tmp/ucore_plan_check_1.txt /tmp/ucore_plan_check_2.txt

if [[ "$violations" -gt 0 ]]; then
  echo "---"
  echo "Planning governance check failed in $violations file(s)."
  echo "Active tasks are only allowed in .tasker/UNIFIED_DEV_TASK_WORKFLOW.md, .tasker/phases/, and .tasker/backlog/."
  exit 1
fi

echo "Planning governance check passed."
