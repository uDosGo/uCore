# Zen Browser + Playwright Automation Toolchain

Date: 2026-06-22  
Status: Completed (UDW-024 through UDW-026)  
Owner: uCore dev agent  
Context: UI shell consolidation towards Zen Browser with Playwright as automation driver

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Cline CLI (Interactive TUI + Headless)                          │
│ - Plan/Act toggles, diffs, markdown rendering                   │
│ - --yolo for CI/CD, --json for structured output                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ├─→ Roundtable MCP (parallel models)
         │
         ├─→ Firewatch MCP (browser automation via WebDriver BiDi)
         │   └─→ Zen Browser (Firefox-based UI shell)
         │       ├─→ Playwright (programmatic control)
         │       └─→ Lightpanda CDP (headless performance tasks)
         │
         └─→ uCore MCP Bridge (skills, knowledge, secrets)
             ├─→ AppFlowy CLI (workspace management)
             ├─→ n8n (workflow orchestration)
             └─→ Zapier MCP (9000+ integrations)
```

---

## 🌐 Zen Browser as UI Shell

### Why Zen?
- **Firefox-based**: Direct Playwright support as first-class engine
- **Modern & Minimal**: Clean UI for dev workflows
- **Customizable**: Extensions and settings align with automation needs
- **Open**: Community-driven, no vendor lock-in

### Deployment
```bash
# macOS
brew install zen-browser

# Ubuntu/Linux
# Download from zen-browser.com

# Verify Playwright compatibility
npx playwright install firefox
```

---

## 🚀 Playwright: Primary Automation Driver

### Core Capabilities

#### 1. **Navigation & Interaction**
```javascript
// Python or JavaScript
browser = await firefox.launch();
page = await browser.newPage();

await page.goto('http://localhost:5173');
await page.click('button:has-text("Login")');
await page.fill('input[type="password"]', secret_password);
await page.screenshot({ path: 'screenshot.png' });

await browser.close();
```

#### 2. **Console Log Capture**
```javascript
page.on('console', message => {
  console.log(`[${message.type()}] ${message.text()}`);
});

// Render charts, trigger errors, capture logs
await page.evaluate(() => {
  window.renderChart({ data: [...] });
});
```

#### 3. **Form Filling & Data Entry**
```javascript
// Multi-step workflows
await page.fill('input[name="title"]', 'My Task');
await page.selectOption('select[name="priority"]', 'high');
await page.click('button[type="submit"]');
await page.waitForNavigation();
```

#### 4. **Accessibility & DOM Inspection**
```javascript
// Extract text content
const text = await page.textContent('h1');

// Query by role (accessible)
const button = await page.locator('role=button[name="Submit"]');

// Full page HTML
const html = await page.content();
```

---

## 🧩 Firewatch MCP: Agent-Integrated Browser Control

### What It Provides

Firewatch exposes Firefox/Zen capabilities as **MCP tools** directly to your AI agent.

#### Available Tools
- `browser_navigate(url)` — Open URL
- `browser_click(selector)` — Click element
- `browser_type(selector, text)` — Type into field
- `browser_screenshot()` — Capture page
- `browser_read_console()` — Extract console logs
- `browser_extract_text(selector)` — Get text content
- `browser_get_html()` — Full page HTML
- `browser_inspect(selector)` — Element details

### Installation

```bash
# Install Firewatch MCP globally
npm install -g firewatch-mcp

# Add to Cline settings (.vscode/settings.json or cline_settings.json)
{
  "mcpServers": {
    "firewatch": {
      "command": "firewatch-mcp",
      "args": ["--port", "3001"],
      "disabled": false
    }
  }
}
```

### Cline CLI Usage

```bash
cline "Use Firewatch to:
1. Navigate to http://localhost:5173
2. Click 'import' button
3. Extract all console errors
4. Screenshot current state
5. Return results as JSON"

# Output: Firewatch tools executed via MCP bridge
```

---

## ⚡ Lightpanda: High-Performance Headless Automation

### When to Use Lightpanda

Not for UI shell driving, but for dedicated headless tasks requiring extreme performance.

| Scenario | Lightpanda | Playwright |
|----------|------------|-----------|
| **Scale** | 10,000+ pages | Moderate workloads |
| **Memory** | 10x less | Standard |
| **Speed** | 10x faster | Slower for bulk tasks |
| **UI Needed** | ❌ No | ✅ Yes |
| **Setup** | CDP server | Direct launch |

### Architecture

Lightpanda runs a **Chrome DevTools Protocol (CDP) server** that Playwright can connect to:

```
Playwright Script
      ↓
CDP Client (port 9222)
      ↓
Lightpanda Browser Engine (Zig-native)
      ↓
Results
```

### Setup & Usage

```bash
# Install Lightpanda
git clone https://github.com/parsyapp/lightpanda
cd lightpanda && zig build

# Start CDP server
./zig-cache/bin/lightpanda --cdp-port 9222

# In separate terminal: run Playwright script
# (uses same Playwright API, but connects to Lightpanda)
```

**Python Example**:
```python
from playwright.async_api import async_playwright

async def scrape_with_lightpanda():
    # Connect to Lightpanda's CDP server instead of launching browser
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:9222')
        page = await browser.new_page()
        
        for url in urls_to_scrape:
            await page.goto(url)
            data = await page.evaluate('() => document.body.innerText')
            process(data)
        
        await browser.close()
