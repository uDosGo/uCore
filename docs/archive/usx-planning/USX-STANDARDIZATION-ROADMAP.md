# USX Standardization Roadmap
**Status:** Foundation Complete ✅ → Phase 2 Ready  
**Created:** 2026-06-24  
**Objective:** Standardize all surfaces using Pico CSS + USX spacing scale

---

## ✅ Phase 1: Foundation (COMPLETE)

### Files Created
1. **`usx-spacing-scale.css`** ✅
   - Defines standardized spacing system (`--usx-spacing-xs` through `--usx-spacing-2xl`)
   - Component-specific variables (cards, buttons, sections, etc.)
   - Utility classes for padding/gap/margin (`.usx-p-*`, `.usx-gap-*`, etc.)
   - Layout helper classes (`.usx-flex-row`, `.usx-flex-col`, etc.)

2. **`usx-pico-reset.css`** ✅
   - Enforces Pico CSS tokens globally
   - Resets hardcoded colors in old code (especially ucode.css)
   - Standardizes common components (cards, badges, buttons)
   - Fixes nested div double-padding issues
   - Normalizes inputs, lists, typography, scrollbars, focus states

3. **`usx-import-order.md`** ✅
   - SOP for importing styles across all surfaces
   - Before/after migration examples
   - Complete variable reference
   - Testing checklist

4. **`USX-STANDARDIZATION-ANALYSIS.md`** ✅
   - Detailed analysis of current state across all surfaces
   - Key issues identified (spacing, colors, nesting)
   - Success criteria

5. **`main.tsx` updated** ✅
   - Added imports for `usx-spacing-scale.css` and `usx-pico-reset.css`
   - Correct import order ensures standardization applies globally

### Import Chain Now Active
```
pico.min.css (from nestframe.css)
    ↓
usx-spacing-scale.css (defines spacing variables)
    ↓
usx-pico-reset.css (enforces Pico tokens, resets conflicts)
    ↓
hub/index.css, developer.css, ucode.css, etc. (surface styles)
```

---

## 🔄 Phase 2: Baseline Reset (Ready to Start)

### High Priority: Conflicting Old Code

#### Task 2.1: Clean `surfaces/ucode.css`
**Issue:** Has hardcoded colors and old style patterns  
**Changes needed:**
- Replace all `#111822` → `var(--pico-card-sectioning-background-color)`
- Replace all `#0f141c` → `var(--pico-card-background-color)`
- Replace all `#30363d` → `var(--pico-border-color)` (already done by reset)
- Replace padding values with `var(--usx-spacing-*)`
- Replace `font-size: 14px` hardcodes → rely on Pico defaults

**Checklist:**
- [ ] Read full file and identify all hardcoded values
- [ ] Replace hex colors with variables
- [ ] Replace padding/margin with spacing variables
- [ ] Test in dev: check no visual shift
- [ ] Run audit: `npm run audit:usx-standard` (if available)

#### Task 2.2: Standardize `hub/dashboard.css`
**Issue:** Inconsistent padding patterns (12px, 16px, 14px mix)  
**Changes needed:**
- Standardize card padding to `var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal)`
- Standardize section padding to `var(--usx-section-padding)`
- Replace loose padding values with spacing variables
- Ensure badges use `var(--usx-badge-padding-*)`

**Checklist:**
- [ ] Audit all `.padding` declarations
- [ ] Replace with appropriate `var(--usx-*)` equivalents
- [ ] Check grid gaps (should be `var(--usx-grid-gap)`)
- [ ] Validate visual consistency with other hub tabs

### Medium Priority: Spacing Inconsistency

#### Task 2.3: Normalize `surfaces/workflow.css`
**Issue:** Uses hardcoded px instead of spacing variables  
**Changes needed:**
- Replace `14px 16px` padding → `var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal)`
- Replace `16px` padding → `var(--usx-spacing-lg)`
- Replace `16px` gaps → `var(--usx-grid-gap-loose)` or `var(--usx-spacing-lg)`
- Replace `10px, 6px` gaps → `var(--usx-spacing-*)`

**Example replacements:**
```
BEFORE: padding: 14px 16px;       AFTER: padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
BEFORE: gap: 10px;                AFTER: gap: var(--usx-spacing-sm);
BEFORE: margin-bottom: 20px;      AFTER: margin-bottom: var(--usx-spacing-lg);
```

