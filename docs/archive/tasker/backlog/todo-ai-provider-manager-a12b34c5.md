# AI Provider Manager UI
- status: done
- source: ucore-dev
- source_id: backlog-provider-ui
- synced_at: 2026-06-22T12:00:00Z
- completed: 2026-06-22

## Summary
AI provider configuration is managed via backend settings and OpenRouter/Ollama integration. Frontend system page wiring deferred to Phase 8 (UX refinement).

## Metadata
- area: ai
- priority: low
- depends_on: UDW-023, Phase 8

## Current Implementation
- **Provider Routing**: `backend/app/services/provider_router.py`
  - Local default: `qwen2.5-coder:7b-instruct-q4_K_M` (Ollama)
  - Medium/Complex workloads routed to OpenRouter
  - Fallback chain: Ollama → OpenRouter → error
- **Configuration**: `backend/app/core/settings.py`
  - `OLLAMA_BASE_URL` (default: http://localhost:11434)
  - `OPENROUTER_API_KEY` (via secrets store)
  - Model selection strategy in provider_router
- **Chat Cache**: SQLite-backed cache in `backend/app/services/chat_cache.py`
  - Tracks latency and cache hit ratio
  - Enables local-first response optimization

## Deferred: Frontend System Page
- Add/remove model UI in System surface
- Key management for OpenRouter/Gemini
- Routing strategy toggles
- Estimated effort: 4-8 hours (Phase 8)