```

### In Cline Automation

```bash
cline --yolo "High-scale AppFlowy export:
1. Start Lightpanda CDP server
2. Connect Playwright to port 9222
3. Navigate to AppFlowy workspace
4. Extract 5000+ pages to markdown
5. Compress and upload to S3"
```

**Performance Gain**:
- Standard Playwright: ~5 pages/sec → 16+ minutes for 5000 pages
- Lightpanda: ~50 pages/sec → 100 seconds for 5000 pages

---

## 🔗 Integration Points with uCore

### 1. **Zen + Playwright for AppFlowy Workflows**

```bash
# Cline TUI mode (interactive)
cline
# → /attach_context
# → Ask: "Extract AppFlowy vault to markdown via Zen"
# → Review plan → approve → execute via Firewatch MCP
```

### 2. **Headless Import Pipeline**

```bash
# Overnight job (Cline `--yolo` mode)
cline --yolo "Daily AppFlowy extraction:
1. Firewatch navigate to AppFlowy
2. Playwright screenshot for verification
3. Extract all documents to JSON
4. Import via /api/knowledge/import
5. Run brain_sync"

# Schedule via launchd at 4:00 AM
```

### 3. **Troubleshooting & Console Capture**

```bash
cline "Debug S300 UI:
1. Firewatch navigate to http://localhost:5173/s300
2. Capture console logs and screenshots
3. Extract any error messages
4. Suggest fixes"
```

---

## 🧠 ZenLink Extension (Lightweight Alternative)

Simple HTTP API wrapper for Firefox/Zen automation. Use only for one-off scripts.

### Installation
```bash
# Firefox Add-ons or build from source
git clone https://github.com/some/zenlink-extension
# Pack as .xpi and install
```

### API Endpoints
```bash
# Navigate
curl 'http://localhost:9999/navigate?url=https://example.com'

# Take screenshot
curl 'http://localhost:9999/screenshot' > page.png

# Get text content
curl 'http://localhost:9999/extract?selector=.title'

# Execute JS
curl -X POST 'http://localhost:9999/eval' -d 'code=document.title'
```

---

## 🛠️ Development Workflow Example

### Scenario: Import & Index New AppFlowy Vault

**Step 1: Interactive Planning (Cline TUI)**
```bash
cline
# In TUI, ask: "Plan an AppFlowy vault import workflow"
# Cline shows plan → review → approve
```

**Step 2: Firewatch Verification (Playwright)**
```bash
cline "Using Zen Browser, verify AppFlowy login:
1. Firewatch navigate to AppFlowy
2. Check if already logged in
3. If not, login via credentials from vault
4. Screenshot dashboard
5. Extract available workspaces"
```

**Step 3: Headless Extraction (Lightpanda)**
```bash
cline --yolo "High-scale extraction:
1. Export 500+ AppFlowy pages
2. Save to markdown directory
3. Upload to uCore knowledge base
4. Run indexing"
```

**Step 4: Monitoring & Logs**
```bash
cline --json "Check import status" | jq '.status'
# Output: NDJSON for programmatic consumption
```

---

## 📋 Comparison: Firewatch vs pi-fox vs ZenLink

| Feature | Firewatch MCP | pi-fox | ZenLink |
|---------|---|---|---|
| **MCP Integration** | ✅ Native | ⚠️ Via pi-fox wrapper | ❌ HTTP only |
| **Feature Set** | Comprehensive | 23 standard tools | Minimal |
| **AI Agent Support** | ✅ First-class | ✅ Good | ⚠️ Custom |
| **Debugging** | Rich logs | Standard | Basic |
| **Setup Complexity** | Low | Low | Very low |
| **Use Case** | Production AI workflows | Quick scripts | One-off tasks |
| **Recommendation** | **✅ Preferred** | Fallback | Legacy |

---

## 🚀 Recommended Deployment

### Local Development
```bash
# 1. Install browsers
npx playwright install firefox

# 2. Install Firewatch MCP
npm install -g firewatch-mcp

# 3. Add to Cline config
# See: ~/.vscode/extensions/cline-*/mcpServers config

# 4. Start Zen Browser
zen-browser

# 5. Use Cline TUI or CLI
cline           # Interactive
cline --yolo    # Headless
```

### Production (Overnight Jobs)
```bash
# launchd job (macOS)
# Run Cline `--yolo` mode at scheduled times
# Logs to uCore spool for monitoring
# Integrates with maintenance chain
```

---

## 📝 Integration Checklist

- [ ] Zen Browser installed and configured
- [ ] Playwright Firefox driver available
- [ ] Firewatch MCP registered in Cline config
- [ ] Lightpanda CDP server (optional) ready for scale tasks
- [ ] Cline CLI `--yolo` mode tested with Zen workflows
- [ ] Overnight AppFlowy import scheduled
- [ ] Spool monitoring for browser automation errors
- [ ] Documentation updated in Cline settings

---

## Next Steps

1. **Document in Cline Config**: Add Firewatch MCP server config to `.vscode/settings.json`
2. **Test Firewatch Tools**: Run sample workflows with Cline TUI
3. **Setup Lightpanda** (optional): For high-scale AppFlowy vault imports
4. **Integrate with n8n**: Connect Zen workflows to external systems
5. **Monitor Spool**: Track browser automation jobs in maintenance logs

