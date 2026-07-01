# USX Styling Import Order
**Status:** Standard Operating Procedure  
**Version:** 2.0 (Pico CSS Standardization)

## Import Hierarchy

All USX surface styles must follow this import order to ensure consistency and prevent conflicts:

```
1. pico.min.css                    ← Pico CSS base (already imported elsewhere)
2. usx-spacing-scale.css           ← Spacing variables & component patterns
3. usx-pico-reset.css              ← Pico token enforcement & color resets
4. Other shared styles (prose, etc)
5. Surface-specific styles (.css)
```

## In Practice

### For NestFrame/Main App (`nestframe.css`)

```css
/* Import order in nestframe.css */
@import 'usx/usx-spacing-scale.css';
@import 'usx/usx-pico-reset.css';
@import 'usx/usx-typography.css';
/* ... rest of imports ... */
```

### For Individual Surfaces

Each surface CSS should assume the shared imports are already loaded:

**workflow.css**
```css
/* No need to import usx-spacing-scale or usx-pico-reset */
/* Just reference the variables they define */
.workflow-card {
  padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
  background: var(--pico-card-background-color);
}
```

**developer.css**
```css
/* Same pattern */
.developer-panel {
  padding: var(--usx-section-padding);
  gap: var(--usx-section-gap);
  background: var(--pico-background-color);
}
```

### For Hub Surfaces (`hub/index.css`)

```css
/* Already has the pattern */
@import './dashboard.css';
@import './apps.css';
@import './settings.css';

/* But should ensure parent (main app) loads USX standardization first */
```

## Critical Rules

1. **DO** use `var(--usx-spacing-*)` for all padding/margin in new code
2. **DO** use `var(--pico-*)` for all colors
3. **DON'T** hardcode pixel values (except for special cases like terminal fonts)
4. **DON'T** repeat Pico color hex values
5. **DO** import usx-spacing-scale.css and usx-pico-reset.css before surface styles
6. **DO** run USX-STANDARD-003 audit after making changes

## Variables Available

### Spacing Variables
```
--usx-spacing-xs: 4px
--usx-spacing-sm: 8px
--usx-spacing-md: 12px
--usx-spacing-lg: 16px
--usx-spacing-xl: 24px
--usx-spacing-2xl: 32px

--usx-card-padding-vertical: 14px
--usx-card-padding-horizontal: 16px
--usx-card-gap: 8px

--usx-section-padding: 16px
--usx-section-gap: 12px

--usx-button-padding-vertical: 8px
--usx-button-padding-horizontal: 16px
--usx-badge-padding-vertical: 2px
--usx-badge-padding-horizontal: 8px

--usx-list-item-gap: 4px
--usx-list-section-gap: 8px

--usx-grid-gap: 12px
--usx-grid-gap-dense: 8px
--usx-grid-gap-loose: 16px

--usx-sidebar-gap: 8px
--usx-sidebar-padding: 12px
```

### Pico Variables (by category)
```
/* Colors */
--pico-background-color
--pico-card-background-color
--pico-card-sectioning-background-color
--pico-color
--pico-muted-color
--pico-border-color
--pico-primary
--pico-primary-hover
--pico-ins-color (success green)
--pico-del-color (error red)

/* Typography */
--pico-font-family
--pico-font-size

/* Can also use */
--pico-warning-color
--pico-color-inverse
--pico-spacing (generic unit, usually 16px)
```

## Before/After Migration

### BEFORE (Old Pattern)
```css
.workflow-card {
  padding: 14px 16px;
  gap: 8px;
  background: #161b22;  /* Hardcoded hex */
  border: 1px solid #30363d;
  color: #c9d1d9;
}

.workflow-section {
  padding: 20px;  /* Inconsistent */
  margin-bottom: 20px;
}
```

### AFTER (New Pattern)
```css
.workflow-card {
  padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
  gap: var(--usx-card-gap);
  background: var(--pico-card-background-color, #161b22);
  border: 1px solid var(--pico-border-color, #30363d);
  color: var(--pico-color, #c9d1d9);
}

.workflow-section {
  padding: var(--usx-section-padding);
  margin-bottom: var(--usx-spacing-lg);
}
```

## Testing Checklist

After updating surface styles:

- [ ] No hardcoded hex colors (except where unavoidable)
- [ ] All padding uses `var(--usx-*)` or Pico variables
- [ ] No margin/padding duplication in nested elements
- [ ] Visual consistency with other surfaces
- [ ] Run `npm run audit:usx-standard` (if script exists)
- [ ] Dev server: check layout alignment and spacing
- [ ] No layout shift compared to before

## Migration Priority

### Phase 1 (High Priority - Conflicting Code)
- [ ] `surfaces/ucode.css` - Update all #hex colors, standardize spacing
- [ ] `hub/dashboard.css` - Replace padding patterns with variables

### Phase 2 (Medium Priority - Spacing Inconsistency)
- [ ] `surfaces/workflow.css` - Replace hardcoded px with variables
- [ ] `surfaces/developer.css` - Normalize font sizes, spacing
- [ ] `userver.css` - Align spacing model

### Phase 3 (Low Priority - Already Good)
- [ ] `prose-ui-standard.css` - Already clean
- [ ] `usx/usx-base.css` - Mostly scaffolding

## Resources

- Pico CSS Variables: https://picocss.com/docs/css-variables
- USX Analysis: See `USX-STANDARDIZATION-ANALYSIS.md`
- Spacing Scale: See `usx-spacing-scale.css`
- Reset Rules: See `usx-pico-reset.css`
