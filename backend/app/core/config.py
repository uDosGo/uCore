"""
Unified Configuration for uCore (Python)
Merges Cline settings, Secret Store values, and Environment Variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GitHubConfig:
    token: str = os.environ.get("GITHUB_TOKEN", "")
    webhook_secret: str = os.environ.get("GITHUB_WEBHOOK_SECRET", "")


@dataclass
class MCPConfig:
    server_port: int = int(os.environ.get("MCP_SERVER_PORT", "8765"))
    server_url: str = (
        f"http://localhost:{os.environ.get('MCP_SERVER_PORT', '8765')}"
    )


@dataclass
class DatabaseConfig:
    path: str = os.environ.get("DB_PATH", "./ucore.db")


@dataclass
class LoggingConfig:
    level: str = os.environ.get("LOG_LEVEL", "INFO")


@dataclass
class ClineConfig:
    operating_principles: Optional[list[str]] = field(default=None)
    mcp_usage: Optional[list[str]] = field(default=None)

    def __post_init__(self):
        if self.operating_principles is None:
            self.operating_principles = [
                "Prefer safe, reversible changes and keep diffs small",
                "Keep durable workflow state in .tasker/ Markdown files",
                "Treat Cline Kanban as orchestration UI, not source of truth",
                "Keep MCP integrations localhost-only by default",
                "Preserve Git history clarity with focused, test-backed changes",
            ]
        if self.mcp_usage is None:
            self.mcp_usage = [
                "Prefer the uCore MCP server for skills and knowledge access",
                "Verify MCP health before relying on tools",
                "Do not broaden network exposure of MCP services without opt-in",
            ]


@dataclass
class AppConfig:
    github: Optional[GitHubConfig] = field(default=None)
    mcp: Optional[MCPConfig] = field(default=None)
    database: Optional[DatabaseConfig] = field(default=None)
    logging: Optional[LoggingConfig] = field(default=None)
    cline: Optional[ClineConfig] = field(default=None)

    def __post_init__(self):
        if self.github is None:
            self.github = GitHubConfig()
        if self.mcp is None:
            self.mcp = MCPConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.cline is None:
            self.cline = ClineConfig()


# Singleton instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the unified configuration instance."""
    return config