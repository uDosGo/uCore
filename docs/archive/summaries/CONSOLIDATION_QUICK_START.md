# Consolidation Quick Start — Implementation Guide

## 🚀 Day 1: Create `.usx-card-header` Utility

### Step 1: Add to `usx-layout-system.css`

```css
/* ═══════════════════════════════════════════════════════════════
   .usx-card-header — Canonical card/panel header utility
   Use this instead of surface-specific .{surface}-card-header
   ═══════════════════════════════════════════════════════════════ */

.usx-card-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--pico-border-color, #30363d);
  background: var(--pico-card-sectioning-background-color, #1c2128);
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
}

.usx-card-header-title {
  flex: 1;
  min-width: 0;
}

.usx-card-header-actions {
  margin-left: auto;
  display: flex;
  gap: var(--usx-spacing-sm);
}
```

### Step 2: Update React Components

**Before**:
```tsx
<div className="developer-panel-header">
  <Icon name="settings" />
  <h3>Settings</h3>
</div>
```

**After**:
```tsx
<div className="usx-card-header">
  <div className="usx-card-header-icon">
    <Icon name="settings" />
  </div>
  <div className="usx-card-header-title">
    <h3>Settings</h3>
  </div>
</div>
```

### Step 3: Remove Old CSS

Delete from `surfaces/developer.css`:
```css
❌ DELETE: .developer-panel-header { ... }
```

Repeat for:
- `hub/settings.css` → `.hub-settings-card-header`
- `hub/dashboard.css` → `.hub-card-header`
- (All 15 duplicate implementations)

---

## 🚀 Day 2: Migrate Hardcoded Font-Sizes

### Priority Files (in order)

#### 1. `surfaces/developer.css` (23 hardcoded)

**Find & Replace**:
```
❌ BEFORE → ✅ AFTER

font-size: 0.9em → font-size: var(--usx-font-size-body)
font-size: 12px → font-size: var(--usx-font-size-body)
font-size: 0.75em → font-size: var(--usx-font-size-meta)
font-size: 0.95rem → font-size: var(--usx-font-size-h3)
font-size: 1.1em → font-size: var(--usx-font-size-h2)
```

**Affected Classes**:
- `.developer-chat-prose`
- `.developer-panel-header`
- `.developer-repo-item-name`
- `.developer-file-preview-subtitle`
- (Continue for all 23)

#### 2. `hub/settings.css` (12 hardcoded)

```
font-size: 0.95rem → var(--usx-font-size-h3)
font-size: 0.9rem → var(--usx-font-size-body)
font-size: 0.75em → var(--usx-font-size-meta)
```

#### 3. `surfaces/ucode.css` (7 hardcoded)

```
font-size: 12px → var(--usx-font-size-body)
font-size: 0.875rem → var(--usx-font-size-body)
```

#### 4. `assistui.css` (5 hardcoded)

```
font-size: 1rem → var(--usx-font-size-body)
font-size: 0.9rem → var(--usx-font-size-body)
```

---

## 🚀 Day 3: Consolidate Icon Rules

### Action: Audit Icon Declarations

**Search in all CSS files**:
```
grep -r "\..*svg\s*{\s*font-size" frontend/src/
```

**Expected Output** (sample):
```
developer.css:234:  .developer-repo-btn svg { font-size: 1em; }
hub/settings.css:89: .hub-settings-card-header svg { font-size: 1em; }
surfaces/assistui.css:145: .assistui-icon svg { font-size: 1em; }
```

### Action: Move to `usx-icons.css`

For each duplicate found, check if it's already in `usx-icons.css`:

**If YES** (most cases):
```css
/* Already in usx-icons.css, so DELETE from surface CSS */
❌ DELETE from developer.css:
.developer-repo-btn svg { font-size: 1em; }
```

**If NO** (rare):
```css
/* Add to usx-icons.css, then delete from surface */
✅ ADD to usx-icons.css:
.my-custom-btn svg { font-size: 1em; }

❌ DELETE from surface.css:
.my-custom-btn svg { font-size: 1em; }
```

---

## Testing Checklist

### Mobile (≤767px)
```
✅ Body text readable (not too small)
✅ Sidebar fonts match body size
✅ Large icons: 1.625em (not oversized)
✅ Card headers: Proper spacing
✅ No horizontal overflow
```

