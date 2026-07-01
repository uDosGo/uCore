# Frontend Consolidation Playbook — Jun 26, 2026

## Executive Summary

Based on comprehensive audit of 78+ React components and 35+ CSS files:

| Metric | Count | Status |
|--------|-------|--------|
| **Surfaces Fully Compliant** | 6 ✅ | Production-ready |
| **Surfaces Needing Fixes** | 4 🔴 | High priority |
| **Duplicate Patterns Found** | 68 | Consolidable |
| **Hardcoded Font-Sizes** | 68 | Need migration |
| **Redundant Icon Rules** | 40+ | Centralize to usx-icons.css |

---

## Phase 1: Immediate Fixes (Days 1-2)

### 1.1 Canonical Reference: Create `.usx-card-header` Utility

**File**: `frontend/src/styles/usx/usx-layout-system.css`

**What**: Consolidate 15+ duplicate card header implementations into single reusable utility

**Impact**: 150 lines of CSS removed, single source of truth

**Action**:
```css
/* ═══════════════════════════════════════════════════════════════
   .usx-card-header — Canonical card/panel header utility
   ═══════════════════════════════════════════════════════════════ */

.usx-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--pico-border-color, #30363d);
  background: var(--pico-card-sectioning-background-color, #1c2128);
  transition: background 150ms ease;
}

.usx-card-header:hover {
  background: color-mix(in srgb, 
    var(--pico-card-sectioning-background-color, #1c2128) 95%, 
    var(--pico-primary, #58a6ff) 5%);
}

.usx-card-header h3,
.usx-card-header h4 {
  margin: 0;
  font-size: var(--usx-font-size-h3);
  font-weight: var(--usx-font-weight-heading);
  color: var(--pico-color, #c9d1d9);
}

.usx-card-header-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.usx-card-header-title {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.usx-card-header-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-left: auto;
  flex-shrink: 0;
}

/* Variants */

.usx-card-header--compact {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  gap: var(--usx-spacing-sm);
}

.usx-card-header--full-width {
  width: 100%;
}
```

**Deprecation Strategy**:
1. Add `.usx-card-header` to layout system ✅
2. Update all surfaces to use `.usx-card-header` (next phase)
3. Keep old classes as aliases for 1 release
4. Remove old classes in following release

**Files to Update** (Phase 1b):
- `hub/settings.css` — Remove `.hub-settings-card-header`
- `hub/dashboard.css` — Remove `.hub-card-header`, `.hub-dash-card-header`
- `surfaces/developer.css` — Remove `.developer-panel-header`
- (Continue for all 15 implementations)

---

### 1.2 Migrate All Hardcoded Font-Sizes to USX Variables

**Effort**: 3-4 hours | **Impact**: CRITICAL

**Target Files** (in priority order):
1. `surfaces/developer.css` (23 hardcoded)
2. `hub/settings.css` (12 hardcoded)
3. `surfaces/ucode.css` (7 hardcoded)
4. `assistui.css` (5 hardcoded)

**Template**:
```css
/* ❌ BEFORE */
.developer-chat-prose { font-size: 0.9em; }
.hub-settings-card h3 { font-size: 0.95rem; }
.assistui-message-body { font-size: 12px; }

/* ✅ AFTER */
.developer-chat-prose { font-size: var(--usx-font-size-body); }
.hub-settings-card h3 { font-size: var(--usx-font-size-h3); }
.assistui-message-body { font-size: var(--usx-font-size-body); }
```

**Mapping Table**:
| Original | Replacement | Reasoning |
|----------|-------------|-----------|
| `font-size: 14px` | `var(--usx-font-size-body)` | Primary content |
| `font-size: 12px` | `var(--usx-font-size-body)` | Still body text |
| `font-size: 11.2px` | `var(--usx-font-size-meta)` | Meta/secondary |
| `font-size: 0.8em` | Already correct ✅ | Keep |
| `font-size: 0.9em` | `1em` (body) | Remove scaling |
| `font-size: 1.2em` | `var(--usx-font-size-h3)` | Subheading |

---

### 1.3 Consolidate All Icon Rules to `usx-icons.css`

**Current State**: Icon sizing rules scattered across 8+ files

**Action**:
1. **Audit all icon declarations** across surfaces
2. **Add to `usx-icons.css` canonical rules**:
   ```css
   .developer-repo-btn svg { font-size: 1em; }  ← Already in usx-icons.css
   ```
3. **Remove duplicate rules** from surface files
4. **Document the canonical rule**: "All icons inherit font-size from parent"

**Savings**: ~100 lines of redundant CSS

---

## Phase 2: Structural Consolidation (Days 3-4)

### 2.1 Create Shared Utility Components Library

**File**: `frontend/src/styles/usx/usx-components.css` (NEW)

Consolidate common patterns:

```css
/* Status Badges — Replaces 5 variants */
.usx-status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: 999px;
  font-size: var(--usx-font-size-meta);
  font-weight: var(--usx-font-weight-meta);
}

.usx-status-badge--success {
  background: rgba(63, 185, 80, 0.1);
  color: var(--pico-ins-color, #3fb950);
}

.usx-status-badge--error {
  background: rgba(248, 81, 73, 0.1);
  color: var(--pico-del-color, #f85449);
}

.usx-status-badge--warning {
  background: rgba(212, 168, 26, 0.1);
  color: var(--pico-type-color, #d4a81a);
}

/* Section Headers — Replaces 8 variants */
.usx-section-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  margin-bottom: var(--usx-spacing-lg);
  padding-bottom: var(--usx-spacing-md);
  border-bottom: 1px solid var(--pico-border-color, #30363d);
}

.usx-section-header h2 {
  margin: 0;
  font-size: var(--usx-font-size-h2);
  font-weight: var(--usx-font-weight-heading);
  color: var(--pico-color, #c9d1d9);
}

/* Filter Buttons — Replaces 6 variants */
.usx-filter-button {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: 999px;
  background: transparent;
  color: var(--pico-muted-color, #8b949e);
  font-size: var(--usx-font-size-meta);
  cursor: pointer;
  transition: all 150ms ease;
}

.usx-filter-button:hover {
  border-color: var(--pico-primary, #58a6ff);
  color: var(--pico-primary, #58a6ff);
}

.usx-filter-button--active {
  background: var(--pico-primary-container, rgba(13, 110, 253, 0.15));
  border-color: var(--pico-primary, #58a6ff);
  color: var(--pico-primary, #58a6ff);
  font-weight: 600;
}
```

**Files to Remove/Update**:
- Remove `.developer-status-badge`, `.hub-status-badge`, etc.
- Update all components to use `.usx-status-badge` variants
- Same for section headers and filter buttons

---

### 2.2 Create Responsive Grid Utilities

**File**: `usx-grid-system.css` (create if not exists)

```css
/* Card Grid — Replaces >20 custom grids */
.usx-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--usx-spacing-lg);
}

/* Responsive: Mobile → Tablet → Desktop */
@media (max-width: 767px) {
  .usx-card-grid {
    grid-template-columns: 1fr;
    gap: var(--usx-spacing-md);
  }
}

@media (min-width: 768px) and (max-width: 1024px) {
  .usx-card-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--usx-spacing-md);
  }
}

/* Settings Grid */
.usx-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--usx-spacing-md);
}

/* List Grid */
.usx-list-grid {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}
```

---

## Phase 3: Testing & Validation (Days 5)

### 3.1 Visual Regression Testing

Create checklist for each surface:

**Template**:
```
Surface: [name]

✅ Typography:
  - [ ] Body text responsive on mobile/tablet/desktop
  - [ ] Sidebar fonts match body size
  - [ ] Meta text at 0.8em (counts, badges)
  - [ ] Headings scale correctly

✅ Icons:
  - [ ] Button icons match text size
  - [ ] Large icons (empty states) scale with viewport
  - [ ] No oversized icons on mobile

✅ Layout:
  - [ ] Card headers consistent across all cards
  - [ ] Spacing follows USX variables
  - [ ] No hardcoded padding/margins

✅ Colors:
  - [ ] Uses Pico variables (not hardcoded hex)
  - [ ] Respects dark/light mode
  - [ ] Status badges show correct colors
```

### 3.2 Regression Test Suite

**Files to Test**:
1. Developer Surface
2. Hub Dashboard
3. System Page
4. AssistUI
5. GridUI
6. Global Toolbar
7. Vault Sidebar

---

## Phase 4: Documentation & Handoff (Day 6)

### 4.1 Update Style Guide

**File**: `docs/FRONTEND_STYLE_GUIDE.md` (update existing)

Add sections:
- ✅ Canonical utilities (card-header, status-badge, etc.)
- ✅ When to use USX vs Pico vs Prose styles
- ✅ Font-size migration checklist
- ✅ Icon sizing rules
- ✅ Common anti-patterns to avoid

### 4.2 Component Library Inventory

Create map of:
- ✅ Which surfaces use which utilities
- ✅ Which patterns are deprecated
- ✅ Migration status per surface

---

## Quick Reference: Before/After

### Before (Broken State)
```
Sidebar nav: 0.8em (too small)
Body text: 14px (correct)
Icons: 2.5em hardcoded (too large on mobile)
Card headers: 15 different implementations
Status badges: 5 variants with duplicate code
Font-size overrides: 68 instances
```

### After (Consolidated State)
```
Sidebar nav: 1em (matches body) ✅
Body text: var(--usx-font-size-body) ✅
Icons: Responsive scaling per viewport ✅
Card headers: Single .usx-card-header utility ✅
Status badges: One .usx-status-badge with variants ✅
Font-size overrides: 0 (all use variables) ✅
```

---

## Files Modified (Summary)

| Phase | File | Changes | Lines Saved |
|-------|------|---------|-------------|
| 1.1 | `usx-layout-system.css` | Add `.usx-card-header` | — |
| 1.2 | `surfaces/developer.css` | Replace 23 hardcoded sizes | ~40 |
| 1.2 | `hub/settings.css` | Replace 12 hardcoded sizes | ~20 |
| 1.3 | Remove from surfaces | Remove duplicate icon rules | ~100 |
| 2.1 | `usx-components.css` | Add unified utilities | — |
| 2.2 | `usx-grid-system.css` | Add responsive grids | — |

**Total CSS Reduction**: ~250-300 lines eliminated through consolidation

---

## Success Metrics

After completing all phases:

- ✅ **Consistency**: 100% of surfaces use USX variables
- ✅ **Duplication**: <5% redundant CSS (down from 30%)
- ✅ **Maintainability**: Single place to update each UI pattern
- ✅ **Performance**: Smaller CSS bundles (consolidation = fewer rules)
- ✅ **Compliance**: All 10 surfaces follow USX standards
- ✅ **Responsiveness**: Font and icon scaling works on all viewports

---

## Next Steps

1. **Assign Phase 1 to developer** → 1-2 days
2. **Validate with visual regression tests** → 4 hours
3. **Proceed to Phase 2** (structural consolidation)
4. **Document patterns** in component library
5. **Socialize standards** with team