**Checklist:**
- [ ] Identify all px-based padding/margin/gap
- [ ] Map to closest `var(--usx-*)` value using spacing scale
- [ ] Test component visuals (cards, sections, grids)
- [ ] Ensure no layout shift

#### Task 2.4: Standardize `surfaces/developer.css`
**Issue:** Font sizes hardcoded, spacing mixture  
**Changes needed:**
- Keep specialized font sizes (11px, 12px, 13px) for now but add comment explaining why
- Replace padding/margin with spacing variables
- Ensure buttons use `var(--usx-button-padding-*)`
- Standardize panel padding/gap

**Checklist:**
- [ ] Replace all padding/margin with `var(--usx-*)`
- [ ] Review font sizes: which can defer to Pico?
- [ ] Test panel layouts, chat panels, floating windows

#### Task 2.5: Align `userver.css` spacing model
**Issue:** Inconsistent grid/padding spacing  
**Changes needed:**
- Standardize grid gaps
- Replace inconsistent padding patterns
- Align with card/section patterns from Phase 2.2

**Checklist:**
- [ ] Audit grid definitions
- [ ] Replace padding with spacing variables
- [ ] Validate card and service row layouts

---

## 🎯 Phase 3: Component Standardization

### Task 3.1: Normalize Padding Across All Surfaces
**Goal:** Every surface uses same padding model

```
Standard model:
- Card padding: 14px vertical, 16px horizontal
- Section padding: 16px all sides
- Label/badge padding: 2px vertical, 8px horizontal
- Button padding: 8px vertical, 16px horizontal
```

**Affected surfaces:** Workflow, Developer, uServer, UIHub  
**Checklist:**
- [ ] Audit each surface's card styles
- [ ] Ensure consistency across all card types
- [ ] Update section/container padding uniformly
- [ ] Document any intentional exceptions

### Task 3.2: Standardize Gaps
**Goal:** Eliminate 2-10px variation mess

```
Use only:
- 4px (tight lists, internal spacing)
- 8px (standard small gap)
- 12px (standard medium gap)
- 16px (large gaps, loose layouts)
- 24px (section separation)
```

**Search and replace plan:**
- [ ] Find all `gap: Xpx` where X ∈ {2,3,5,6,7,9,10,11,13,14,15,17,18,19} → map to closest standard
- [ ] Replace `gap: 6px` → `var(--usx-spacing-xs)` or `var(--usx-compact-gap)`
- [ ] Replace `gap: 10px` → `var(--usx-spacing-sm)` (8px)
- [ ] Replace `gap: 20px` → `var(--usx-section-separator)` or `var(--usx-spacing-lg)` (16px)
- [ ] Test visuals: no crowding, no excessive whitespace

### Task 3.3: Fix Nested Div Double-Padding
**Goal:** Eliminate margin/padding accumulation in panels/sections

**Pattern to fix:**
```
BEFORE (double padding):
.panel { padding: 16px; }
.panel-header { padding-bottom: 4px; }  ← Creates extra space

AFTER (clean nesting):
.panel { padding: 16px; }
.panel-header { margin: 0; padding: 0; }  ← Header text inherits panel padding
.panel-content { margin: 0; padding: 0; } ← Content inherits panel padding
```

**usx-pico-reset.css already includes patterns** for this, but surfaces need updating:
- [ ] Review Developer surface's panel hierarchy
- [ ] Check Workflow section nesting
- [ ] Validate no margin accumulation in UIHub cards

---

## 📊 Phase 4: Validation & QA

### Task 4.1: Visual Regression Testing
**Goal:** Ensure no layout shift or visual breakage

**Test each surface:**
- [ ] UIHub Dashboard: Check card alignment, grid gaps, padding consistency
- [ ] Workflow: Verify task cards, stats cards, panels
- [ ] Developer: Check floating panels, chat window, code preview
- [ ] uServer: Validate service cards, log display, grid layout
- [ ] uCode: Verify viewport, dashboard, tool grid (terminal rendering exempt)

**Success criteria:**
- Same visual appearance as before
- No unexpected whitespace or crowding
- All components properly aligned

### Task 4.2: Audit Pass
**Run USX-STANDARD-003 audit:**
```bash
npm run audit:usx-standard
```

