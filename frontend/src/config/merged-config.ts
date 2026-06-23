/**
 * Unified Configuration for uCore
 * Merges Cline settings, Secret Store values, and Environment Variables.
 */

export interface AppConfig {
  github: {
    token: string;
    webhookSecret: string;
  };
  mcp: {
    serverPort: number;
    serverUrl: string;
  };
  database: {
    path: string;
  };
  logging: {
    level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  };
  // Cline specific settings
  cline: {
    operatingPrinciples: string[];
    mcpUsage: string[];
  };
}

const mergedConfig: AppConfig = {
  github: {
    token: process.env.GITHUB_TOKEN || '',
    webhookSecret: process.env.GITHUB_WEBHOOK_SECRET || '',
  },
  mcp: {
    serverPort: parseInt(process.env.MCP_SERVER_PORT || '8765', 10),
    serverUrl: `http://localhost:${process.env.MCP_SERVER_PORT || '8765'}`,
  },
  database: {
    path: process.env.DB_PATH || './ucore.db',
  },
  logging: {
    level: (process.env.LOG_LEVEL as any) || 'INFO',
  },
  cline: {
    operatingPrinciples: [
      "Prefer safe, reversible changes and keep diffs small",
      "Keep durable workflow state in .tasker/ Markdown files",
      "Treat Cline Kanban as orchestration UI, not source of truth",
      "Keep MCP integrations localhost-only by default",
      "Preserve Git history clarity with focused, test-backed changes",
    ],
    mcpUsage: [
      "Prefer the uCore MCP server for skills and knowledge access",
      "Verify MCP health before relying on tools",
      "Do not broaden network exposure of MCP services without explicit opt-in",
    ],
  },
};

export default mergedConfig;