> **Canonical version:** `/Users/fredbook/Code/uDocs/guides/qqcode-tui.md`
> This repo copy is kept for local reference; edits should be made in uDocs.

# QQCode TUI Integration Specification

**Version:** 1.0.0 | **Status:** Spec | **Target:** uCode Developer Surface

---

## 📋 Executive Summary

This specification defines the integration of **QQCode** as a lightweight TUI coding assistant within the uCode Developer Surface. QQCode serves as a fast, deterministic, and highly configurable CLI agent that complements the Hivemind orchestration layer by providing a **terminal-first interface** for quick tasks, research, and direct interaction with the codebase.

---

## 🎯 Use Cases

| Use Case | Description | When to Use QQCode Over Hivemind |
| :--- | :--- | :--- |
| **Quick Fixes** | Simple bug fixes, typos, small refactors | Task is < 50 lines, single file |
| **Codebase Navigation** | "Where is this function defined?", "Find all X" | Fast grep/ripgrep queries |
| **File Operations** | Read, edit, create files | Direct file manipulation without workflow overhead |
| **Shell Integration** | Run commands, build, test | Command-line operations with stateful terminal |
| **Research Tasks** | Evaluate new tools, test hypotheses | Exploratory work before Hivemind consensus |
| **Offline Mode** | Coding without network (Ollama) | When API is unavailable or costly |

---

## 🏗️ Architecture

### QQCode in the uCode Ecosystem

```
┌──────────────────────────────────────────────────────────────────┐
│                    uCode Developer Surface                      │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │  Cline Kanban UI    │    │  QQCode TUI (Embedded)         │ │
│  │  (Workflow View)    │    │  - Terminal-based interaction  │ │
│  └─────────────────────┘    │  - Real-time agent output      │ │
│                              │  - Command history            │ │
│                              │  - Auto-completion            │ │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    QQCode CLI (TUI Layer)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Interactive Chat                                       │  │
│  │  - Natural language queries                            │  │
│  │  - Task breakdown                                      │  │
│  │  - Tool calls (file ops, grep, bash, todo)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Advanced TUI Experience                                │  │
│  │  - `/` slash commands                                  │  │
│  │  - `@` file path autocompletion                        │  │
│  │  - Command history (up/down)                          │  │
│  │  - Multi-line input (Ctrl+J)                          │  │
│  │  - Beautiful themes (appflows)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    QQCode Core Engine                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Toolset     │  │ Model       │  │ Configuration           │ │
│  │ - grep      │  │ - OpenRouter│  │ - ~/.qqcode/config.toml │ │
│  │ - bash      │  │ - Ollama    │  │ - ~/.qqcode/.env       │ │
│  │ - read/write│  │ - Provider  │  │ - Skills/Agents         │ │
│  │ - todo      │  │   Fallback  │  │ - Theme support         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📝 QQCode Configuration Templates

### 1. Primary Configuration (`~/.qqcode/config.toml`)

```toml
# ~/.qqcode/config.toml
# QQCode Configuration for uCode Developer Standard

[general]
# Project-aware context scanning
project_aware = true
scan_submodules = true
ignore_patterns = [".git", "node_modules", "__pycache__", "*.pyc", ".venv", "target/", "build/"]

[ui]
# AppFlowy-inspired theme for consistency with uCode
theme = "appflows"
show_timestamps = true
enable_syntax_highlighting = true
enable_autocomplete = true
enable_file_path_suggestions = true
enable_command_history = true
history_limit = 1000

[models]
# Primary models (OpenRouter)
active_provider = "openrouter"
active_model = "openai/gpt-oss-20b"  # $0.02/M input

# Model fallback chain
[[models.provider]]
name = "openrouter"
api_key_env = "OPENROUTER_API_KEY"
models = [
    "openai/gpt-oss-20b",           # Primary - $0.02/M
    "nvidia/nemotron-3-super",      # Fallback - $0.09/M
    "meta-llama/llama-3.3-70b-instruct", # Free tier capable
]

[[models.provider]]
name = "ollama"
enabled = true
models = [
    "codellama:7b",
    "deepseek-coder:6.7b",
    "mistral:7b"
]
fallback_on_network_failure = true

[models.routing]
strategy = "cost-first"  # cost-first | performance-first | balanced
free_tier_first = true
provider_fallbacks = true
max_cost_per_request = 0.05
timeout = 60

[tools]
# Permission levels: always | ask | never
[tools.read_file]
permission = "always"

[tools.write_file]
permission = "ask"

[tools.edit]
permission = "ask"

[tools.bash]
permission = "ask"

[tools.grep]
permission = "always"

[tools.todo]
permission = "always"

[tools.skills]
permission = "ask"

# MCP Server integration
[tools.mcp]
enabled = true
servers = ["browser", "github", "secrets"]

# Skills on-demand loading
[tools.skills]
enabled = true
skill_dir = "~/.qqcode/skills"
load_on_demand = true

[mcp_servers]
# Browser automation (Lightpanda)
[[mcp_servers]]
name = "browser"
transport = "stdio"
command = "lightpanda"
args = ["--mcp", "--port=8930"]

# GitHub integration
[[mcp_servers]]
name = "github"
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]

# Secrets management
[[mcp_servers]]
name = "secrets"
transport = "stdio"
command = "hivemind"
args = ["secrets", "--mcp"]

