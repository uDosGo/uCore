# Developer Surface — uCore Control Panel

The Developer Surface is a browser-based control panel that gives you a single pane of glass over your entire development ecosystem. It runs at `http://localhost:5175/developer` and replaces scattered terminal windows, manual status checks, and disconnected tooling with one unified interface.

---

## Getting Started

Open `http://localhost:5175/developer` in your browser. You will land on the **🎯 Control** tab — the default dashboard. It fetches live status from all services and displays them as color-coded badges. Green means online, red means offline.

### Lanes and Workspace Switching

- **System** lane: operates on uCore/uCode with protection guardrails.
- **Project** lane: operates on repositories discovered under `~/Code` and excludes system repositories (uCore/uCode and related system repos).
- The Control header includes **two selectors**:
	- Lane selector (`System` / `Project`)
	- Project repo selector (visible in `Project` lane)

Switching either selector updates backend workspace context via `POST /api/developer/workspace`.

### First Things to Check

1. **Status badges** — Are Ollama, Cline, and the Feed Pod showing green? If not, the quickest fix is the "🔄 Destroy/Rebuild" button in Quick Actions.
2. **Live Feed** — Empty? That's expected on a fresh start. Click "📥 Ingest Feed" to seed activity data.
3. **Cost Dashboard** — Should show `$0.00 / $2.00` (daily). Local Ollama tasks cost nothing.

---

## Tab Layout (Zen Flow)

The surface has 9 tabs arranged in a logical workflow: overview → execution → history/review → configuration.

| Tab | Purpose | When to Use |
|-----|---------|-------------|
| 🎯 **Control** | Unified dashboard — status, feed, agents, cost, mission | Default view, always open |
| 🤖 **Agents** | See which specialized agents are available | Before starting a task |
| 🧠 **Skills** | Browse and run 54 built-in skills | When planning work |
| 🕘 **History** | Action log, snapshots, and rollback tools | Before/after risky edits |
| 📊 **Dev Flow** | Track workflow runs and history | During execution |
| 📁 **Repos** | Manage repositories and branches | For git operations |
| 🔍 **Review** | See what changed before committing | Before pushing |
| ⚙️ **Settings** | Configure your environment | One-time setup |
| 🔌 **MCP** | Monitor MCP server connections | When something fails |

Each tab loads lazily — only the Control tab is eager-loaded so the dashboard appears instantly.

---

## Core Concepts

### Control Tab — The Cockpit

Think of the Control tab as the cockpit of a plane. At a glance you see:

- **Status Badges (top)** — Live health of Cline, OpenRouter, Hivemind, Roundtable, Ollama, Feed, Slate, and Budget. Click any badge to jump to the relevant detail tab.
- **Live Feed (left)** — Incoming activity from browser, email, messages, and alerts. Filter by source.
- **Agent Status (left)** — Which agents are available and how many Ollama models are loaded.
- **Cost Dashboard (right)** — Daily, weekly, and monthly API spend. Local Ollama usage is always $0.
- **Active Mission (right)** — Progress on the current sprint or `.tasker` item.
- **Bottom Bar** — Tasker summary, MCP server counts, and available Slates.
- **Quick Actions** — One-click buttons for health checks, offline recovery, restart backend, feed ingestion, cost export, and DESTROY/REBUILD.

The Control tab polls every 60 seconds for live updates. If the backend goes down, it shows your last known data with a retry button.

### Recovery Controls

- **Recover Offline Services** calls `POST /api/control/recover` to attempt targeted recovery (including Hivemind on port 8490) and then re-check service status.
- **Restart Backend** uses `POST /api/surfaces/popcorn/restart-backend`.

### Cost-Aware Routing — Local First, Premium as Fallback

uCore routes every AI task through a cost-aware decision engine defined in `backend/config/llm_router.yaml`:

| Complexity | Route | Cost |
|------------|-------|------|
| Simple (score ≤7) | Ollama — `qwen2.5-coder:3b` | $0 (local) |
| Complex (score >7) | OpenRouter — `claude-opus-4.7` | ~$0.15/task |
| Budget exhausted | Ollama — `qwen2.5-coder:3b` | $0 (forced) |

You can also explicitly route to any provider by calling the `route_task` skill with `"target_agent": "cline"`, `"ollama"`, `"hivemind"`, or `"roundtable"`.

### Task System (.tasker)

Tasks are defined as Markdown files in the `.tasker/` directory. Each task has:
- A UID (e.g., `task.enhance.001`)
- A title, description, complexity, and status
- Optional execution path preference (`local` or `cline`)

The **Dev Flow** tab shows all workflow runs and their status. Tasks executed through the `dev-mode-executor` skill automatically log to the spool and update the tasker.

---

## Daily Development Loop

