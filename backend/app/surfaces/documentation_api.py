"""Documentation Surface — serves doc index and course data."""

from __future__ import annotations

from aiohttp import web

DOC_COURSES: list[dict] = [
    {
        "id": "getting-started",
        "title": "Getting Started",
        "icon": "rocket_launch",
        "description": "Introduction to uCore ecosystem and architecture",
        "status": "completed",
    },
    {
        "id": "grid-core",
        "title": "GridUI & Canvas Engine",
        "icon": "grid_on",
        "description": "Building with Ceefax G0 renderer and grid layers",
        "status": "completed",
    },
    {
        "id": "surfaces",
        "title": "Surface Architecture",
        "icon": "dashboard",
        "description": "Tabbed surfaces, panels, and backend wiring",
        "status": "in-progress",
    },
    {
        "id": "agentic-workflows",
        "title": "Agentic Workflows",
        "icon": "account_tree",
        "description": "Mission control, tasker, and skills pipeline",
        "status": "in-progress",
    },
    {
        "id": "mcp-integration",
        "title": "MCP Servers & Tools",
        "icon": "sync_alt",
        "description": "Building and connecting MCP servers",
        "status": "not-started",
    },
    {
        "id": "feed-system",
        "title": "Feed & Activity System",
        "icon": "rss_feed",
        "description": "Pod, nugget, seed, slate, and spool pipeline",
        "status": "not-started",
    },
]

DOC_SECTIONS: list[dict] = [
    {"id": "architecture", "title": "Architecture Overview", "path": "architecture"},
    {"id": "setup", "title": "Setup & Installation", "path": "setup"},
    {"id": "guide", "title": "Developer Guide", "path": "guide"},
    {"id": "api", "title": "API Reference", "path": "api"},
    {"id": "specs", "title": "Feature Specs", "path": "specs"},
    {"id": "archive", "title": "Archived Docs", "path": "archive"},
]


def register_documentation_routes(app: web.Application) -> None:
    """Register documentation surface API routes."""

    async def handle_courses(_request: web.Request) -> web.Response:
        return web.json_response({
            "courses": DOC_COURSES,
            "count": len(DOC_COURSES),
        })

    async def handle_sections(_request: web.Request) -> web.Response:
        return web.json_response({
            "sections": DOC_SECTIONS,
            "count": len(DOC_SECTIONS),
        })

    async def handle_index(_request: web.Request) -> web.Response:
        return web.json_response({
            "courses": DOC_COURSES,
            "sections": DOC_SECTIONS,
        })

    app.router.add_get("/api/docs/courses", handle_courses)
    app.router.add_get("/api/docs/sections", handle_sections)
    app.router.add_get("/api/docs/index", handle_index)
