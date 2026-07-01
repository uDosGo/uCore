# AppFlowy Integration Methods & Toolchain

Date: 2026-06-22  
Status: Completed (UDW-024 through UDW-026 closure)  
Owner: uCore team

---

## Overview

AppFlowy integration for uCore spans data management, MCP bridges, automation, and publishing. This document maps recommended tools and methods for each use case.

## 📂 Managing Data and Workspaces

### Workspace Data Location
- **Settings → Manage Data**: Shows local file storage location on disk
- **Manual Backup**: Copy data folder to external storage
- **Data Migration**: Copy folder and replace default location (manual process)

### Programmatic Workspace Management
Use **`appflowy-cli`** for scripting:
```bash
# List workspaces
appflowy-cli workspaces

# Switch workspace
appflowy-cli use <workspace_id>

# Backup to ZIP
appflowy-cli backup

# Import data
appflowy-cli import <source>

# Create note from CLI
appflowy-cli save "Note title"
```

---

## 🔌 MCP & Extension Integration

### Foundation: appflowy-mcp
The **`appflowy-mcp`** server is the core MCP implementation. All higher-level tools build on top of it.

### Integration Paths

#### 1. **appflowy-cli** (Command-Line)
Primary tool for automation and scripting.
```bash
# Authentication
appflowy-cli login
appflowy-cli logout

# Programmatic import/export
appflowy-cli export <view_id> --format json
appflowy-cli import <file> --workspace <id>

# Workspace operations
appflowy-cli save "Quick note"
appflowy-cli list-docs
```

**Use in uCore**: Schedule via cron/launchd with Cline CLI `--yolo` mode
```bash
# Daily AppFlowy import at 4:00 AM (via launchd)
0 4 * * * /path/to/cline --yolo "Run appflowy-cli import from vault"
```

#### 2. **Zapier Integration** (Workflow Automation)
Connect AppFlowy to 9,000+ apps via Zapier MCP server.

**Recommended Workflows**:
- Trigger: "Row Added to Database" → Action: "Post to Slack"
- Trigger: "Document Updated" → Action: "Create GitHub Issue"
- Trigger: "Custom Event" → Action: "Create AppFlowy Item"

#### 3. **n8n Node** (Visual Workflow Builder)
Community node for low-code/no-code automation.

**Setup**:
```bash
npm install n8n-nodes-appflowy
# or use n8n Cloud with prebuilt node
```

**Workflow Examples**:
- AppFlowy row → Process → Zapier → External system
- External webhook → n8n trigger → Create AppFlowy database item
- Schedule: Every hour → Query AppFlowy → Slack notification

**Recommended**: Combine n8n + Zapier for multi-step workflows

---

## ✍️ Publishing & Sharing

AppFlowy provides built-in sharing controls:

### Make View Public
- Select view (document, database, etc.)
- Settings → Publish
- Get shareable link (read-only)
- Anyone with link can access

### Share with Specific Users
- Settings → Share
- Granular permissions:
  - **Read Only**: View content only
  - **Read & Write**: Edit content
  - **Full Access**: Manage view + permissions

---

## 🌐 UI Automation: Zen Browser + Playwright

For uCore dev workflows that require UI control and automation.

### Recommended Stack

#### 1. **Playwright + Firefox**
Playwright natively supports Firefox (Zen is Firefox-based).

**Basic Setup**:
```bash
npm install -D playwright
npx playwright install firefox
```

**Python Equivalent**:
```bash
pip install playwright
playwright install firefox
```

**Cline CLI Integration**:
```bash
cline "Use Playwright to automate Firefox/Zen: 
- Navigate to AppFlowy
- Extract console logs
- Fill forms
- Take screenshots"
```

#### 2. **Firewatch MCP** (Recommended for Agent Integration)
MCP server for automating Firefox/Zen via WebDriver BiDi protocol.

**What It Provides**:
- Navigation and page interaction
- Text extraction and inspection
- Console log capture
- Screenshot capture
- Full integration with AI agent workflows

**Setup**:
```bash
# Install Firewatch MCP
npm install -g firewatch-mcp

# Use in Cline or Roundtable
# Agent gains: "open", "click", "type", "screenshot", "read_logs" tools
```

