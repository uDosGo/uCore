# Hivemind Orchestration Specification

> **Version:** 1.0  
> **Status:** Draft  
> **Scope:** Multi-agent orchestration, consensus engine, MCP server topology

## 1. Philosophy

Hivemind is uCore's multi-agent orchestration layer. It enables:

1. **Specialized agents** — Each agent has a defined role (coder, tester, planner, reviewer)
2. **Consensus-driven decisions** — Agents vote/negotiate on ambiguous tasks
3. **Roundtable AI integration** — Leverage multiple LLM backends (OpenAI, Anthropic, Ollama)
4. **Template-driven workflows** — Agent interaction patterns are defined as templates

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hivemind MCP Server                    │
│  (backend/mcp/start_hivemind.sh → port 8490)             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │ │
│  │  Coder   │  │  Tester  │  │  Planner │  │ Reviewer │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │           Consensus Engine                        │    │
│  │  - Majority vote  - Weighted scoring             │    │
│  │  - Escalation chain  - Deadlock detection        │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │           LLM Router                              │    │
│  │  - Roundtable API  - Ollama local  - Fallback    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    uCore Backend                          │
│  (port 8484 — skills, snacks, MCP tools)                 │
└─────────────────────────────────────────────────────────┘
```

## 3. MCP Server Topology

| Server | Port | Purpose | Status |
|--------|------|---------|--------|
| `mcp-main` | 8484 | uCore backend (skills, tools) | ✅ Active |
| `mcp-firewatch` | 8485 | Browser automation testing | ⚙️ Setup |
| `mcp-playwright` | 8486 | Playwright test runner | ⚙️ Setup |
| `mcp-scheduler` | 8487 | Cron/scheduled tasks | ⚙️ Setup |
| `mcp-secrets` | 8488 | Secret management | ⚙️ Setup |
| `mcp-serena` | 8489 | Serena AI assistant | ⚙️ Setup |
| **`mcp-hivemind`** | **8490** | **Multi-agent orchestration** | **✅ Active** |


## 4. Agent Definitions

Agents are defined in `backend/config/agents.yaml`:

```yaml
agents:
  coder:
    name: "Coder Agent"
    model: "claude-sonnet-4-20250514"
    system_prompt: "You are a senior software engineer..."
    tools: ["skill_*", "knowledge_search", "tasker_*"]
    timeout: 120
    weight: 1.0  # Voting weight in consensus

  tester:
    name: "Tester Agent"
    model: "gpt-4o"
    system_prompt: "You are a QA engineer..."
    tools: ["skill_lint_fix", "gridsmith_*"]
    timeout: 60
    weight: 0.8

  planner:
    name: "Planner Agent"
    model: "claude-opus-4-20250514"
    system_prompt: "You are a technical architect..."
    tools: ["knowledge_search", "tasker_write_task"]
    timeout: 180
    weight: 1.2

  reviewer:
    name: "Reviewer Agent"
    model: "gpt-4o"
    system_prompt: "You are a code reviewer..."
    tools: ["skill_lint_fix", "knowledge_search"]
    timeout: 60
    weight: 0.9
```

## 5. Consensus Engine

### Voting Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `majority` | Simple majority wins | Low-risk decisions |
| `unanimous` | All agents must agree | Destructive operations |
| `weighted` | Weighted score threshold | Technical decisions |
| `escalation` | Escalate to human on deadlock | Ambiguous requirements |

### Consensus Flow

```
1. PROPOSE  → Agent submits proposal with rationale
2. DEBATE   → Other agents critique and suggest alternatives
3. VOTE     → Each agent votes (approve/reject/abstain) with reasoning
4. RESOLVE  → Apply voting mode to determine outcome
5. EXECUTE  → Winning proposal is executed via MCP tools
6. VERIFY   → Reviewer agent validates the result
```

### Deadlock Detection

- If no consensus after 3 rounds → escalate to human
- If agent unresponsive for >30s → mark as abstained
- If two agents repeatedly disagree → invoke tiebreaker agent

## 6. LLM Router

The router selects which LLM backend to use for each agent:

```yaml
router:
  backends:
    roundtable:
      type: "openai_compatible"
      base_url: "http://localhost:4891/v1"  # Roundtable local
      models: ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "gpt-4o"]
      priority: 1

    ollama:
      type: "openai_compatible"
      base_url: "http://localhost:11434/v1"
      models: ["llama3", "codellama", "mistral"]
      priority: 2  # Fallback when Roundtable unavailable

    fallback:
      type: "openai"
      api_key: "${OPENAI_API_KEY}"
      models: ["gpt-4o-mini"]
      priority: 3  # Last resort
```

## 7. Workflow Plates

Hivemind workflows are defined as YAML plates in `plates/hivemind/`:

```yaml
# plates/hivemind/code_review.yaml

workflow:
  id: "hivemind.code_review"
  version: "1.0.0"
  description: "Multi-agent code review workflow"
  agents: ["coder", "reviewer"]
  consensus: "majority"
  steps:
    - role: "coder"
      action: "propose_change"
      tools: ["skill_lint_fix", "knowledge_search"]
    - role: "reviewer"
      action: "review_change"
      tools: ["skill_lint_fix"]
    - role: "coder"
      action: "address_feedback"
    - role: "reviewer"
      action: "approve_or_reject"
  timeout: 300
```

## 8. Integration with Plates System

Hivemind workflows are plates themselves (see `docs/PLATES_SYSTEM_SPEC.md`):

- **Scaffolding** — `ucore hivemind init --workflow code_review` generates a new workflow from a Cookiecutter plate
- **Validation** — `skill_audit` checks agent configs against workflow plates
- **DESTROY/REBUILD** — On agent corruption, salvage agent config and rebuild from plate


## 9. Setup Steps

```bash
# 1. Create Hivemind MCP server
cd backend/mcp
cp mcp-serena-manifest.json mcp-hivemind-manifest.json
# Edit: change port to 8490, name to "hivemind"

# 2. Create startup script
cat > start_hivemind.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
exec python3 -m app.mcp.hivemind_server --port 8490
EOF
chmod +x start_hivemind.sh

# 3. Register in MCP config
# Add to devlog.mcp.yaml or VS Code settings

# 4. Verify
python3 -m backend.mcp.mcp_diagnostics --check hivemind
```

## 10. Implementation Status

- [x] Implement Hivemind MCP server (`backend/app/mcp/hivemind_server.py`) — ✅ Done
- [x] Implement consensus engine (`backend/app/mcp/consensus.py`) — ✅ Done
- [x] Implement LLM router (`backend/app/mcp/llm_router.py`) — ✅ Done
- [x] Create MCP manifest (`backend/mcp/mcp-hivemind-manifest.json`) — ✅ Done
- [x] Create startup script (`backend/mcp/start_hivemind.sh`) — ✅ Done
- [ ] Create workflow plates directory (`plates/hivemind/`)


- [ ] Add `skill_hivemind` for agent orchestration via MCP
- [ ] Integration with Roundtable AI for local LLM routing
- [ ] Deadlock recovery and human escalation UI
