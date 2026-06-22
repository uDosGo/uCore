# Surface Audit & Alignment Report (2026-06-22)

## Executive Summary

Frontend surface registration and visibility is **fragmented**:
- **Developer Surface**: Registered but visibility toggle is **inverted** in MissionControl
- **Documentation**: No dedicated surface; S600 Learning Hub is a SystemPage only
- **System Tab (Server)**: Conflates **Settings + System Links** in one tab
- **Abandoned**: USystemSurface route never registered but still exists in codebase
- **Gap**: No canonical place to access System Pages (S100-S899) as first-class surface cards

---

## Current Surface Registration Map

### Registered Surfaces (7 total)
| Surface | Route | Visibility | Notes |
|---------|-------|-----------|-------|
| Mission Control | `/` (default) | Always shown | Hub + dashboard |
| AssistUI | `/assistui/*` | Always shown | Full-page AI chat |
| GridUI | `/gridui/*` | Always shown | Terminal + Teletext |
| uCode | `/ucode/*` | Always shown | New: GridCore wrapper |
| BrowserUI | `/browserui/*` | HIDDEN from Surfaces tab | Has globe icon in toolbar |
| Server | `/server/*` | Always shown | Operations + ingest |
| Developer | `/developer/**` | **CONDITIONAL** (see issue below) | Dev-only environment |

### NOT Registered (but exists in codebase)
| Surface | Path | Status | Issue |
|---------|------|--------|-------|
| **USystemSurface** | `frontend/src/surfaces/system/USystemSurface.tsx` | **ABANDONED** | Never added to main.tsx routes; `/system/*` redirects to `/server?tab=settings` |

### System Pages (routed via SystemPage generic component)
- `/p{###}` → Surface status pages (P100-P899)
- `/s{###}` → System pages (S100-S899) with dedicated components
- Notable: **S600 "Learning Hub"** (Documentation) is only reachable via `/s600`, not as a card in UIHub

---

## Issue #1: Developer Surface Visibility Toggle is INVERTED

**Location**: `frontend/src/surfaces/missioncontrol/MissionControlSurface.tsx:49`

### Current Logic (BROKEN):
```typescript
const DEV_MODE_ENABLED = ['1', 'true', 'yes', 'on'].includes(
  String(import.meta.env.VITE_DEV_MODE || '').toLowerCase(),
)
const DEV_SURFACE_IDS: string[] = DEV_MODE_ENABLED ? [] : ['developer']
```

**Problem**: 
- When `VITE_DEV_MODE=1` → `DEV_MODE_ENABLED=true` → `DEV_SURFACE_IDS=[]` (Developer NOT hidden from surfaces, SHOWN)
- When `VITE_DEV_MODE=0` or unset → `DEV_MODE_ENABLED=false` → `DEV_SURFACE_IDS=['developer']` (Developer IS hidden)
- This contradicts the comment "All other surface cards ... Developer"

### Compare with main.tsx Route (CORRECT):
```typescript
<Route
  path="/developer/**"
  element={DEV_MODE_ENABLED ? <DeveloperSurface /> : <Navigate to="/" replace />}
/>
```
- This is **correct**: When `DEV_MODE_ENABLED=true`, show Developer; when false, redirect to home

### Fix:
```typescript
// Invert the logic: if DEV_MODE is OFF, then hide developer
const DEV_SURFACE_IDS: string[] = DEV_MODE_ENABLED ? ['developer'] : []
```

### Dev Mode Toggle Behavior:
- **Current**: Env var only (set at build time via `VITE_DEV_MODE`)
- **Desired**: Runtime toggle button in UIHub so user can show/hide Developer card without rebuild
- **Location to add**: UIHubManager or MissionControl toolbar

---

## Issue #2: Server "System" Tab Conflates Two Concerns

**Location**: `frontend/src/surfaces/userver/UServerSurface.tsx`