### Tablet (768-1024px)
```
✅ Icons: 2.0em (0.8× scaling)
✅ Typography: Proportional to mobile
✅ Layout: 2-column grid on cards
```

### Desktop (1025px+)
```
✅ Icons: 2.5em (full 10-foot scale)
✅ Typography: Full body size
✅ Layout: Multi-column grid
```

---

## Template: Font-Size Migration

Use this template for each CSS file:

```css
/* ═══════════════════════════════════════════════════════════════
   MIGRATION COMPLETE: All hardcoded font-sizes replaced with USX variables
   Last updated: [DATE]
   ═══════════════════════════════════════════════════════════════ */

❌ BEFORE:
.my-class {
  font-size: 0.9em;  ← Hardcoded
  font-size: 12px;   ← Hardcoded
  font-size: 0.75rem; ← Hardcoded
}

✅ AFTER:
.my-class {
  font-size: var(--usx-font-size-body);  ← Variable
}

.my-class-meta {
  font-size: var(--usx-font-size-meta);  ← Variable (0.8× body)
}

.my-class-heading {
  font-size: var(--usx-font-size-h3);  ← Variable
}
```

---

## Common Font-Size Mappings

| What You Have | What It Should Be | Reason |
|---------------|------------------|--------|
| `14px`, `12px`, `1rem`, `0.9em` | `var(--usx-font-size-body)` | Primary text |
| `11.2px`, `0.8em`, `0.875rem` | `var(--usx-font-size-meta)` | Secondary/meta |
| `20px`, `1.25rem`, `1.2em` | `var(--usx-font-size-h3)` | Subheadings |
| `24px`, `1.5rem`, `1.5em` | `var(--usx-font-size-h2)` | Section headers |
| `32px`, `2rem`, `2em` | `var(--usx-font-size-h1)` | Page titles |

---

## Verification Commands

### Check for remaining hardcoded font-sizes:
```bash
grep -r "font-size.*:[^v]" frontend/src/styles/ | grep -v "usx-" | grep -v "//" | head -20
```

Expected output after migration: Almost none (only intentional grid-specific ones)

### Verify USX variables are used:
```bash
grep -r "var(--usx-font-size" frontend/src/styles/ | wc -l
```

Expected: High count (200+)

### Check for remaining duplicate icon rules:
```bash
grep -r "svg.*font-size.*1em" frontend/src/styles/ | grep -v usx-icons.css
```

Expected: Minimal (only surface-specific overrides)

---

## Before/After Checklist

### Phase 1 Complete When:
- [ ] `.usx-card-header` utility added
- [ ] 15 surface card-header definitions removed
- [ ] 68 hardcoded font-sizes migrated to variables
- [ ] 40+ redundant icon rules removed from surfaces
- [ ] All 4 priority files updated (developer, settings, ucode, assistui)
- [ ] Tests pass on mobile/tablet/desktop
- [ ] CSS bundle size reduced (measure with `npm run build`)

### Metrics:
```
Lines of CSS saved: ~250-300
Files modified: 4 primary + 10+ surface files
Time invested: 2-3 days
Maintenance time saved: Ongoing (updates to 1 place instead of 15+)
```

---

## Rollback Plan

If something breaks:

1. **Git revert last commit**
   ```bash
   git revert [commit-hash]
   ```

2. **Check component rendering**
   - Test each surface in browser
   - Verify no console errors
   - Check localStorage for cached styles

3. **Clear browser cache**
   ```bash
   # In DevTools: Application → Clear storage
   ```

4. **Restart dev server**
   ```bash
   npm run dev
   ```

---

## Success Indicators

✅ All surfaces look consistent  
✅ Font sizes scale correctly on mobile/tablet/desktop  
✅ No hardcoded font-sizes in surfaces (only USX variables)  
✅ Icon sizes match their parent text sizes  
✅ Large icons scale responsively (1.625em mobile → 2.0em tablet → 2.5em desktop)  
✅ CSS bundle size reduced by ~250 lines  

---

**Status**: Ready for Phase 1 implementation  
**Estimated Duration**: 2-3 days  
**Next Step**: Start with `.usx-card-header` utility creation
