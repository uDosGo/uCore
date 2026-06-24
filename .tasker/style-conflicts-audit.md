# Style Conflicts Audit — Hardcoded Font-Sizes & Blue Remnants

**Scope**: Found 68 hardcoded font-size declarations conflicting with new typography system  
**Date**: 2026-06-24

---

## Critical Findings

### 1. Hardcoded Font-Sizes (68 instances)

These override the global typography system and should be using CSS variables:

#### **assistui.css**
```css
.assistui-prompt-card-icon { font-size: 18px; }  → Should use --usx-font-size-display
.assistui-prompt-card-label { /* inherits 14px */ }  → Should use --usx-font-size-body
.assistui-model-btn { font-size: 13px; }  → Should use --usx-font-size-body or --usx-font-size-meta
```

#### **surfaces/developer.css** (Most conflicts here)
```css
.developer-preview-title { font-size: 13px; }  → Use --usx-font-size-h3
.developer-preview-subtitle { font-size: 11px; }  → Use --usx-font-size-meta
.developer-skill-title { font-size: 12px; }  → Use --usx-font-size-body
.developer-chat-prompt-icon { font-size: 18px; }  → Use --usx-font-size-h2 or display
.kanban-detail-meta-text { font-size: 11px; }  → Use --usx-font-size-meta
.kanban-detail-tag { font-size: 10px; }  → Use --usx-font-size-meta (0.8em)
.diff-editor-simple-label { font-size: 11px; }  → Use --usx-font-size-meta
```

#### **surfaces/ucode.css**
```css
.ucode-tool-card-title { font-size: 13px; }  → Use --usx-font-size-h3
.ucode-tool-card-subtitle { font-size: 11px; }  → Use --usx-font-size-meta
.ucode-tool-btn { font-size: 12px; }  → Use --usx-font-size-body
```

#### **gridui-terminal.css** (Grid-specific)
```css
.gridui-teletext-msg { font-size: 16px; }  → Keep (grid-specific override)
.gridui-teletext-poll-time { font-size: 10px; }  → Use --usx-font-size-meta
.gridui-teletext-nav-label { font-size: 14px; }  → Use --usx-font-size-body
```

---

### 2. Blue Background Remnants (13 instances)

These should use semantic Pico variables instead of hardcoded blue:

**Pattern**: `background: rgba(13, 110, 253, 0.15);` ← Should use Pico variables

#### **hub/settings.css**
```css
.hub-settings-fontsize-btn--active {
  background: rgba(13, 110, 253, 0.15);  → Use var(--pico-primary-container)
  border-color: var(--pico-primary, #58a6ff);
}
```

#### **hub/dashboard.css**
```css
.hub-card--pending {
  background: rgba(13, 110, 253, 0.15);  → Use var(--pico-primary-container)
}
```

#### **surfaces/developer.css**
```css
.developer-chat-msg--user .developer-chat-msg-content {
  background: rgba(13, 110, 253, 0.15);  → Should be consistent
}
```

#### **assistui.css**
```css
.assistui-agent-pill--active {
  background: rgba(13, 110, 253, 0.15);  → Use var(--pico-primary-container)
}
```

#### **nestframe.css**
```css
.usx-badge--blue {
  background: rgba(13, 110, 253, 0.15);  → Already defined, but check consistency
}
```

---

## Recommended Actions

### Phase 1: Replace Hardcoded Font-Sizes (High Priority)

Map hardcoded sizes to typography variables:

| Hardcoded | → | Variable | Notes |
|-----------|---|----------|-------|
| 18px | → | `var(--usx-font-size-display)` | Display/hero text |
| 16px | → | `var(--usx-font-size-h1)` | Large labels |
| 14px | → | `var(--usx-font-size-body)` | Default text |
| 13px | → | `var(--usx-font-size-body)` | Slightly smaller body |
| 12px | → | `var(--usx-font-size-body)` | Also body size |
| 11px | → | `var(--usx-font-size-meta)` | Supporting text |
| 10px | → | `var(--usx-font-size-meta)` | Also meta (0.8em) |

### Phase 2: Clean Up Blue Backgrounds

Replace all `rgba(13, 110, 253, 0.15)` with:
```css
background: var(--pico-primary-container, rgba(13, 110, 253, 0.15));
```

This ensures:
1. Uses the system's primary container color
2. Falls back to blue if not defined
3. Makes it themeable

### Phase 3: Remove Conflicting Declarations

Files to audit and potentially remove redundant styles:
- `usx/usx-typography-prose.css` - Has font-size overrides that may conflict

---

## Impact Analysis

### Current Conflicts
- **68 instances** of hardcoded font-sizes override the typography system
- **13 instances** of hardcoded blue backgrounds not using Pico variables
- Typography scaling only works where no hardcoded size exists
- Active/hover states use inconsistent blue tonality

### After Cleanup
✅ All text respects typography hierarchy  
✅ All active/disabled states use consistent Pico variables  
✅ System responds properly to `data-typography-scale` changes  
✅ Easier to maintain — change one variable, affects everything  
✅ Better theme support — respects user preferences  

---

## Files to Modify

| File | Issue | Action |
|------|-------|--------|
| `surfaces/developer.css` | 15+ hardcoded sizes | Replace with variables |
| `gridui-terminal.css` | 8 hardcoded sizes | Replace with variables (except grid-specific) |
| `surfaces/ucode.css` | 7 hardcoded sizes | Replace with variables |
| `assistui.css` | 5 hardcoded sizes | Replace with variables |
| `hub/settings.css` | 2 blue backgrounds | Use var(--pico-primary-container) |
| `hub/dashboard.css` | 2 blue backgrounds + sizes | Replace both |
| `nestframe.css` | 1 blue background | Verify consistency |
| `usx/usx-typography-prose.css` | Font-size catch-alls | Review for conflicts |

---

## Next Steps

1. **Run audit on each file** — Identify which hardcoded sizes are intentional (grid/special)
2. **Create replacement plan** — Map each hardcoded size to appropriate variable
3. **Update files** — Replace hardcoded with CSS variables
4. **Test responsive scaling** — Verify `data-typography-scale` works correctly
5. **Verify theme consistency** — Ensure all active states use Pico variables
6. **Rebuild & verify** — Check visual consistency across viewports

---

## Example Fixes

### Before (Conflicting)
```css
.developer-preview-title {
  font-size: 13px;  ← Hardcoded, overrides system
  font-weight: 600;
}
```

### After (Clean)
```css
.developer-preview-title {
  font-size: var(--usx-font-size-h3);  ← Uses system
  font-weight: var(--usx-font-weight-heading);
}
```

---

## Severity Levels

🔴 **Critical** (Breaks responsive scaling):
- All hardcoded font-sizes in display/interactive components
- Should be replaced immediately

🟡 **Medium** (Hardcoded but acceptable):
- Grid-specific sizes (terminal, teletext)
- Monospace-specific adjustments
- Can be reviewed case-by-case

🟢 **Low** (Good practice):
- Blue background hardcodes
- Should use Pico variables for consistency

