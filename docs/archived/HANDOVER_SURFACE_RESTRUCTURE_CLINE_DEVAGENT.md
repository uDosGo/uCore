# Surface Restructuring Recommendation

Date: 2026-06-23
Audience: Cline and DevAgent
Status: Live surface assessment and recommended restructuring

## Goal

Reduce overlap and role confusion across:

- Developer Surface
- Server Surface
- System Tools Surface

The current system works, but ownership boundaries are blurred. Several tabs are duplicated conceptually, and some tasks appear in the wrong operational home.

## Current Live Surface Roles

## Developer Surface

Live file:
- `/Users/fredbook/Code/uCore/frontend/src/surfaces/developer/DeveloperSurface.tsx`

Current tabs:
- models
- agents
- kanban
- tasks
- repos
- skills
- review
- workflows
- benchbench
- creative
- agents-old
- settings

Actual theme:
- code work
- AI/model management for development
- repo browsing and review
- dev workflow visibility

## Server Surface

Live file:
- `/Users/fredbook/Code/uCore/frontend/src/surfaces/userver/UServerSurface.tsx`

Current tabs:
- dashboard
- ingest
- missions
- story
- pages
- tools
- secrets
- settings
- services
- logs
- workflows
- budget
- agents
- snacks

Actual theme:
- runtime operations
- service health
- secrets and budget
- some workflow visibility
- but also mixed-in system pages, tools, and agent controls

## System Tools Surface

Live file:
- `/Users/fredbook/Code/uCore/frontend/src/surfaces/systemtools/SystemToolsSurface.tsx`

Current tabs:
- pages
- tools
- settings

Actual theme:
- S100-S899 system page browser
- administrative tool registry
- generic settings panel

## Overlap Findings

## 1. Workflows are split across Server and Developer

Current state:
- Developer has `kanban`, `tasks`, and `workflows`
- Server has `workflows`
- docs already say durable task state belongs in `.tasker/` and workflow visibility belongs to local orchestration, not a heavy duplicate UI first

Problem:
- Developer and Server are both presenting workflow-like concepts, but for different reasons and without clear naming.
- This makes it easy to put dev tasks in the ops surface and automation runs in the dev surface.

Recommendation:
- Developer owns **Dev Flow**
  - `kanban`
  - `tasks`
  - dev-oriented workflow runs
- Server owns **Automation Ops**
  - scheduled workflows
  - runtime job history
  - maintenance chains

Rename to remove ambiguity:
- Developer `workflows` -> `dev-flow` or `runs`
- Server `workflows` -> `automation`

## 2. Agents are split across Server and Developer

Current state:
- Developer has `agents`, `agents-old`, and `models`
- Server has `agents`

Problem:
- There are two different meanings of “agents”:
  - development/specialized coding agents
  - runtime/server automation agents
- They are currently using the same term in two different surfaces.

Recommendation:
- Developer owns **Dev Agents**
  - specialized coding agents
  - models
  - routing strategies
  - benchmarks
- Server owns **Runtime Agents**
  - operational agents
  - queue workers
  - background automation participants

Rename tabs explicitly:
- Developer `agents` -> `Dev Agents`
- Developer `agents-old` -> remove after migration or rename `Legacy Router`
- Server `agents` -> `Runtime Agents`

## 3. Settings are duplicated without scope boundaries

Current state:
- Developer has `settings`
- Server has `settings`
- System Tools has `settings`

Problem:
- Settings appear in three places, but there is no explicit distinction between:
  - developer preferences
  - server/runtime settings
  - generic system tool settings

Recommendation:
- Developer settings: dev-only
  - model defaults
  - agent behavior
  - review preferences
  - repo tooling
- Server settings: ops/runtime
  - service behavior
  - ingest/automation parameters
  - health/reload controls
- System Tools settings: shared/admin
  - global tool/page configuration
  - route-level admin preferences

If a setting is shared and global, it should not live primarily on Developer.

## 4. System Pages and Tools are duplicated across Server and System Tools

Current state:
- Server includes `pages` and `tools`
- System Tools already exists specifically for `pages`, `tools`, and `settings`

Problem:
- Server embeds a second home for System Tools.
- This makes the first-class System Tools surface redundant and teaches users two places to look.

Recommendation:
- System Tools becomes the only canonical home for:
  - `pages`
  - `tools`
  - generic admin settings
- Server should stop embedding those tabs directly.

Preferred replacement inside Server:
- a single shortcut card or link: `Open System Tools`

## 5. Mission/Story content in Server is mismatched

Current state:
- Server has `missions` and `story`

