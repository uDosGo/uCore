---

## ✅ Phase 1: Foundation & Orchestration (Week 1-2)

### 1.1 Core Orchestrator Setup

- [ ] **Install Cline CLI** as the primary orchestrator
  - [ ] `npm install -g @cliner/cli`
  - [ ] Configure with OpenRouter API key
  - [ ] Enable `cline kanban` mode for UI
  - [ ] Set up project-specific workflows
- [ ] **Configure Cline's autonomous mode**
  - [ ] Set auto-approve policies per task type
  - [ ] Configure `cline.toml` for project standards
  - [ ] Enable dynamic tool retrieval (preserves tokens)
  - [ ] Test with sample task: `cline "Fix the TODO in src/main.rs"`

### 1.2 Developer Surface Integration

- [ ] **Integrate Cline Kanban UI** into uCode's Developer Surface
  - [ ] Embed `cline kanban` as a tab/panel
  - [ ] Enable real-time diff viewing
  - [ ] Add cost tracking widget (per task)
  - [ ] Link tasks to uCode's agent router (port 8485)
- [ ] **Add task complexity estimation**
  - [ ] Implement `TaskEstimator` service
  - [ ] Classify tasks as `simple`, `medium`, `complex`
  - [ ] Expose via `/api/tasks/estimate`

---

## ✅ Phase 2: Smart Routing & Cost Control (Week 2-3)

### 2.1 Router Installation

- [ ] **Deploy Flow-LLM-Router** (or OmniRoute)
  - [ ] `pip install flow-llm-router`
  - [ ] Configure with OpenRouter credentials
  - [ ] Set up model pools:
    - `cheap_pool`: `gpt-oss-20b`, `gemini-3-flash`, `deepseek-v4-flash`
    - `premium_pool`: `claude-opus-4.5`, `gpt-5`, `gemini-3-pro`
  - [ ] Define routing rules per task complexity
- [ ] **Add cost analytics**
  - [ ] Configure `cost_tracker` middleware
  - [ ] Log per-task costs to `/api/spool`
  - [ ] Set budgets and alerts
  - [ ] Build dashboard in Developer Surface

### 2.2 Model Selection Automation

- [ ] **Create routing decision flow**
  ```python
def route_task(task_complexity, estimated_tokens):
    if task_complexity == "simple" and estimated_tokens < 5000:
        return "cheap_pool"
    elif task_complexity == "complex" or estimated_tokens > 20000:
        return "premium_pool"
    else:
        return "balanced_pool"  # mix of both
```
- [ ] **Implement automatic model switching**
  - [ ] Retry with cheaper model if premium fails
  - [ ] Fallback to premium if cheap model times out
- [ ] **Add OpenRouter `:floor` optimization**
  - [ ] Append `:floor` to all model IDs
  - [ ] Set `max_price` per request type

---

## ✅ Phase 3: Token Optimization (Week 3-4)

### 3.1 Context Compression & Caching

- [ ] **Deploy TOON-context-mcp-server**
  - [ ] Install: `npm install -g toon-context-mcp`
  - [ ] Configure to intercept file requests
  - [ ] Set up TOON format for JSON/CSV files
  - [ ] Expected savings: 30-60% on structured data
- [ ] **Deploy Token Optimizer MCP**
  - [ ] `pip install token-optimizer-mcp`
  - [ ] Initialize SQLite cache database
  - [ ] Configure cache TTLs (1 hour default)
  - [ ] Test caching with repeated API calls
- [ ] **Measure baseline token usage**
  - [ ] Run 10 sample tasks without optimization
  - [ ] Record token count per task
  - [ ] Compare with optimized runs (target: 60-90% savings)

### 3.2 Smart Context Injection

- [ ] **Implement dynamic tool retrieval**
  - [ ] Replace static tool loading with `get_tools_for_task()`
  - [ ] Index all available tools in agent router
  - [ ] Cache tool descriptions
  - [ ] Update Cline configuration: `dynamic_tools = true`
- [ ] **Add "education" memory**
  - [ ] Implement project-wide memory store
  - [ ] Cache common patterns (e.g., "use our API wrapper")
  - [ ] Auto-inject from memory into prompts
  - [ ] Expected savings: 20-30% on repetitive tasks

---

## ✅ Phase 4: Workflow Automation (Week 4-5)

### 4.1 Task Automation Pipeline

- [ ] **Set up task scheduler**
  - [ ] Deploy `mcp-scheduler` (custom or open-source)
  - [ ] Configure cron jobs for recurring tasks
  - [ ] Add webhook triggers (GitHub push → run agent)
