#!/bin/bash
# audit-fonts.sh — USX Font Standards Audit Script
# Usage: ./audit-fonts.sh [path/to/surface]
# If no path provided, audits entire frontend/src/styles directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default path
AUDIT_PATH="${1:-${UCORE_ROOT:-$HOME/Code/uCore}/frontend/src/styles}"

echo -e "${BLUE}🔍 USX Font Standards Audit${NC}"
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

# ─── 1. Hardcoded Font Sizes ───────────────────────────────────────
print_section "1. Hardcoded Font Sizes (px values)"

HARDCODED=$(grep -rn "font-size:[^;]*px" "$AUDIT_PATH" --include="*.css" --include="*.jsx" 2>/dev/null | \
  grep -v "var(--" | \
  grep -v "calc(" | \
  grep -v "prose-ui" | \
  grep -v "pico" | \
  grep -v "nestframe" || true)

if [ -n "$HARDCODED" ]; then
  echo "$HARDCODED" | while read -r line; do
    print_violation "$line"
  done
else
  print_success "No hardcoded font sizes found"
fi

# ─── 2. Duplicate Heading Styles ───────────────────────────────────
print_section "2. Duplicate Heading Styles"

DUPLICATE_HEADINGS=$(grep -rn "h1\b\|h2\b\|h3\b" "$AUDIT_PATH" --include="*.css" 2>/dev/null | \
  grep -v "prose-ui" | \
  grep -v "pico" | \
  grep -v "nestframe" | \
  grep -v "\.prose" | \
  grep -v "usx-prose" || true)

if [ -n "$DUPLICATE_HEADINGS" ]; then
  echo "$DUPLICATE_HEADINGS" | while read -r line; do
    print_violation "$line"
  done
else
  print_success "No duplicate heading styles found"
fi

# ─── 3. Sidebar Font Size Issues ───────────────────────────────────
print_section "3. Sidebar Font Size Issues"

SIDEBAR_ISSUES=$(grep -rn "\.sidebar" "$AUDIT_PATH" --include="*.css" 2>/dev/null | \
  grep "font-size:" | \
  grep -v "var(--font-base)" || true)

if [ -n "$SIDEBAR_ISSUES" ]; then
  echo "$SIDEBAR_ISSUES" | while read -r line; do
    print_violation "$line"
  done
else
  print_success "No sidebar font size issues found"
fi

# ─── 4. Missing --font-base System ─────────────────────────────────
print_section "4. Missing --font-base System"

MISSING_FONT_BASE=$(grep -rn "@media" "$AUDIT_PATH" --include="*.css" 2>/dev/null | \
  grep -E "(max-width|min-width)" | \
  grep -v "var(--font-base)" | \
  grep -v "prose-ui" | \
  grep -v "pico" || true)

if [ -n "$MISSING_FONT_BASE" ]; then
  print_warning "Viewport media queries found without --font-base system"
  echo "$MISSING_FONT_BASE" | head -5 | while read -r line; do
    echo "  $line"
  done
else
  print_success "--font-base system properly defined"
fi

# ─── 5. Prose UI Usage Check ───────────────────────────────────────
print_section "5. Prose UI Usage Check"

PROSE_USAGE=$(grep -rn "\.prose" "$AUDIT_PATH" --include="*.css" 2>/dev/null | \
  grep -v "prose-ui" | \
  grep -v "prose-multi" || true)

if [ -n "$PROSE_USAGE" ]; then
  print_warning "Found custom .prose styles (should use Prose UI tokens)"
  echo "$PROSE_USAGE" | head -3 | while read -r line; do
    echo "  $line"
  done
else
  print_success "Prose UI properly used"
fi

# ─── 6. Pico.css Usage Check ───────────────────────────────────────
print_section "6. Pico.css Usage Check"

PICO_USAGE=$(grep -rn "@import.*pico" "$AUDIT_PATH" --include="*.css" 2>/dev/null || true)

if [ -n "$PICO_USAGE" ]; then
  print_success "Pico.css imported"
else
  print_warning "Pico.css not imported"
fi

# ─── 7. TV (10-foot) Override Check ─────────────────────────────────
print_section "7. TV (10-foot) Override Check"

TV_OVERRIDE=$(grep -rn "min-width.*1800" "$AUDIT_PATH" --include="*.css" 2>/dev/null | \
  grep -v "prose-ui" | \
  grep -v "pico" || true)

if [ -n "$TV_OVERRIDE" ]; then
  print_success "TV (10-foot) override found"
else
  print_warning "TV (10-foot) override not found"
fi

# ─── 8. File Count ─────────────────────────────────────────────────
print_section "8. Audit Summary"

CSS_COUNT=$(find "$AUDIT_PATH" -name "*.css" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "CSS files audited: $CSS_COUNT"

# ─── Final Report ───────────────────────────────────────────────────
echo ""
print_section "FINAL REPORT"

if [ $VIOLATIONS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  print_success "All checks passed! Surface is compliant with USX font standards."
  exit 0
elif [ $VIOLATIONS -eq 0 ]; then
  print_warning "No violations found, but there are $WARNINGS warnings to review."
  exit 0
else
  print_violation "Found $VIOLATIONS violations and $WARNINGS warnings."
  echo ""
  echo "Fixes needed:"
  echo "  1. Replace hardcoded px values with CSS variables"
  echo "  2. Remove duplicate/conflicting CSS"
  echo "  3. Use --font-base system for all viewport scaling"
  echo "  4. Ensure Prose UI and Pico use the same --font-base"
  exit 1
fi