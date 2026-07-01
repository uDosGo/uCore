# Filepicker Integration Status

**Date:** 2026-07-01
**Status:** ✅ Vault Plate Integration Complete (Vue)

---

## Overview

The FilepickerSidebar has been fully integrated with the vault plate system.
It now dynamically loads vault layers from the backend, supports real-time
search via the unified library index, and provides proper file type icons,
vault layer badges, and empty/error states.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FilepickerSidebar                   │
│  ┌─────────────────────────────────────────────────┐│
│  │  Header: "Files" + [New] button                 ││
│  ├─────────────────────────────────────────────────┤│
│  │  UInput: Search (debounced, wired to library)   ││
│  ├─────────────────────────────────────────────────┤│
│  │  WorkspaceFilter (vault layer selector)         ││
│  │  BinderMissionFilter (binder/mission selector)  ││
│  ├─────────────────────────────────────────────────┤│
│  │  Index Status Banner (if not built)             ││
│  ├─────────────────────────────────────────────────┤│
│  │  File List:                                     ││
│  │  ┌───────────────────────────────────────────┐  ││
│  │  │ [icon] filename.ext          [Badge] [🔒]│  ││
│  │  │        ~/path/to/file.ext                  │  ││
│  │  └───────────────────────────────────────────┘  ││
│  │  ...                                             ││
│  ├─────────────────────────────────────────────────┤│
│  │  Empty State / Error State / Loading State      ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## Components Status (Vue)

| Component | Status | Location |
|-----------|--------|----------|
| `FilepickerSidebar.vue` | ✅ Vault-integrated | `frontend-vue/src/skills/molecules/FilepickerSidebar.vue` |
| `WorkspaceFilter.vue` | ✅ Vault layer aware | `frontend-vue/src/skills/molecules/WorkspaceFilter.vue` |
| `BinderMissionFilter.vue` | ✅ Dynamic binder population | `frontend-vue/src/skills/molecules/BinderMissionFilter.vue` |
| `api/client.ts` | ✅ Library + vault endpoints | `frontend-vue/src/api/client.ts` |
| `types/filepicker.ts` | ✅ Type definitions | `frontend-vue/src/types/filepicker.ts` |
| `backend/app/api/vault_api.py` | ✅ Vault topology API | `backend/app/api/vault_api.py` |
| `backend/app/api/routes.py` | ✅ Vault routes registered | `backend/app/api/routes.py` |

---

## Vault Layer Integration

The WorkspaceFilter now dynamically loads vault layers from the library index
stats API (`/api/library/stats`) and shows real file counts per layer.

**Vault Layers (from plate system):**

| Layer | Icon | Path | Badge Color |
|-------|------|------|-------------|
| User Vault | `mdi:account` | `~/Vault/` | Info (blue) |
| Shared | `mdi:account-group` | `~/Shared/` | Success (green) |
| Global Knowledge | `mdi:book-open-variant` | `~/Public/global-knowledge/` | Warning (yellow) |
| Published | `mdi:web` | `~/Public/doc-sites/` | Warning (yellow) |
| Code | `mdi:code-tags` | `~/Code/` | Error (red) |

---

## File Type Icons

The FilepickerSidebar maps file extensions to Iconify icons:

| Extension | Icon |
|-----------|------|
| `.md` | `mdi:language-markdown` |
| `.ts` / `.tsx` | `mdi:language-typescript` |
| `.vue` | `mdi:vuejs` |
| `.json` | `mdi:code-json` |
| `.yaml` / `.yml` | `mdi:file-code` |
| `.py` | `mdi:language-python` |
| `.js` / `.jsx` | `mdi:language-javascript` |
| `.css` | `mdi:language-css3` |
| `.html` | `mdi:language-html5` |
| `.txt` | `mdi:text` |
| `.csv` | `mdi:file-delimited` |
| `.sh` | `mdi:console` |
| `.svg` / `.png` / `.jpg` | `mdi:file-image` / `mdi:svg` |
| `.pdf` | `mdi:file-pdf` |
| Other | `mdi:file-document-outline` |

---

## API Endpoints

### Backend (new)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vault/topology` | GET | Vault layer topology with existence status |
| `/api/vault/layers` | GET | Vault layer definitions |

### Frontend Client

```typescript
// Library search with vault layer filter
ucoreApi.library.search(query, source?)

// Library stats (file counts per layer)
ucoreApi.library.stats()

// Build/rebuild the index
ucoreApi.library.build()

// Vault topology
ucoreApi.vault.topology()
ucoreApi.vault.layers()
```

---

## States Handled

| State | Behavior |
|-------|----------|
| **Loading** | Spinner + "Loading files..." text |
| **Error** | Error message + Retry button |
| **Empty (no query)** | "No files found in this vault layer" + Create button |
| **Empty (with query)** | 'No files matching "query"' + Create button |
| **Index not built** | Warning banner + Build Index button |
| **Read-only files** | Lock icon + reduced opacity |
| **Debounced search** | 300ms debounce on query input |

---

## Integration Status

| Integration Point | Status | Location |
|---|---|---|
| AppShell layout | ✅ Wired | `AppShell.vue` — `<FilepickerSidebar />` in sidebar `<aside>` |
| GlobalToolbar toggle | ✅ Wired | `GlobalToolbar.vue` — Finder button emits `toggle-sidebar` |
| Shell store | ✅ Wired | `stores/shell.ts` — `sidebarOpen` + `toggleSidebar()` |
| Backend vault API | ✅ Registered | `api/vault_api.py` — `/api/vault/topology`, `/api/vault/layers` |
| Library index API | ✅ Wired | `api/client.ts` — `ucoreApi.library.search()`, `stats()`, `build()` |

## Future Enhancements

1. **File Preview** — Preview files on hover/click
2. **Drag & Drop** — Drag files to surfaces
3. **Keyboard Navigation** — Full keyboard support
4. **Mobile Responsive** — Mobile-friendly layout
5. **File Operations** — Rename, delete, move files
6. **Recent Files** — Recently accessed files section
7. **Favorites** — Pin favorite files

---

## References

- [VAULT_PLATES_AND_DESTROY_SPEC.md](VAULT_PLATES_AND_DESTROY_SPEC.md) — Vault plate system
- [FILEPICKER_SIDEBAR_SPEC.md](FILEPICKER_SIDEBAR_SPEC.md) — Original spec
- [USX_LAYOUT_SYSTEM_SPEC.md](USX_LAYOUT_SYSTEM_SPEC.md) — Layout system