- [ ] **Create workflow templates**
  - [ ] `code-review.yml`: PR → analyze → comment
  - [ ] `bug-fix.yml`: issue → reproduce → fix → PR
  - [ ] `docs-update.yml`: code change → update docs
  - [ ] `dependency-update.yml`: weekly → upgrade → test
- [ ] **Add parallel execution**
  - [ ] Configure Cline's `max_concurrent_tasks`
  - [ ] Implement task queuing in agent router
  - [ ] Monitor queue in Developer Surface

### 4.2 PR Automation & Review

- [ ] **Integrate with GitHub API via MCP**
  - [ ] Deploy `mcp-github` server
  - [ ] Register with agent router
  - [ ] Test PR creation: `agent create-pr --auto`
- [ ] **Add automated review loop**
  - [ ] Agent creates PR → triggers review
  - [ ] Review agent comments on code
  - [ ] Developer feedback → agent updates PR
- [ ] **Enable Cline's diff visualization**
  - [ ] Show `diff` in Kanban UI
  - [ ] Allow commenting directly on diffs
  - [ ] One-click approval to merge

---

## ✅ Phase 5: MCP Server Deployment (Week 5-6)

### 5.1 Core MCP Servers

- [x] **Deploy required MCP servers**
  - [ ] `mcp-browser` (Lightpanda) → port 8930 - Not deployed
  - [ ] `mcp-playwright` → port 8931 (optional)
  - [ ] `mcp-firewatch` → port 8932 (for Zen)
  - [ ] `mcp-secrets` → port 8933 (custom)
  - [x] `mcp-github` → port 8934 - Partially implemented
  - [ ] `mcp-scheduler` → port 8935
  - [ ] `mcp-serena` → port 8936 (code analysis)
- [x] **Configure each server**
  - [x] Add `mcp-manifest.json` per server - Core server configured
  - [ ] Register with agent router (port 8485)
  - [ ] Set health check intervals (30s)
  - [ ] Configure permissions matrix

### 5.2 Server Discovery & Registry

- [x] **Implement registration endpoint**
  - [x] `POST /api/mcp/register` - Available via MCP API
  - [x] Store in `McpRegistry` service - MCP bridge infrastructure
  - [x] Expose via `/api/mcp/servers` - Available via MCP API
- [x] **Add health monitoring**
  - [x] Ping all servers every 30s - MCP bridge has health checks
  - [x] Log failures to spool - Spool logging integrated
  - [ ] Show status in Developer Surface - Partially implemented
- [ ] **Create server dashboard**
  - [ ] List all registered servers
  - [ ] Show status (online/offline)
  - [ ] Display tool counts
  - [ ] Show recent usage metrics

  - [ ] Store in `McpRegistry` service
  - [ ] Expose via `/api/mcp/servers`
- [ ] **Add health monitoring**
  - [ ] Ping all servers every 30s
  - [ ] Log failures to spool
  - [ ] Show status in Developer Surface
- [ ] **Create server dashboard**
  - [ ] List all registered servers
  - [ ] Show status (online/offline)
  - [ ] Display tool counts
  - [ ] Show recent usage metrics

---


### 6.1 UI Components

- [x] **Add MCP control panel**
  - [x] `MCPToolsPanel` (list all tools by server) - S320 Knowledge Tools
  - [ ] `CostDashboard` (per task, per model, total)
  - [ ] `WorkflowStatus` (running tasks, queue)
  - [ ] `ModelSelector` (manual override option)
- [x] **Integrate Cline Kanban**
  - [x] Embed as primary workflow view - S300 board actions
  - [x] Add columns: Backlog → In Progress → Review → Done - TaskDetailDrawer
  - [x] Auto-update from agent tasks - Task management integration
- [x] **Add real-time logs**
  - [x] Subscribe to spool feed - Spool integration
  - [x] Filter by task ID - TaskDetailDrawer
  - [ ] Show token usage per step - Not implemented

### 6.2 Cost Visibility

- [ ] **Build cost tracking dashboard**
  - [ ] Per-task cost breakdown
  - [ ] Daily/weekly/monthly trends
  - [ ] Model cost comparison
  - [ ] Savings visualization
- [ ] **Add budget alerts**
  - [ ] Set daily budget ($5 default)
  - [ ] Warn at 80% usage
  - [ ] Auto-pause at 100%
- [ ] **Export cost reports**
  - [ ] CSV/JSON export
  - [ ] Slack notifications (optional)


## ✅ Phase 7: Skills & Rules Migration (Week 7-8)

### 7.1 Skill Conversion

- [ ] **Convert existing skills to MCP-backed workflows**
  - [ ] Audit all skills in `backend/app/skills/`
  - [ ] Identify MCP server for each skill
  - [ ] Create skill → server mapping
  - [ ] Update skill loading to use MCP tools
