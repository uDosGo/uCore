# Filepicker Sidebar Specification

**Date:** 2026-06-28  
**Status:** Implementation Started  
**Goal:** Replace VaultSidebar with unified FilepickerSidebar using three-filter-box system

---

## Overview

The FilepickerSidebar provides a unified, modular file picker system with three filter boxes:
1. **Workspace Filter** - Select vault layers (User, Shared, Global, Code, Public)
2. **Binder/Mission Filter** - Filter by binder/mission or search tags
3. **Search/Tags** - Search across files and filter by tags

---

## Component Architecture

### Main Component: FilepickerSidebar

**File:** `frontend/src/components/FilepickerSidebar.tsx`

**Props:**
```typescript
interface FilepickerSidebarProps {
  open: boolean
  onFileSelect?: (file: FileEntry) => void
  onNewFile?: (binderId: string) => void
  compact?: boolean
}
```

### Sub-Components

#### 1. WorkspaceFilter
**File:** `frontend/src/components/WorkspaceFilter.tsx`

**Purpose:** Workspace selection with toggle buttons

**Features:**
- Dropdown for quick selection
- Toggle buttons for multi-select
- Icons for each workspace

**Workspaces:**
- User Vault (👤)
- Shared Vault (🤝)
- Global Vault (🌍)
- Code Repos (💻)
- Public Sites (📢)

#### 2. BinderMissionFilter
**File:** `frontend/src/components/BinderMissionFilter.tsx`

**Purpose:** Binder/Mission selection with chip selector

**Features:**
- Dropdown for quick selection
- Chip buttons for active binders
- Custom binder input
- Tag filtering

**Binder Options:**
- All Binders
- Active Projects
- Tasks/Missions
- Inbox
- Archive

#### 3. Search/Tags Box
**Purpose:** Search and tag filtering

**Features:**
- Search input with clear button
- Tag pills display
- Real-time filtering

---

## Integration Plan

### Phase 1: Update VaultSidebar to Use New Components

**File:** `frontend/src/components/VaultSidebar.tsx`

**Changes:**
1. Import new sub-components
2. Replace existing binder selector with `BinderMissionFilter`
3. Add search functionality
4. Keep existing file list and binder data

### Phase 2: Update All Surfaces

**Files to Update:**
- `frontend/src/surfaces/assistui/AssistUISurface.tsx`
- `frontend/src/surfaces/browserui/BrowserUISurface.tsx`
- `frontend/src/surfaces/dashboard/DashboardSurface.tsx`
- `frontend/src/surfaces/developer/DeveloperSurface.tsx`
- `frontend/src/surfaces/snackmachine/SnackMachineSurface.tsx`
- `frontend/src/surfaces/system/USystemSurface.tsx`
- `frontend/src/surfaces/ucode/UCodeSurface.tsx`
- `frontend/src/surfaces/userver/UServerSurface.tsx`
- `frontend/src/surfaces/workflow/WorkflowSurface.tsx`

**Changes:**
- Replace `<VaultSidebar>` with `<FilepickerSidebar>`
- Update props if needed
- Test file selection functionality

### Phase 3: Backend Integration

**File:** `backend/app/services/vault_file_discovery.py`

**Changes:**
1. Implement `discover_files()` API endpoint
2. Implement `apply_filters()` API endpoint
3. Add caching for file discovery
4. Support real-time search

---

## Styling

**File:** `frontend/src/styles/filepicker-sidebar.css`

**Features:**
- Responsive design
- Compact mode support
- Dark theme compatible
- Smooth transitions

---

## Migration Path

### Step 1: Create FilepickerSidebar Component
- ✅ Create `FilepickerSidebar.tsx`
- ✅ Create `WorkspaceFilter.tsx`
- ✅ Create `BinderMissionFilter.tsx`
- ✅ Create `filepicker-sidebar.css`

### Step 2: Update VaultSidebar
- ⏳ Replace binder selector with `BinderMissionFilter`
- ⏳ Add search functionality
- ⏳ Keep existing file list

### Step 3: Update All Surfaces
- ⏳ Replace `<VaultSidebar>` with `<FilepickerSidebar>`
- ⏳ Test file selection
- ⏳ Verify search functionality

### Step 4: Backend API
- ⏳ Implement file discovery endpoint
- ⏳ Implement filtering endpoint
- ⏳ Add caching

---

## Benefits

1. **Modularity**: Each filter box is a separate, reusable component
2. **Flexibility**: Easy to add/remove filter boxes
3. **Consistency**: Unified interface across all surfaces
4. **Search**: Built-in search and tag filtering
5. **Performance**: Caching and efficient filtering

---

## Future Enhancements

1. **Real-time Search**: Debounced search with live filtering
2. **File Preview**: Preview files on hover
3. **Drag & Drop**: Drag files to surfaces
4. **Keyboard Navigation**: Full keyboard support
5. **Mobile Responsive**: Mobile-friendly layout