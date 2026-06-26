# Settings Refactor - Deferred Work Items

**Date**: 25/06/2026  
**Status**: Completed architecture + initial implementation; 3 bugs identified for next pass

## Completed ✅

- [x] Global Settings consolidation (4 switchers)
- [x] USXSettingsPanel creation (Typography/Colors/Variables/Stylesheet tabs)
- [x] GridCoreSettingsPanel creation (5 presets + grid algebra)
- [x] uSystemSettingsPanel creation (Service/Performance/Monitoring)
- [x] System Surface modernization (system-surface.css)
- [x] Settings architecture documentation
- [x] Cache clear & fresh build
- [x] Services icon fix (hub)
- [x] Story Forms full-page layout

## ✅ Fixed Bugs (Completed - Pass 2)

### 1. ✅ USX Styles - Inconsistent Overrides (FIXED)

**Resolution**: Replaced all hardcoded rgba() colors with `color-mix(in srgb, var(--pico-primary) X%, transparent)` pattern.

**Files Fixed**:
- `frontend/src/surfaces/developer/usx-settings.css`
- `frontend/src/surfaces/developer/system-surface-dev.css`
- `frontend/src/surfaces/system/system-surface.css`
- `frontend/src/styles/system/story-forms.css`

**Changes Made**:
- `rgba(88, 166, 255, 0.05)` → `color-mix(in srgb, var(--pico-primary, #58a6ff) 5%, transparent)`
- `rgba(88, 166, 255, 0.08)` → `color-mix(in srgb, var(--pico-primary, #58a6ff) 8%, transparent)`
- `rgba(88, 166, 255, 0.1)` → `color-mix(in srgb, var(--pico-primary, #58a6ff) 10%, transparent)`
- All custom font-family references replaced with `var(--pico-font-family-monospace)`

### 2. ✅ Card Selection Styling Bug (FIXED)

**Resolution**: Added scoped `:focus-within` selector with proper outline handling.

**Files Fixed**:
- `frontend/src/surfaces/system/system-surface.css`

**Changes Made**:
```css
.system-card:focus-within {
  outline: 2px solid var(--pico-primary, #58a6ff);
  outline-offset: -1px;
}

.system-card.no-focus:focus-within {
  outline: none;
}
```

- Only fires when card has focus within AND not marked with `.no-focus` class
- Uses outline instead of hard border to avoid layout shift
- Maintains Pico color variables exclusively

### 3. ✅ Font Sizes Not Standardized (FIXED)

**Resolution**: Replaced all hardcoded px values with Pico CSS variable cascade.

**Files Fixed**:
- `frontend/src/surfaces/developer/usx-settings.css` (12 changes)
- `frontend/src/surfaces/developer/gridcore-settings.css` (9 changes)
- `frontend/src/surfaces/developer/system-surface-dev.css` (4 changes)
- `frontend/src/surfaces/system/system-surface.css` (11 changes)
- `frontend/src/styles/system/story-forms.css` (4 changes)

**Font Size Mappings**:
- `13px` → `var(--pico-font-size, 1rem)` (base size)
- `12px` → `var(--pico-font-size-sm, 0.875rem)` (small)
- `11px` → `var(--pico-font-size-xs, 0.75rem)` (extra small)
- `12px` (hardcoded padding) → `var(--usx-spacing-sm)` (consistent spacing)

**Total Replacements**: 40 hardcoded font-size values standardized

## Next Steps

1. **Priority 1**: Fix card selection styling (visual bug)
2. **Priority 2**: Strip font-size overrides (consistency)
3. **Priority 3**: Unify color variable usage (style cleanliness)

## Testing Checklist for Next Pass

- [ ] Open System > Services tab - icon displays, no card highlighting
- [ ] Open Developer > USX Settings - all text sizes consistent with Pico cascade  
- [ ] Open Developer > GridCore Settings - cards don't show blue outline on hover
- [ ] Verify font sizes scale correctly with Global Settings > Base Font Size
- [ ] Check Pico CSS cascade is working (no inline overrides)

## Commits in This Session

1. `784b276` - refactor(settings): consolidate Global & Developer surface settings
2. `94fdf47` - feat(settings): complete uSystem Surface refactor + Developer panels
3. `eff9566` - docs: add comprehensive settings architecture reference
4. `3693332` - fix: Services icon + Story Forms full-page layout
5. `6e1dd1c` - fix: Services tab icon in header (hub)

## Architecture Notes

The 4-layer settings system is now architecturally sound:
- Each layer has independent state management
- All persist to localStorage correctly
- Developer settings are properly isolated
- Global Settings correctly cascades defaults

The remaining bugs are **purely CSS/styling** issues, not architectural problems.