- [ ] **Test skill migration**
  - [ ] Run `e2e` tests for each skill
  - [ ] Compare execution time (MCP should be faster)
- [ ] **Skill token optimization**
  - [ ] Migrate relevant tools to MCP-backed ones

### 7.2 Rule Optimization

- [ ] **Consolidate rules using AgentMesh or OpenPackage**
  - [ ] Audit `rules/` directory
  - [ ] Identify duplicate/overlapping rules
  - [ ] Create canonical rule source
  - [ ] Implement sync to all tools
- [ ] **Add dynamic rule injection**
  - [ ] Load only relevant rules per task
  - [ ] Cache rule lookup
  - [ ] Measure token savings

---

## ✅ Phase 8: Testing & Validation (Week 8-9)

### 8.1 Performance Testing

- [ ] **Run benchmark suite**
  - [ ] 50 sample tasks across categories
  - [ ] Measure: time, tokens, cost
  - [ ] Compare with pre-optimization baseline
- [ ] **Validate cost savings**
  - [ ] Target: 60-90% token reduction
  - [ ] Target: 40-60% cost reduction
  - [ ] Target: No degradation in success rate

### 8.2 User Acceptance Testing

- [ ] **Onboard 5 power users**
  - [ ] 1 week trial with full toolset
  - [ ] Collect feedback via form
  - [ ] Iterate based on feedback
- [ ] **Documentation**
  - [ ] Write "Getting Started" guide
  - [ ] Create video tutorials
  - [ ] Update internal wiki

---

## ✅ Phase 9: Production Rollout (Week 9-10)

### 9.1 Deployment

- [ ] **Deploy to production environment**
  - [ ] All MCP servers in Docker
  - [ ] Agent router (8485) with high availability
  - [ ] Cline orchestration configured
- [ ] **Set up monitoring**
  - [ ] Prometheus metrics
  - [ ] Grafana dashboard
  - [ ] Alert rules

### 9.2 Team Training

- [ ] **Train all developers**
  - [ ] 1-hour workshop on MCP-first tools
  - [ ] Hands-on exercises
  - [ ] Office hours support
- [ ] **Create "cheat sheet"**
  - [ ] Common tasks → recommended flow
  - [ ] Quick reference for Cline commands
  - [ ] Troubleshooting guide

---

## 🎯 Success Metrics

| Metric | Target | Measurement |
| :--- | :--- | :--- |
| **Token cost per task** | Reduce by 60-90% | Pre/Post comparison |
| **Total monthly cost** | Reduce by 40-60% | Monthly billing |
| **Task completion time** | Reduce by 30% | Time tracking |
| **Model selection time** | 0ms (automated) | Manual vs automated |
| **Developer satisfaction** | > 4/5 | Survey |
| **MCP server uptime** | > 99.5% | Health checks |
| **Success rate (tasks)** | > 90% | Agent stats |

---

## 🛠️ Tools & Technologies

| Component | Recommendation | Alternative |
| :--- | :--- | :--- |
| **Orchestrator** | Cline | Aider, Codex CLI |
| **Router** | Flow-LLM-Router | OmniRoute, RouterLLM |
| **Token Optimizer MCP** | TOON + Token Optimizer MCP | Custom cache layer |
| **Cost Tracking** | OpenRouter analytics | Custom spool integration |
| **MCP Servers** | Lightpanda, Playwright, Firewatch | Self-hosted alternatives |
| **UI** | Cline Kanban | Custom React integration |
| **Scheduler** | mcp-scheduler | cron + scripts |

---

## 📝 Notes

- **All MCP servers MUST follow the "MCP for Everything" policy**
- **Cost tracking is mandatory** — no exceptions
- **Fallback to manual routing** if router is down (but log the failure)
- **Review token optimization** monthly — models improve, costs change
- **Celebrate wins** — share cost savings in team standup!

---

Here is a summary of the key open-source libraries, frameworks, and vendor resources available to implement your MCP-first Developer Tools upgrade.

...
# uCode MCP-First Developer Tools Upgrade Checklist

**Version:** 2.0.0 | **Target:** Complete by 2026-07-31 | **Owner:** Developer Productivity Team
**Last Updated:** 2026-06-26 | **Status:** Phase 5 In Progress

---

## 🎯 Objective

Transform uCode's Developer Surface into a fully MCP-integrated, cost-optimized development environment that eliminates manual model selection, reduces token costs by 60-90%, and provides complete workflow visibility through the Cline Kanban UI.

**Progress Summary:**
- ✅ Phase 1-4: Foundation & Orchestration (Not started - deferred)
- 🔄 Phase 5: MCP Server Deployment (In Progress)
- ⏳ Phase 6: Developer Surface Enhancement (Partially started)
- ⏳ Phase 7-9: Remaining phases (Not started)

