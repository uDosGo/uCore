#!/usr/bin/env bash
# =============================================================================
# generate_surface.sh — Surface Plate Generator
# =============================================================================
# Generates a new Vue surface from a Cookiecutter template.
#
# Usage:
#   ./plates/surface/generate_surface.sh <surface_id> <template_type>
#
# Template types:
#   basic     — Simple surface with header + content area
#   tabbed    — Tabbed surface with multiple panels (Developer, Server, System)
#   chat      — Chat surface with messages + input (AssistUI)
#   grid      — Grid/canvas surface (UCode)
#
# Example:
#   ./plates/surface/generate_surface.sh myfeature tabbed
#
# This will create:
#   frontend-vue/src/surfaces/myfeature/MyfeatureSurface.vue
#   frontend-vue/src/surfaces/myfeature/panels/Panel1.vue
#   frontend-vue/src/surfaces/myfeature/panels/Panel2.vue
#   frontend-vue/src/surfaces/myfeature/panels/Panel3.vue
#   frontend-vue/src/stores/myfeature.ts
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATES_DIR="$SCRIPT_DIR"
FRONTEND_VUE_DIR="$(cd "$SCRIPT_DIR/../../frontend-vue" && pwd)"

SURFACE_ID="${1:-}"
TEMPLATE_TYPE="${2:-}"

if [ -z "$SURFACE_ID" ] || [ -z "$TEMPLATE_TYPE" ]; then
  echo "Usage: $0 <surface_id> <template_type>"
  echo ""
  echo "Template types: basic, tabbed, chat, grid"
  echo ""
  echo "Examples:"
  echo "  $0 myfeature basic"
  echo "  $0 developer tabbed"
  echo "  $0 assistant chat"
  echo "  $0 ucode grid"
  exit 1
fi

TEMPLATE_DIR="$PLATES_DIR/surface-$TEMPLATE_TYPE"

if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "Error: Unknown template type '$TEMPLATE_TYPE'"
  echo "Available: basic, tabbed, chat, grid"
  exit 1
fi

SURFACE_DIR="$FRONTEND_VUE_DIR/src/surfaces/$SURFACE_ID"
STORE_FILE="$FRONTEND_VUE_DIR/src/stores/$SURFACE_ID.ts"

if [ -d "$SURFACE_DIR" ]; then
  echo "Warning: Surface directory already exists: $SURFACE_DIR"
  echo "Overwrite? [y/N]"
  read -r CONFIRM
  if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Aborted."
    exit 1
  fi
fi

echo "=== Generating surface: $SURFACE_ID ($TEMPLATE_TYPE) ==="

# Create surface directory
mkdir -p "$SURFACE_DIR/panels"

# Capitalize surface_id for component names
CAP_ID="$(echo "$SURFACE_ID" | sed 's/^\(.\)/\U\1/')"

# Copy and process template files
for template_file in "$TEMPLATE_DIR/{{cookiecutter.surface_id}}"/*; do
  filename=$(basename "$template_file")
  # Replace {{cookiecutter.surface_id}} with actual surface_id
  output_name=$(echo "$filename" | sed "s/{{cookiecutter.surface_id}}/$SURFACE_ID/g")
  output_path="$SURFACE_DIR/$output_name"

  if [ -f "$template_file" ]; then
    sed \
      -e "s/{{cookiecutter.surface_id}}/$SURFACE_ID/g" \
      -e "s/{{cookiecutter.surface_title}}/$(echo "$SURFACE_ID" | sed 's/-/ /g' | sed 's/\b\(.\)/\U\1/g')/g" \
      -e "s/{{cookiecutter.surface_description}}/Description of $SURFACE_ID/g" \
      -e "s/{{cookiecutter.surface_icon}}/extension/g" \
      -e "s/{{cookiecutter.surface_color}}/#a855f7/g" \
      -e "s/{{cookiecutter.route_path}}/\/$SURFACE_ID/g" \
      -e "s/{{cookiecutter.dev_only}}/false/g" \
      -e "s/{{cookiecutter.author}}/uCore/g" \
      -e "s/{{cookiecutter.surface_id|capitalize}}/$CAP_ID/g" \
      "$template_file" > "$output_path"
    echo "  Created: $output_path"
  fi
done

# Copy panel templates
for panel_file in "$TEMPLATE_DIR/{{cookiecutter.surface_id}}/panels"/*; do
  if [ -f "$panel_file" ]; then
    filename=$(basename "$panel_file")
    output_path="$SURFACE_DIR/panels/$filename"
    sed \
      -e "s/{{cookiecutter.surface_id}}/$SURFACE_ID/g" \
      -e "s/{{cookiecutter.surface_id|capitalize}}/$CAP_ID/g" \
      "$panel_file" > "$output_path"
    echo "  Created: $output_path"
  fi
done

# Generate Pinia store
if [ ! -f "$STORE_FILE" ]; then
  cat > "$STORE_FILE" << STOREEOF
/**
 * @module stores/$SURFACE_ID
 * @description $CAP_ID surface state management.
 * Generated from surface-$TEMPLATE_TYPE plate template.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const use${CAP_ID}Store = defineStore('$SURFACE_ID', () => {
  const activeTab = ref<string>('panel1')
  const loading = ref(false)
  const messages = ref<Array<{ role: string; content: string }>>([])

  function setTab(tab: string) {
    activeTab.value = tab
  }

  async function sendMessage(content: string) {
    messages.value.push({ role: 'user', content })
    loading.value = true
    // TODO: Wire to backend API
    setTimeout(() => {
      messages.value.push({ role: 'assistant', content: 'Response placeholder' })
      loading.value = false
    }, 500)
  }

  return {
    activeTab,
    loading,
    messages,
    setTab,
    sendMessage,
  }
})
STOREEOF
  echo "  Created: $STORE_FILE"
else
  echo "  Skipped store (already exists): $STORE_FILE"
fi

echo ""
echo "=== Done! ==="
echo ""
echo "Next steps:"
echo "  1. Add route to frontend-vue/src/router/index.ts"
echo "  2. Add card to frontend-vue/src/surfaces/dashboard/DashboardSurface.vue"
echo "  3. Customize panels in $SURFACE_DIR/panels/"
echo "  4. Customize store in $STORE_FILE"