Problem:
- These are not pure server operations concepts.
- They are content- and workflow-adjacent surfaces mixed into an infrastructure hub.

Recommendation:
- `missions` should move toward Mission Control or a dedicated planning/ops bridge view.
- `story` should move toward System Tools or Documentation/Story tooling, depending on whether it is page-based or content-authoring.

Short-term compromise:
- keep routes alive for compatibility
- remove them from primary Server nav once destination surfaces are ready

## 6. Developer Surface is carrying “creative” without a clear home

Problem:
- `creative` feels more like a lab or content/design lane than core developer workflow.

Recommendation:
- either reframe it as `Labs`
- or move it behind System Tools or a dedicated creative surface later

It should not sit at the same information-architecture level as repos, review, and tasks unless it is clearly part of dev workflow.

## Recommended Canonical Ownership Model

## Developer Surface = Build Lane

Owns:
- repos
- review
- skills
- models
- dev agents
- kanban
- tasks
- dev flow / run history
- benchmarks
- dev-only settings

Does not own:
- service health
- logs
- secrets
- global settings
- system pages registry

## Server Surface = Runtime Ops Lane

Owns:
- dashboard
- services
- logs
- secrets
- budget
- ingest
- runtime agents
- automation workflows
- snacks
- server/runtime settings

Should not own directly:
- system pages browser
- generic tools browser
- dev tasks / kanban
- repo review

## System Tools Surface = Admin Registry Lane

Owns:
- pages
- tools
- shared admin settings
- system page discovery and launch

Should be the one canonical home for S100-S899 browsing.

## Proposed Streamlined Navigation

## Developer
- Dev Flow
- Tasks
- Repos
- Review
- Skills
- Models
- Dev Agents
- Bench
- Settings

## Server
- Dashboard
- Services
- Logs
- Secrets
- Budget
- Ingest
- Automation
- Runtime Agents
- Snacks
- Settings
- Open System Tools

## System Tools
- Pages
- Tools
- Settings

## Migration Strategy

## Phase 1: Naming and de-duplication

1. Rename ambiguous tabs
   - Server `workflows` -> `automation`
   - Server `agents` -> `runtime-agents`
   - Developer `agents-old` -> `legacy-router`
2. Document canonical ownership in code comments and handover docs.

## Phase 2: Remove duplicated nav homes

1. Remove `pages` and `tools` from Server nav.
2. Replace with a shortcut to System Tools.
3. Keep route compatibility redirects while the nav settles.

## Phase 3: Separate workflow meanings

1. Keep `.tasker/` and Kanban under Developer.
2. Keep maintenance and scheduled workflow execution under Server.
3. Point both at a shared backend status model where useful, but do not present them as the same surface concept.

## Phase 4: Relocate mismatched content tabs

1. Re-home `missions` and `story` out of Server nav if they are not fundamentally operational.
2. Move creative/lab content out of the primary developer stack if it remains separate from code execution.

## DevAgent Configuration Assessment

Checked file:
- `/Users/fredbook/Code/uCore/backend/config/agents.yaml`

## Current outcome

The config can handle this work after the latest capability update.

### Architect agent
Now explicitly suited for the planning pass:
- capabilities include `information-architecture` and `surface-taxonomy`

Best use:
- define canonical ownership boundaries
- decide where tabs should move
- design migration order and compatibility plan

### Dev agent
Now explicitly suited for implementation:
- capabilities include `frontend`, `integration`, `surface-refactor`, `workflow-ui`

Best use:
- rename tabs
- move panels/routes
- simplify nav
- preserve compatibility redirects
- update UI components and tests

### Reviewer agent
Use after migration:
- regression audit
- overlap check
- naming consistency pass

## Recommendation for agent usage

Do not assign the entire restructure to DevAgent alone.

Best split:
1. Architect defines the target taxonomy.
2. DevAgent performs the actual surface refactor.
3. Reviewer verifies regressions and ownership drift.

So: DevAgent can handle the implementation work, but it should not be the only agent deciding the IA.

## Recommended First Execution Slice

The first safe refactor slice is:

1. rename Server `workflows` -> `automation`
2. rename Server `agents` -> `runtime agents`
3. remove Server `pages` and `tools` from primary nav
4. add `Open System Tools` link/card in Server instead
5. rename Developer `agents-old` -> `legacy router`

This gives immediate clarity without moving the more sensitive mission/story/dev-flow boundaries yet.

## One-line Summary

Developer should own build workflow and coding agents, Server should own runtime operations and automation, and System Tools should be the only home for the page/tool registry. The current DevAgent config is now strong enough to implement that refactor, but Architect should define the target taxonomy first.