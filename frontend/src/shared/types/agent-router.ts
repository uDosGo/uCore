/* ═══════════════════════════════════════════════════════════════════
   agent-router.ts — Shared types for Agent Router
   ═══════════════════════════════════════════════════════════════════
   Extracted from DeveloperSurface and UServerSurface duplications.
   ═══════════════════════════════════════════════════════════════════ */

export interface RouterAgent {
  id: string
  name: string
  capabilities: string[]
  status: string
  load: string
  costPerTask: number
  avgLatencyMs: number
  successRate: number
}

export interface RouterStats {
  totalRouted: number
  totalErrors: number
  byAgent: Record<string, number>
  byCapability: Record<string, number>
  recentRoutes: Array<{ task: string; agent: string; capability: string; timestamp: string }>
}