**Expected results:**
- ✅ All files pass typography audit
- ✅ No hardcoded colors (except Pico fallbacks)
- ✅ No hardcoded px in padding/margin (except exceptions)
- ✅ Spacing uses variable system
- ✅ No nested div double-padding

### Task 4.3: Code Review
**Checklist:**
- [ ] All `var(--pico-*)` usage correct
- [ ] All `var(--usx-*)` usage correct
- [ ] No inline style attributes can be moved to CSS
- [ ] Components follow documented patterns
- [ ] Documentation up to date

### Task 4.4: Browser Testing
- [ ] Chrome/Edge (Latest)
- [ ] Firefox (Latest)
- [ ] Safari (Latest)
- [ ] Mobile viewport (iPad, phone)

---

## 📋 Phase 5: Documentation & Knowledge Transfer

### Task 5.1: Update Developer Guide
**Location:** `usx-import-order.md` + `USX-STANDARDIZATION-ANALYSIS.md`

**Ensure it covers:**
- [ ] The spacing scale and when to use each value
- [ ] Pico variable reference
- [ ] Common component patterns
- [ ] Import order requirements
- [ ] Testing checklist for PRs

### Task 5.2: Create PR Template
**For future USX styling work:**
```markdown
## USX Styling Checklist
- [ ] Uses var(--usx-*) for spacing
- [ ] Uses var(--pico-*) for colors
- [ ] No hardcoded px (except special cases)
- [ ] Follows component patterns from usx-spacing-scale.css
- [ ] Visual consistency tested in dev
- [ ] No layout shift from previous version
```

### Task 5.3: Pin to /tasker/ (if using Kanban)
Create a `.tasker/ ` markdown note so future work references this plan.

---

## 🚀 Quick Start Commands

### To verify setup:
```bash
# Check if new CSS files load
cd frontend
npm run dev
# Visit http://localhost:5173
# Check DevTools: should see usx-spacing-scale.css and usx-pico-reset.css loaded
```

### To start Phase 2 (pick one):
```bash
# 1. Start with ucode.css (highest priority)
# - Use usx-pico-reset.css as a template for what gets overridden
# - Replace hex colors systematically
# - Test in /ucode page

# 2. Or start with hub/dashboard.css
# - Simpler surface, good starting point
# - Focus on card/badge/button padding standardization
# - Test in / (dashboard)

# 3. Or start with userver.css
# - Good test case for grid standardization
# - Service cards + log display
# - Test in /server
```

### To run audit (when available):
```bash
npm run audit:usx-standard
```

---

## 📈 Success Metrics

At completion of all phases:

| Metric | Target | Status |
|--------|--------|--------|
| Spacing scale adoption | 100% of surfaces use `var(--usx-*)` | 🔄 In Progress |
| Color consistency | 100% use Pico vars + fallbacks | 🔄 In Progress |
| Hardcoded px in sizing | 0% (except terminal fonts) | 🔄 In Progress |
| Card padding consistency | All cards: 14px V, 16px H | 🔄 In Progress |
| Gap standardization | Only 4, 8, 12, 16, 24px gaps used | 🔄 In Progress |
| Double-padding fixed | 100% of panels/sections clean | 🔄 In Progress |
| USX-STANDARD-003 audit | PASS | 🔄 Pending |
| Visual regression tests | All surfaces: no layout shift | 🔄 Pending |

---

## 🔗 Related Documents

- **Pico CSS Docs:** https://picocss.com/docs/css-variables
- **USX Analysis:** `USX-STANDARDIZATION-ANALYSIS.md`
- **Import Order SOP:** `usx-import-order.md`
- **Spacing Scale:** `usx-spacing-scale.css`
- **Reset Rules:** `usx-pico-reset.css`

---

## Next Steps

1. **Choose Phase 2 task** (recommend starting with `ucode.css` or `hub/dashboard.css`)
2. **Create a feature branch** if using Git workflow
3. **Follow the checklist** for that task
4. **Test in dev** at each step
5. **Commit small, focused changes** with good messages
6. **Get code review** before merging
7. **Move to next task** when complete

---

**Last Updated:** 2026-06-24  
**Roadmap Owner:** uCore Dev Team  
**Estimated Effort:** Phase 2-3: ~8-12 hours of focused work
