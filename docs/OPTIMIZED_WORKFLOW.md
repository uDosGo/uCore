# Optimized Workflow Documentation

## Overview

This document describes the optimized workflow features implemented in uCore to reduce token waste and improve cost efficiency:

- **TOON Context Optimization**: Token-optimized context encoding for 30-60% token savings
- **Flow-LLM Router**: Cost-optimized routing with analytics and visualization
- **Token Optimizer MCP**: Cache and compress API responses and file contents

## TOON Context Optimization

### What is TOON?

TOON (Token-Optimized Object Notation) is a compact representation format that preserves semantic meaning while reducing token usage by 30-60%.

### How it works

1. **Content Analysis**: TOON analyzes the content type (JSON, Markdown, CSV, text)
2. **Optimized Encoding**: Converts content to a compact format that preserves structure but removes redundancy
3. **Caching**: Stores encoded content in a SQLite database for reuse
4. **Analytics**: Tracks compression ratios and cache hit rates

### Usage

#### REST API
- `POST /api/toon/encode` - Convert content to TOON format
- `GET /api/toon/stats` - Get TOON server statistics
- `POST /api/toon/clear` - Clear TOON cache

#### MCP Tools
- `toon_encode` - Convert content to TOON format
- `toon_stats` - Get TOON context server statistics
- `toon_clear` - Clear TOON context cache

## Flow-LLM Router

### What is Flow-LLM Router?

Flow-LLM Router is an enhanced routing system that intelligently selects the best AI provider and model for each task based on cost, complexity, context size, and risk level.

### How it works

1. **Task Analysis**: Analyzes task description to determine complexity, context size, and risk level
2. **Cost Estimation**: Calculates estimated cost and token usage for each provider/model combination
3. **Optimal Selection**: Selects the provider/model that provides the best balance of cost, performance, and security
4. **Analytics**: Tracks cost savings, token savings, and latency improvements
5. **History**: Maintains routing history for debugging and optimization

### Usage

#### REST API
- `POST /api/flow-router/route` - Route a task to optimal provider/model
- `GET /api/flow-router/analytics` - Get routing analytics
- `GET /api/flow-router/history` - Get routing history

#### MCP Tools
- `flow_router_route` - Route a task to optimal provider/model with cost analytics
- `flow_router_analytics` - Get routing analytics and cost savings
- `flow_router_history` - Get recent routing history

## Integration with Developer Surface

The Cline Kanban UI integrates with these optimization features to provide:

- Real-time routing decisions with model selection and cost estimates
- Visual feedback for each agent run showing estimated cost and token usage
- Cost savings analytics dashboard
- Routing history visualization
- Automatic review and PR creation with context-aware feedback

## Getting Started

1. Start the uCore backend: `cd backend && python3 -m app`
2. Start the frontend: `cd frontend && npm run dev`
3. Use the Cline Kanban UI or MCP tools to access the optimization features
4. Monitor analytics at `/api/toon/stats` and `/api/flow-router/analytics`

## Configuration

Configuration files are available in the `config/` directory:
- `toon.example.yaml` - TOON server configuration
- `flow-router.example.yaml` - Flow-LLM Router configuration

## Troubleshooting

- If TOON encoding doesn't show compression, ensure content is large enough (>1000 bytes)
- If Flow-LLM Router doesn't select expected providers, check `~/.config/udos/models.yaml` configuration
- For MCP tool issues, verify `/api/mcp/tools` returns the expected tools

## Next Steps

- Integrate TOON encoding into the Cline Kanban UI for automatic context optimization
- Add visual analytics dashboard to the Developer Surface
- Implement automatic cost optimization based on usage patterns
- Add support for additional content types (YAML, XML, etc.)
