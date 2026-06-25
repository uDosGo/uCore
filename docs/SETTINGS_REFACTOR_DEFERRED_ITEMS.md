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

## Remaining Bugs (Deferred)

### 1. USX Styles - Inconsistent Overrides

**Issue**: USX settings panel CSS has conflicting or overriding styles that don't match Pico CSS standard variables.

**Files to Review**:
- `frontend/src/surfaces/developer/usx-settings.css`
- `frontend/src/surfaces/developer/system-surface-dev.css`
- Check for hardcoded colors/sizes that override Pico cascade

**Action**: Strip inline style overrides, replace with Pico CSS variables (--pico-primary, --pico-color, etc.)

### 2. Card Selection Styling Bug

**Issue**: Card views sometimes display with blue outline/selection state on all cards, should only be on active.

**Root Cause**: Likely CSS `:focus-within`, `:focus-visible`, or `.outline` class being applied incorrectly.

**Files to Check**:
- `frontend/src/surfaces/system/system-surface.css` (`.system-card` class)
- Check for overly broad `:focus` or `:active` selectors
- Verify `.outline` Pico class isn't being applied to all cards

**Action**: 
```css
/* Likely issue - remove or scope correctly */
.system-card:focus-within {
  /* This might be firing on all cards */
}

/* Should be */
.system-card:focus-within:not(.no-focus) {
  /* Only on specific cards */
}
```

### 3. Font Sizes Not Standardized to USX Variables

**Issue**: Various panels using hardcoded font sizes (px) instead of Pico CSS size variables.

**Offending Patterns**:
- `font-size: 13px` → should be `font-size: var(--pico-font-size)`
- `font-size: 12px` → should be `var(--usx-font-size-sm)` or inherit
- Card titles, labels using hardcoded sizes

**Files to Audit**:
- `frontend/src/surfaces/developeroper/usx-settings.css`
- `frontend/src/surfaces/developer/gridcore-settings.css`
- `frontend/src/surfaces/developer/system-surface-dev.css`
- `frontend/src/surfaces/system/system-surface.css`

**Action**: Replace all hardcoded font-size values with Pico/USX cascade:
```css
/* Before */
.developer-panel-title {
  font-size: 13px;
}

/* After */
.developer-panel-title {
  font-size: var(--pico-font-size); /* or inherit from parent */
  font-weight: 600;
}
```

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
