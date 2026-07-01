# Handover Note: uDOS Local Model Performance and Optimization

Date: 2026-06-21
Status: Archived for planning; active tasks moved to unified workflow

## Executive Summary

Local Ollama performance remains latency-bound on larger models. The recommended local default is:

- qwen2.5-coder:7b-instruct-q4_K_M

Primary recommendation:

- Use OpenRouter for speed and scale
- Keep local Qwen Q4 as fallback
- Cache aggressively for repeated prompts

## Bottlenecks Observed

- High latency on local large models
- Elevated error rate under memory pressure
- Context limits with default local settings
- Cold-start delays
- Low concurrency with local runtime defaults

## Model Guidance

Recommended local model:

- qwen2.5-coder:7b-instruct-q4_K_M

Avoid heavy local defaults for daily workflow:

- 13B+ and 32B class models unless a dedicated high-memory host is used

## OpenRouter Integration Guidance

Preferred OpenRouter coding model:

- qwen/qwen-2.5-coder-7b-instruct

Optional stronger reasoning model:

- deepseek/deepseek-chat-v3-0324

Local fallback model:

- qwen2.5-coder:7b-instruct-q4_K_M

## Caching Strategy

Use a local SQLite cache keyed by prompt hash and model to reduce repeat latency and API cost.

Recommended cache fields:

- key
- prompt_hash
- model
- response
- created_at
- accessed_at
- hit_count

Maintenance actions:

- prune by last access age (for example 7 days)
- collect hit ratio stats

## Action Plan

Action items from this note are registered in:

- `.tasker/UNIFIED_DEV_TASK_WORKFLOW.md`
- `docs/archive/plans/2026-06-21-plan-migration-snapshot.md`

1. Keep Qwen Q4 as local default.
2. Route medium and complex tasks to OpenRouter by default.
3. Add SQLite chat cache for extension/tooling path.
4. Keep OpenRouter -> local fallback behavior.
5. Monitor latency and cache hit ratio regularly.

## Operational Checks

Use these scripts:

- scripts/repair_ai_extensions_stack.sh
- scripts/ai_stack_health_check.sh

These validate:

- Cline MCP config
- Continue config
- MCP bridge and API health
- skill_route_task execution
- maintenance endpoint reachability

## Open Questions

1. Should common prompts be pre-warmed into cache?
2. Target response latency threshold for daily coding?
3. Cache policy split between provider-side and local cache?
4. Cache invalidation strategy for changing code context?