[skills]
# Skill auto-discovery and registration
auto_discover = true
skill_dirs = [
    "~/.qqcode/skills",
    "~/.ucode/skills",
    "./.ucode/skills"
]

[performance]
enable_cache = true
cache_ttl_seconds = 300
max_cache_size_mb = 500

[logging]
enabled = true
log_file = "~/.qqcode/logs/qqcode.log"
log_level = "info"  # debug | info | warn | error
# Structured output mode for programmatic consumption
structured_output_enabled = true
structured_output_file = "~/.qqcode/logs/agent-events.jsonl"
```

### 2. Environment Configuration (`~/.qqcode/.env`)

```bash
# ~/.qqcode/.env
# API Keys for QQCode

# Primary provider (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-xxx...

# Fallback providers
ANTHROPIC_API_KEY=sk-ant-xxx...
GOOGLE_API_KEY=AIzaSy...

# Hivemind integration (optional)
HIVEMIND_ENABLED=false  # QQCode can run independently
HIVEMIND_API_KEY=hm_live_xxx...

# MCP server configs
GITHUB_TOKEN=ghp_xxx...
BROWSER_AUTH_TOKEN=xxx...

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b

# uCode workspace context
UCORE_WORKSPACE=~/Code/uCore
UCORE_VAULT=~/Code/uCore/vault
```

### 3. Skills Registry (`~/.qqcode/skills/registry.json`)

```json
{
  "version": "1.0.0",
  "skills": [
    {
      "id": "code-review",
      "name": "Code Review",
      "description": "Reviews code for style, bugs, security",
      "triggers": ["review", "pr", "pull request"],
      "priority": 1
    },
    {
      "id": "web-scrape",
      "name": "Web Scraper",
      "description": "Extracts content from web pages",
      "triggers": ["scrape", "extract", "fetch page"],
      "priority": 2
    },
    {
      "id": "refactor",
      "name": "Refactor Code",
      "description": "Refactors code to improve structure",
      "triggers": ["refactor", "restructure", "improve"],
      "priority": 1
    },
    {
      "id": "mcp-tools",
      "name": "MCP Tools",
      "description": "Access MCP servers for browser, github, secrets",
      "triggers": ["mcp", "browser", "github", "secrets"],
      "priority": 3
    }
  ]
}
```

---

## 🔧 Dual Output & Event Streaming

QQCode supports **Dual Output** for programmatic consumption. This is critical for integrating with the Developer Surface.

### Configuration

```toml
[output]
# Structured JSON event stream
structured_output_enabled = true
structured_output_file = "~/.ucode/logs/qqcode-events.jsonl"

# Event types to log
structured_output_events = [
    "user_input",
    "agent_response",
    "tool_call",
    "tool_result",
    "task_start",
    "task_complete",
    "error"
]

# For real-time integration with Developer Surface
# Pipe to a file descriptor that Developer Surface can read
structured_output_fd = 3
```

### Event Schema

```json
{
  "timestamp": "2026-06-28T10:00:00Z",
  "event_type": "tool_call",
  "session_id": "abc123",
  "task_id": "task.dev-flow.001",
  "data": {
    "tool": "grep",
    "args": {
      "pattern": "TODO",
      "path": "src/"
    },
    "result": "...",
    "duration_ms": 245,
    "cost": 0.0001
  }
}
```

---

## 🚀 Installation & Setup

### One-Line Install (Recommended)

```bash
# Linux and macOS
curl -LsSf https://raw.githubusercontent.com/qnguyen3/qqcode/main/scripts/install.sh | bash
```

### Via `uv` (Python Package Manager)

```bash
uv tool install qqcode
```

### Via `pip`

```bash
pip install qqcode
```

### Configuration First Run

```bash
# Navigate to uCore workspace
cd ~/Code/uCore

# Start QQCode (generates default config)
qqcode

# First run will prompt:
# - API key (if not configured)
# - Workspace context
# - Theme selection
```

---

## 🔄 Integration with uCode Developer Surface

### Developer Surface Tabs

```typescript
// frontend/src/surfaces/developer/DeveloperSurface.tsx

const TABS = [
  { id: 'kanban', label: '📋 Kanban', component: ClineKanban },
  { id: 'qqcode', label: '💻 QQCode', component: QQCodeTerminal },
  { id: 'hivemind', label: '🧠 Hivemind', component: HivemindDashboard },
  { id: 'mcp', label: '🔌 MCP', component: MCPServerView },
];
```

---

## 🔍 Verification Checklist

- [ ] **QQCode installed** via `curl` or `uv`
- [ ] **Configuration** files created in `~/.qqcode/`
- [ ] **API keys** configured in `~/.qqcode/.env`
- [ ] **Skills** available in `~/.qqcode/skills/`
- [ ] **MCP servers** configured and running
- [ ] **Theme** matches uCode Developer Surface (appflows)
- [ ] **Dual output** enabled for event streaming
- [ ] **Developer Surface** shows QQCode tab
- [ ] **Terminal** connects to QQCode process
- [ ] **Event stream** visible in Developer Surface logs

---

## 📚 Resource Links

- **QQCode GitHub**: https://github.com/qnguyen3/qqcode
- **QQCode Documentation**: https://github.com/qnguyen3/qqcode#readme
- **Mistral Vibe (Parent Project)**: https://github.com/mistralai/vibe
- **uCode Developer Surface**: `/server?tab=qqcode`

---

**Version:** 1.0.0 | **Next Review:** 2026-07-28 | **Owner:** Developer Productivity Team