### Current Implementation:
The "System" tab on Server surface shows:
1. **SettingsPanel** (actual settings: Display, Font, Palette, Ollama, Providers)
2. **System page links** (S110, S120, etc. - just links, no real content)

### Root Cause:
- `USystemSurface.tsx` was designed to consolidate system tools (install/modules/feeds/story/pages/**settings**)
- But the route was **never registered** in `main.tsx`
- Instead, a **legacy redirect** was added: `/system/*` → `/server?tab=settings`
- SettingsPanel was extracted and moved to Server surface to avoid orphaning Settings

### Impact:
- Settings are in the right place (Server surface for operations)
- But **System Pages (S100-S899) are orphaned**:
  - No UI card to access them from UIHub
  - Only reachable via direct URL `/s100`, `/s200`, etc. or via SystemPage links scattered in codebase
  - S600 "Learning Hub" (Documentation) buried in this redirect chain

### Recommended Split:
1. **Settings** → Stays in Server "System" tab ✓ (correct)
2. **System Pages** → New "System" or "Tools" surface card in UIHub pointing to S100-S899 browser

---

## Issue #3: No "Documentation" or "Learning Hub" Card in UIHub

**Current State**:
- S600 Learning Hub exists but is **only accessible via**:
  - Direct URL: `/s600`
  - MissionControl "Documentation" link (hard-coded, not a card)
  - SettingsPanel links

**Should Be**: First-class surface card in UIHub alongside AssistUI, GridUI, etc.

### Alignment:
- MissionControl has: `{ icon: 'help', label: 'Documentation', color: '#a855f7', route: '/s600' }`
- But this is a **hard-coded link**, not a registry entry
- Should create a **DocumentationSurface** or expose S600 as a full surface card

---

## Issue #4: Abandoned USystemSurface Code

**Location**: `frontend/src/surfaces/system/USystemSurface.tsx`

### Status:
- Component exists with 5 tabs: install, modules, feeds, story, pages
- Routes defined in the component itself
- **Never registered** in `main.tsx`

### Why It Happened:
- When `/system/*` routes were consolidated into Server surface, USystemSurface was left in place
- Modern approach: merge its content into existing surfaces or create new cards

### Decision Options:
1. **Delete** if content is covered elsewhere (most likely)
2. **Resurrect** as a dedicated "System Tools" card if we want System Pages as first-class surface
3. **Merge** install/modules/feeds tabs into Server surface

---

## Other Surfaces in Codebase

### Status Check:
- ✓ **AssistUISurface** - Registered, visible
- ✓ **BrowserUISurface** - Registered, hidden from Surfaces tab (globe icon in toolbar)
- ✓ **DeveloperSurface** - Registered, visibility conditional (but toggle inverted)
- ✓ **GridUISurface** - Registered, visible
- ✓ **UCodeSurface** - Registered, visible (new)
- ✓ **UServerSurface** - Registered, visible
- ✓ **MissionControlSurface** - Registered, always default root
- ✗ **USystemSurface** - Exists but NOT registered

### Legacy/Removed:
- ✓ Archived: `frontend/src/surfaces/gridcore/GridCoreSurface.tsx` (redirects to `/gridui?panel=terminal`)
- ✓ Archived: `frontend/src/pages/S800Labs.tsx` (removed from active nav)
- ✓ Absorbed: ChatUISurface → AssistUI
- ✓ Absorbed: FloatingChatPanel → AssistUI
- ✓ Absorbed: ProseUI tabs → MissionControl

---

## Recommended Actions

### Priority 1: Fix Developer Visibility Toggle
1. Fix inverted logic in `MissionControlSurface.tsx:49`
2. Add runtime toggle button to UIHub toolbar
3. Sync visibility across both MissionControl and UIHubManager

**Files to update**:
- `frontend/src/surfaces/missioncontrol/MissionControlSurface.tsx`
- `frontend/src/UIHubManager.tsx`
- Optional: Add toggle UI component

### Priority 2: Decide on System Pages (S100-S899) Exposure
**Option A: Create "System" Surface Card** (Recommended)
- Register new "System Tools" surface card in UIHub
- Link to S100-S899 browser/selector
- Makes discoverable what's now hidden

**Option B: Keep S600 Only**
- Add S600 Learning Hub as dedicated "Documentation" card in UIHub
- Keep S100-S899 as internal/admin pages

**Option C: Resurrect USystemSurface**
- Register USystemSurface in main.tsx
- Add to UIHub cards with tabs for install/modules/feeds/story/pages/settings
- Risk: Duplicates Server surface functionality

### Priority 3: Documentation Surface Alignment
1. Promote S600 from hard-coded link to actual UIHub card
2. Or: Create DocumentationSurface wrapper if more content needed
3. Consider: Should "Documentation" be shown in first-row cards or secondary section?

### Priority 4: Clean Up Abandoned Code
1. Audit USystemSurface to see if any content should be salvaged
2. Delete if superseded by Server surface tabs
3. If keeping: register in main.tsx and add as UIHub card

---

## UIHub Card Order & Visibility Strategy

### Current CORE_SURFACE_IDS Order:
```typescript
['ucode', 'gridui', 'server', 'assistui', 'browserui', 'developer']
```

### Recommended Final Order:
```typescript
[
  'ucode',           // GridCore unified entry
  'gridui',          // Terminal/Teletext
  'assistui',        // AI Chat
  'server',          // Operations
  'documentation',   // Learning Hub (S600 + docs)
  'browserui',       // Web Reader (hidden from Surfaces tab, has globe icon)
  'developer',       // Dev environment (conditional visibility)
  'system-tools',    // Optional: S100-S899 browser (if creating)
]
```

### HIDDEN_FROM_SURFACES_TAB:
```typescript
['browserui', 'developer', 'system-tools']  // Optional: add system-tools if created
```

Rationale:
- browserui: has dedicated globe icon in toolbar
- developer: shown/hidden via DEV_MODE toggle
- system-tools: admin/advanced section below main row

---

## Next Steps Checklist

- [ ] Fix Developer visibility toggle inversion
- [ ] Add runtime dev mode toggle UI in UIHub
- [ ] Test dev mode true/false states
- [ ] Decide on System Pages strategy (A/B/C above)
- [ ] If Option A or B: Add Documentation/System card to UIHub
- [ ] If Option C: Register USystemSurface route in main.tsx
- [ ] Audit and clean up abandoned USystemSurface code
- [ ] Update HIDDEN_FROM_SURFACES_TAB based on final decision
- [ ] Update CORE_SURFACE_IDS order if adding new cards
- [ ] Smoke test all surfaces load without 404s
- [ ] Verify dev mode toggle works in UIHub
- [ ] Verify Documentation card visibility in UIHub

---

## Files Affected

### Core Registration:
- `frontend/src/main.tsx` (route registration)
- `frontend/src/UIHubManager.tsx` (card registry)
- `frontend/src/surfaces/missioncontrol/MissionControlSurface.tsx` (visibility logic)

### Surfaces:
- `frontend/src/surfaces/developer/DeveloperSurface.tsx` (visibility control)
- `frontend/src/surfaces/system/USystemSurface.tsx` (abandoned)
- `frontend/src/surfaces/system/SettingsPanel.tsx` (Settings content)

### System Pages:
- `frontend/src/pages/S600Learning.tsx` (Documentation)
- `frontend/src/SystemPage.tsx` (generic S-page router)

---

## References

- DEV_MODE logic: main.tsx:42-45, MissionControlSurface.tsx:44-49
- Server System tab: UServerSurface.tsx:1087, 1143
- SettingsPanel: frontend/src/surfaces/system/SettingsPanel.tsx
- USystemSurface: frontend/src/surfaces/system/USystemSurface.tsx (lines 1-50)
- S600 Learning: frontend/src/pages/S600Learning.tsx, SystemPage.tsx:63
- UIHub cards: UIHubManager.tsx:35-110