### 1. Start — Select Lane and Workspace
Open the Control tab. Choose:
- `System` lane for uCore/uCode operations.
- `Project` lane for non-system repos under `~/Code`, then pick your target repo in the project selector.

Then confirm service status badges.

### 2. Plan — Review Agents and Skills
Switch to the **Agents** tab to see the 6 specialized agents (architect, dev, reviewer, debugger, docgen, gridsmith-dev) and their model assignments. Browse the **Skills** tab to see all 54 available skills.

### 3. Execute — Run a Task
Use the Quick Actions in the Control tab:
- **"📋 Create Task"** — Creates a new `.tasker` item
- **"📥 Ingest Feed"** — Seeds feed activity for testing
- **"🔄 Destroy/Rebuild"** — Resets Dev Mode to active Slate
- **"📊 Export Cost"** — Downloads cost report as JSON

For programmatic execution, call the `dev-mode-executor` skill:
```
POST /api/skills/dev-mode-executor/run
{"task_uid": "task.test.001", "mode": "auto"}
```

### 4. Review — Check Dev Flow
The **Dev Flow** tab lists all workflow runs with status and step progress. The **Review** tab shows git changes across your repos.

### 5. Iterate — Adjust and Repeat
Use the **Settings** tab to change configuration. The cost dashboard in Control updates automatically.

---

## Key Skills

| Skill | What It Does | When to Use |
|-------|-------------|-------------|
| `ecosystem-audit` | Catalogs all skills, routes, secrets, runtimes | Health checks |
| `ucore-index` | Generates live health reports with service checks | Before demo or deploy |
| `dev-mode-executor` | Full pipeline: analyze → route → consensus → execute → review → log | Running any task |
| `route_task` | Routes tasks to the best AI provider based on complexity | Cost-aware execution |
| `cline-invoke` | Invokes Cline CLI with DeepSeek credits | Complex multi-step tasks |
| `hivemind-consensus` | Multi-model deliberation (3+ models in parallel) | Architecture decisions |
| `roundtable-dispatch` | Parallel execution via specialized agents | Documentation and analysis |
| `gh-workflow-bridge` | Triggers GitHub Actions and creates PRs | CI/CD integration |
| `enhancement-planner` | Generates prioritized `.tasker` items from audits | Planning sprints |
| `docs_roundup` | Archives completed tasks and updates devlog | End of dev session |

All skills are accessible via `POST /api/skills/{skill_id}/run` with `X-User-Confirm: true` header for destructive operations.

---

## Security

- **Confirmation gates**: Mutating and destructive skills require explicit confirmation. Send `"confirm": true` in the JSON body or `X-User-Confirm: true` as a header.
- **API keys**: Stored in the AES-256-GCM encrypted `SecretStore` (`~/.ucore/secrets.enc`). Environment variables take precedence over the store.
- **Budget enforcement**: Daily ($2), weekly ($10), and monthly ($30) limits with automatic fallback to local models when exhausted.
- **Local-first**: All simple tasks route to Ollama by default. No data leaves your machine unless complexity demands premium cloud models.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Hivemind/Roundtable red | Hivemind not started on port 8490 | Click **Recover Offline Services** in Control |
| Feed empty | No feed data ingested yet | Click "📥 Ingest Feed" in Quick Actions |
| Cost showing $0 | Budget manager not initialized | Server restart required after config change |
| OpenRouter red | API key missing/invalid | Check key in SecretStore (`GET /api/secrets/env`) |
| Slate showing 0 templates | No templates seeded | Run `ecosystem-audit` to populate registry |
| Task not found | Wrong UID in dev-mode-executor | Verify UID matches `.tasker/` filename |

---

## API Endpoints Quick Reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/control/status` | Full ecosystem status (Control tab uses this) |
| `POST /api/control/recover` | Attempt recovery for currently offline services |
| `POST /api/surfaces/popcorn/restart-backend` | Restart backend process via orchestration |
| `POST /api/developer/workspace` | Set active lane/repo workspace context |
| `GET /api/skills` | List all 54 skills |
| `POST /api/skills/{id}/run` | Execute a skill |
| `GET /api/agents` | List specialized agents |
| `POST /api/chat` | Chat with any AI provider (Ollama, OpenRouter) |
| `GET /api/budget/status` | Budget usage and limits |
| `GET /api/workflows/runs` | Dev Flow run history |
| `GET /api/templates/list` | Available Slate templates |

---

## File Locations

| Path | Purpose |
|------|---------|
| `.tasker/` | Task definitions and sprint plans |
| `backend/config/llm_router.yaml` | Cost routing rules and provider config |
| `backend/config/agents.yaml` | Specialized agent definitions |
| `backend/app/skills/builtin/` | All 54 skill implementations |
| `~/.ucore/secrets.enc` | Encrypted API key store |
| `~/.config/hivemind/.env` | Environment variables for API keys |