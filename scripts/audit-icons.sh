#!/bin/bash
# audit-icons.sh — USX Icon System Audit Script
# Usage: ./audit-icons.sh [path/to/surface]
# If no path provided, audits entire frontend/src directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default path
AUDIT_PATH="${1:-${UCORE_ROOT:-$HOME/Code/uCore}/frontend/src}"

echo -e "${BLUE}🔍 USX Icon System Audit${NC}"
echo "Auditing: $AUDIT_PATH"
echo ""

# Track violations
VIOLATIONS=0
WARNINGS=0

# Function to print violations
print_violation() {
  echo -e "${RED}❌ $1${NC}"
  VIOLATIONS=$((VIOLATIONS + 1))
}

# Function to print warnings
print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
  WARNINGS=$((WARNINGS + 1))
}

# Function to print success
print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

# Function to print section header
print_section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ─── 1. Lucide Icons Check ─────────────────────────────────────────
print_section "1. Lucide Icons (Should be removed)"

LUCIDE_USAGE=$(grep -rn "lucide\|Lucide" "$AUDIT_PATH" --include="*.jsx" --include="*.tsx" --include="*.ts" --include="*.css" 2>/dev/null | \
  grep -v "node_modules" | \
  grep -v "legacy" || true)

if [ -n "$LUCIDE_USAGE" ]; then
  echo "$LUCIDE_USAGE" | while read -r line; do
    print_violation "$line"
  done
else
  print_success "No Lucide icons found"
fi

# ─── 2. Hardcoded Icon Strings Check ───────────────────────────────
print_section "2. Hardcoded Icon Strings (Should use Icon component)"

HARDCODED_ICONS=$(grep -rn "material-icons" "$AUDIT_PATH" --include="*.jsx" --include="*.tsx" --include="*.ts" 2>/dev/null | \
  grep -v "Icon" | \
  grep -v "node_modules" | \
  grep -v "grid-icon-mapping" || true)

if [ -n "$HARDCODED_ICONS" ]; then
  echo "$HARDCODED_ICONS" | while read -r line; do
    print_violation "$line"
  done
else
  print_success "No hardcoded icon strings found"
fi

# ─── 3. Icon Size Consistency Check ────────────────────────────────
print_section "3. Icon Size Consistency (Should use sm/md/lg/xl)"

ICON_SIZES=$(grep -rn "fontSize\|style.*fontSize" "$AUDIT_PATH" --include="*.jsx" --include="*.tsx" --include="*.ts" 2>/dev/null | \
  grep -v "Icon" | \
  grep -v "node_modules" | \
  grep -v "grid-icon-mapping" || true)

if [ -n "$ICON_SIZES" ]; then
  print_warning "Found hardcoded icon sizes (should use Icon component with size prop)"
  echo "$ICON_SIZES" | head -5 | while read -r line; do
    echo "  $line"
  done
else
  print_success "Icon sizes are consistent"
fi

# ─── 4. Google Fonts Check ─────────────────────────────────────────
print_section "4. Google Fonts Import"

GOOGLE_FONTS=$(grep -rn "fonts.googleapis.com" "$AUDIT_PATH" --include="*.html" --include="*.tsx" --include="*.ts" 2>/dev/null | \
  grep -v "node_modules" || true)

if [ -n "$GOOGLE_FONTS" ]; then
  print_success "Google Fonts imported"
  echo "$GOOGLE_FONTS" | head -3 | while read -r line; do
    echo "  $line"
  done
else
  print_warning "Google Fonts not found (should be imported in index.html or main.tsx)"
fi

# ─── 5. Icon Component Check ───────────────────────────────────────
print_section "5. Icon Component Usage"

ICON_COMPONENT=$(grep -rn "from.*Icon" "$AUDIT_PATH" --include="*.jsx" --include="*.tsx" --include="*.ts" 2>/dev/null | \
  grep -v "node_modules" | \
  grep -v "legacy" || true)

if [ -n "$ICON_COMPONENT" ]; then
  print_success "Icon component is being used"
  echo "$ICON_COMPONENT" | head -3 | while read -r line; do
    echo "  $line"
  done
else
  print_warning "Icon component not found (should be imported from @/components/Icon)"
fi

# ─── 6. Grid Icon Mapping Check ────────────────────────────────────
print_section "6. Grid Icon Mapping"

GRID_MAPPING=$(grep -rn "grid-icon-mapping" "$AUDIT_PATH" --include="*.jsx" --include="*.tsx" --include="*.ts" 2>/dev/null | \
  grep -v "node_modules" | \
  grep -v "legacy" || true)

if [ -n "$GRID_MAPPING" ]; then
  print_success "Grid icon mapping is being used"
else
  print_warning "Grid icon mapping not found (should be imported from @/lib/grid-icon-mapping)"
fi

# ─── 7. File Count ─────────────────────────────────────────────────
print_section "7. Audit Summary"

JSX_COUNT=$(find "$AUDIT_PATH" -name "*.jsx" -o -name "*.tsx" | wc -l | tr -d ' ')
TS_COUNT=$(find "$AUDIT_PATH" -name "*.ts" | wc -l | tr -d ' ')
CSS_COUNT=$(find "$AUDIT_PATH" -name "*.css" | wc -l | tr -d ' ')

echo "Files audited:"
echo "  JSX/TSX files: $JSX_COUNT"
echo "  TypeScript files: $TS_COUNT"
echo "  CSS files: $CSS_COUNT"

# ─── Final Report ───────────────────────────────────────────────────
echo ""
print_section "FINAL REPORT"

if [ $VIOLATIONS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  print_success "All checks passed! Surface is compliant with USX Icon System."
  exit 0
elif [ $VIOLATIONS -eq 0 ]; then
  print_warning "No violations found, but there are $WARNINGS warnings to review."
  exit 0
else
  print_violation "Found $VIOLATIONS violations and $WARNINGS warnings."
  echo ""
  echo "Fixes needed:"
  echo "  1. Remove all Lucide icon imports"
  echo "  2. Replace hardcoded icon strings with Icon component"
  echo "  3. Use size prop (sm/md/lg/xl) instead of inline fontSize"
  echo "  4. Add Google Fonts import to index.html"
  echo "  5. Import Icon component from @/components/Icon"
  echo "  6. Use grid-icon-mapping for icon names"
  exit 1
fi