#### 3. **pi-fox Extension** (Simpler Alternative)
Lightweight Firefox extension wrapper around Playwright.

**Provides**:
- 23 browser automation tools
- Console log capture
- Convenient for one-off scripts

**When to Use**:
- Quick automation scripts
- No need for full Playwright complexity

---

## ⚡ High-Performance Headless Automation: Lightpanda

**Not** for UI shell driving, but for dedicated headless tasks.

**What It Is**:
- Browser built from scratch in Zig
- ~10x faster than Chrome headless
- ~10x less memory
- No UI rendering

**When to Use**:
- Large-scale scraping
- Automated testing of headless workflows
- Resource-intensive automation

**Integration with Playwright**:
```javascript
// Lightpanda's CDP server + Playwright as client
const browser = await chromium.connect('http://localhost:9222');
// Same Playwright API, but powered by Lightpanda
```

**In Cline CLI**:
```bash
cline --yolo "Use Lightpanda for high-scale import processing:
- Launch CDP server
- Connect Playwright
- Scrape 1000+ pages
- Log results"
```

---

## 🧩 ZenLink Extension (Quick Scripting)

Simpler Firefox/Gecko extension for basic automation.

**When to Use**:
- One-off scripts
- Don't need Playwright's full feature set
- Quick HTTP API for browser control

**Typical Flow**:
```bash
curl http://localhost:9999/navigate?url=https://example.com
curl http://localhost:9999/screenshot > page.png
```

---

## 📊 Recommended Tool Matrix

| Use Case | Recommended Tool | Rationale |
|----------|------------------|-----------|
| **AppFlowy Data Sync** | `appflowy-cli` + Cline `--yolo` | Scheduled, headless, reliable |
| **Workflow Automation** | n8n + Zapier | Visual builder, 9000+ integrations |
| **Dev Agent Browser Control** | **Firewatch MCP** | Deep AI agent integration, feature-rich |
| **Simple Browser Tasks** | Playwright Firefox | Mature, well-supported |
| **Quick Scripts** | pi-fox or ZenLink | Lightweight, no setup |
| **High-Scale Scraping** | Lightpanda + Playwright CDP | Performance-critical |

---

## 🚀 Cline CLI + uCore Integration

### Overnight Automation Example

```bash
# /Users/fredbook/.config/launchd/com.udos.appflowy-import.plist
# Run daily at 4:00 AM

<key>ProgramArguments</key>
<array>
  <string>/usr/local/bin/cline</string>
  <string>--yolo</string>
  <string>Run AppFlowy vault sync: 
    1. appflowy-cli export vaults --format markdown
    2. Import into uCore knowledge base
    3. Run tasker_sync
    4. Log to spool</string>
</array>
```

### Interactive Mode for Debugging

```bash
cline  # Opens TUI
# In TUI: /attach_context → loads CONTEXT.md + wisdom.md
# Ask: "Check AppFlowy index coverage"
# Review Plan → approve with Tab → execute
```

---

## 📝 Summary Table

| Feature | Implementation | Status |
|---------|---|---|
| AppFlowy data import | `appflowy-cli` in Cline `--yolo` | ✅ Done |
| Workspace management | `appflowy-cli use` + scripts | ✅ Done |
| MCP foundation | `appflowy-mcp` server | ✅ Done |
| Workflow automation | n8n + Zapier integration | ✅ Recommended |
| UI automation (Zen) | **Firewatch MCP** + Playwright | ✅ Recommended |
| Publishing/sharing | Built-in AppFlowy UI | ✅ Done |
| Scheduling | Cline CLI + launchd/cron | ✅ Done |

---

## Next Steps

1. **Document MCP Configuration**: Add Firewatch MCP setup to Cline extension config
2. **n8n Workflow Templates**: Create example workflows for common AppFlowy → uCore pipelines
3. **Lightpanda Integration**: Add CDP setup docs if large-scale scraping becomes needed
4. **UI Wiring**: Wire AppFlowy import/export into System Surface (Phase 8)
