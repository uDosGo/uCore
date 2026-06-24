# USX Standardization Analysis & Plan
**Date:** 2026-06-24  
**Status:** Analysis Phase  

## Executive Summary

The uCore frontend has multiple surfaces with inconsistent styles despite prior Pico CSS migration work. This document analyzes the current state and proposes standardization using Pico CSS variables as the foundation.

---

## Current State Analysis

### Surfaces Reviewed

1. **UIHub** (`hub/dashboard.css`, `hub/apps.css`, `hub/settings.css`)
   - Status: Partially using Pico variables
   - Spacing: Mix of `var(--pico-spacing)` and hardcoded `px` values
   - Colors: Mostly using var() but some fallbacks to hex codes
   - Issues: Inconsistent padding application (12px, 16px, 14px patterns)

2. **Workflow Surface** (`surfaces/workflow.css`)
   - Status: Well-structured Pico integration
   - Spacing: Using `14px`, `16px`, `20px` hardcoded values
   - Colors: Consistent Pico variable usage
   - Issues: No spacing variable abstraction, differing gaps/margins

3. **Developer Surface** (`surfaces/developer.css`)
   - Status: Good Pico usage but some hardcoded sizes
   - Spacing: Mix of px values (6px, 8px, 10px, 12px, 14px, 16px)
   - Colors: Mostly Pico variables with inline rgba() fallbacks
   - Issues: Font sizes hardcoded (11px, 12px, 13px), spacing not abstracted

4. **uServer Surface** (`userver.css`)
   - Status: Uses Pico variables correctly
   - Spacing: Mostly px-based with `var(--pico-spacing)` in key places
   - Colors: Consistent Pico usage
   - Issues: Inconsistent spacing model

5. **uCode Surface** (`surfaces/ucode.css`)
   - Status: Older code, some hardcoded values
   - Spacing: Hardcoded px values (10px, 12px, 16px)
   - Colors: Mix of hex codes and Pico variables
   - Issues: Needs cleanup, conflicting old code patterns

6. **UIHubManager** (`hub/` subdirectory)
   - Imports: dashboard.css → apps.css → settings.css
   - Status: Index-based architecture good, but content inconsistent

### Pico CSS Integration Status

#### ✅ Correct Usage
- All surfaces import Pico implicitly or have fallback values
- Color tokens properly using `var(--pico-*)` with fallbacks
- Border radius consistent (mostly 8px, 6px)

#### ⚠️ Partial/Inconsistent Usage
- **Spacing**: No standardized spacing scale (6, 8, 10, 12, 14, 16, 20, 24, 32px)
- **Padding**: Multiple surface-specific padding patterns
- **Gaps**: Inconsistent component gaps (ranging 2px to 16px)
- **Font Sizes**: Some hardcoded instead of using Pico defaults
- **Nesting**: Some divs with deep nesting + padding causing double-padding

