# Docs Consolidation Plan

Date: 2026-06-21
Owner: uDosGo maintainers
Status: Milestone A started

## Objective

Consolidate distributed documentation into uDocs so architecture, API, and operational knowledge have one canonical home.

## Canonical Repository

uDocs path: /Users/fredbook/Code/uDocs

Canonical sections:
- architecture/
- api/
- runbooks/
- guides/
- surfaces/
- runtimes/
- changelog/

## Source Inventory Summary

Discovered and reviewed sources:
- /Users/fredbook/Code/uCore/CONTEXT.md
- /Users/fredbook/Code/uCore/docs/GITHUB_AUTOMATION.md
- /Users/fredbook/Code/uCore/docs/GITHUB_SKILLS_SUMMARY.md
- /Users/fredbook/Code/uCode/README.md
- /Users/fredbook/Code/global-knowledge/README.md
- /Users/fredbook/Code/ARCHIVED/uDosGo.code-workspace

Missing expected sources:
- /Users/fredbook/Code/uConnect (repo missing)
- /Users/fredbook/Code/uServer (repo missing)
- /Users/fredbook/Code/HomeNest/README.md (missing)
- /Users/fredbook/Code/uCore/README.md (missing)

## Keep / Merge / Archive

Keep and normalize into uDocs:
- uCore CONTEXT content for architecture and API baseline
- uCore GitHub automation docs for runbooks and MCP bridge docs
- uCode runtime map for runtime docs

Merge:
- GITHUB_SKILLS_SUMMARY.md into broader automation docs to remove duplication
- Workspace role comments into onboarding guide

Archive or deprecate in-place:
- Legacy repo docs should point to uDocs after migration completion

## Milestone A Deliverables Completed

1. uDocs structure scaffolded.
2. uDocs CONTEXT.md drafted.
3. ADR-001 and ADR-002 drafted.
4. Source inventory and decisions documented in /Users/fredbook/Code/uDocs/migration-source-inventory.md.

## Next Milestone A Actions

1. Populate architecture/overview.md and api/rest-api.md directly from current uCore routes and handlers.
2. Populate runbooks/development.md from current backend/frontend setup commands.
3. Populate surfaces/ceefax.md and surfaces/devstudio.md from current uCore surfaces and frontend modules.
4. Populate runtimes/basic.md from uCode runtime docs.
5. Update repository README files to point to uDocs.

## Definition of Done for Consolidation

- All active architecture and API docs exist in uDocs.
- Every repo README links to uDocs canonical sections.
- Duplicate detailed docs outside uDocs are archived or replaced with pointers.
- AI context files reference uDocs as source of truth.