#### ❌ Missing/Obsolete Patterns
- No spacing variable abstraction layer
- No standardized component padding model
- uCode surface has old hardcoded colors (#111822, #0f141c, #30363d instead of var())
- Some inline styles compete with CSS classes

---

## Key Issues to Address

### 1. **Spacing Inconsistency**
```
Current patterns:
- Small gaps: 2px, 4px, 6px, 8px (inconsistent usage)
- Regular gaps: 12px, 16px (most common)
- Large gaps: 20px, 24px, 32px (sporadic)
```

### 2. **Div Nesting & Double Padding**
```
Example (developer.css):
.developer-panel { padding: 16px; }
.developer-panel-header { padding-bottom: 4px; }
^ Creates padding + margin-bottom accumulation
```

### 3. **Old Color Code Remnants**
```
Example (ucode.css):
background: #111822;  ← Should be var(--pico-card-background-color)
color: #8b949e;       ← Should be var(--pico-muted-color)
```

### 4. **Font Size Variations**
```
Current:
- Labels: 11px, 12px (inconsistent)
- Body: 14px (mostly correct)
- Headings: Varied (should defer to Pico)
```

---

## Standardization Target

### Spacing Scale (CSS Variables to Add)

```css
--usx-spacing-xs: 4px;     /* Minimal gaps, internal spacing */
--usx-spacing-sm: 8px;     /* Small gaps, inline compression */
--usx-spacing-md: 12px;    /* Standard gap/padding default */
--usx-spacing-lg: 16px;    /* Primary padding/margin */
--usx-spacing-xl: 24px;    /* Section spacing */
--usx-spacing-2xl: 32px;   /* Large gaps, container spacing */
```

### Padding Model

```
Base padding: 16px (var(--usx-spacing-lg))
Card padding: 14px (slight reduction for density)
Compact padding: 12px (content-focused areas)
Minimal padding: 8px (badge, small components)
Dense padding: 6px (badges, inline elements)
```

### Component Patterns

1. **Cards**: `padding: 14px 16px;` + `gap: 8px;`
2. **Sections**: `padding: 16px;` + `gap: 12px;`
3. **Lists**: `gap: 4px;` or `gap: 8px;` (row spacing)
4. **Badges**: `padding: 2px 8px;` (consistent)
5. **Buttons**: `padding: 8px 16px;` (consistent)

---

## Implementation Plan

### Phase 1: Foundation (This Task)
- [ ] Create `usx-spacing-vars.css` with standardized spacing scale
- [ ] Create `usx-colors-reset.css` with Pico color variable reset
- [ ] Document current state in this file

### Phase 2: Baseline Reset
- [ ] Import Pico CSS standardization
- [ ] Reset old hardcoded colors in ucode.css
- [ ] Standardize surface container padding

### Phase 3: Component Standardization
- [ ] Normalize padding across all surfaces (14px card, 16px sections)
- [ ] Standardize gaps (use 8px or 12px, eliminate 2-10px variations)
- [ ] Fix nested div double-padding issues

### Phase 4: Surface-Specific Cleanup
- [ ] UIHub dashboard.css → standardize grid padding
- [ ] Workflow surface → replace hardcoded px with variables
- [ ] Developer surface → standardize font sizes, spacing
- [ ] uServer surface → align spacing model
- [ ] uCode surface → full color/spacing audit

### Phase 5: Validation
- [ ] Run USX-STANDARD-003 audit again
- [ ] Visual regression testing across surfaces
- [ ] Ensure no layout shift

---

## Next Steps

1. **Create `usx-spacing-vars.css`**: Define the standardized spacing scale
2. **Create `usx-pico-reset.css`**: Zero-out conflicting inline styles
3. **Update each surface CSS**: Replace hardcoded values with variables
4. **Test in dev**: Verify visual consistency across all surfaces

---

## Files to Modify (Priority Order)

1. **High Priority** (conflicting old code):
   - `surfaces/ucode.css` - Has old hardcoded colors, needs full reset
   - `hub/dashboard.css` - Inconsistent padding patterns

2. **Medium Priority** (spacing inconsistency):
   - `surfaces/workflow.css` - Replicate gap/padding inconsistency
   - `surfaces/developer.css` - Font sizes and spacing mixture
   - `userver.css` - Spacing model normalization

3. **Low Priority** (already clean):
   - `prose-ui-standard.css` - Already minimal
   - `usx/usx-base.css` - Mostly scaffolding

---

## Pico CSS Reference

Key Pico variables in use:
- `--pico-background-color`, `--pico-card-background-color`, `--pico-card-sectioning-background-color`
- `--pico-color`, `--pico-muted-color`
- `--pico-border-color`, `--pico-primary`, `--pico-primary-hover`
- `--pico-spacing` (base unit)
- `--pico-font-family`, `--pico-font-size`

See: https://picocss.com/docs/css-variables

---

## Success Criteria

- [ ] All surfaces use `var(--usx-spacing-*)` for padding/margin
- [ ] No hardcoded colors outside Pico var() with fallbacks
- [ ] Consistent card padding across all surfaces (14px)
- [ ] Consistent section padding (16px)
- [ ] No double-padding from nested divs
- [ ] All font sizes defer to Pico or use explicit scale
- [ ] USX-STANDARD-003 audit passes
