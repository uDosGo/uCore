#!/usr/bin/env python3
"""uCore Central Index Skill — Unified index and search across uCore ecosystem

Provides a comprehensive index of:
  - All skills (builtin and custom)
  - All MCP servers and tools
  - All surfaces and components
  - All configuration files and schemas
  - All documentation and specs

Usage:
  POST /api/skills/ucore_index/run
    Body: {
        "search": "filepicker",
        "category": "component",
        "limit": 10
    }
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.ucore_index")

# uCore root directory
UCORE_ROOT = Path(__file__).parent.parent.parent.parent.parent
FRONTEND_SRC = UCORE_ROOT / "frontend" / "src"
BACKEND_APP = UCORE_ROOT / "backend" / "app"
DOCS_DIR = UCORE_ROOT / "docs"


class UCoreIndexSkill(BaseSkill):
    """Central index for uCore ecosystem components and resources."""

    meta = SkillMeta(
        id="ucore_index",
        name="uCore Index",
        description="Central index and search across uCore ecosystem - skills, surfaces, components, and documentation",
        category="system",
        timeout=30,
        params=[
            SkillParam(name="search", type="string", required=False, description="Search query"),
            SkillParam(name="category", type="string", required=False, description="Filter by category (Skill, Surface, Component, Documentation)"),
            SkillParam(name="limit", type="integer", required=False, default=20, description="Maximum results to return"),
        ],
        requires_confirmation=False,
    )

    def __init__(self):
        super().__init__()
        self.index: Dict[str, Any] = {
            "meta": {
                "version": "1.0.0",
                "generated_at": None,
                "ucore_version": None,
            },
            "skills": [],
            "mcp_servers": [],
            "surfaces": [],
            "components": [],
            "config_files": [],
            "documentation": [],
        }

    async def run(self, **kwargs) -> dict:
        """Execute the uCore index skill."""
        skill = UCoreIndexSkill()

        # Check if search query provided
        search_query = kwargs.get("search", "")
        category = kwargs.get("category")
        limit = kwargs.get("limit", 20)

        if search_query:
            # Perform search
            result = skill.search(search_query, category, limit)
            return {
                "success": True,
                "action": "search",
                "query": search_query,
                "category": category,
                "results": result,
            }
        else:
            # Generate full index
            index = skill.generate()
            return {
                "success": True,
                "action": "index",
                "index": index,
            }

    def generate(self) -> Dict[str, Any]:
        """Generate comprehensive uCore index."""
        log.info("Generating uCore central index...")

        self.index["meta"]["generated_at"] = str(Path.cwd())
        self.index["meta"]["ucore_version"] = self._get_ucore_version()

        # Index all components
        self._index_components()
        # Index all skills
        self._index_skills()
        # Index all MCP servers
        self._index_mcp_servers()
        # Index all surfaces
        self._index_surfaces()
        # Index config files
        self._index_config_files()
        # Index documentation
        self._index_documentation()

        log.info(f"Index generated: {len(self.index['skills'])} skills, "
                 f"{len(self.index['surfaces'])} surfaces, "
                 f"{len(self.index['components'])} components")

        return self.index

    def search(self, query: str, category: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Search the uCore index."""
        if not query:
            return {"results": [], "total": 0}

        query = query.lower()
        results: List[Dict[str, Any]] = []

        # Flatten all indexed items
        all_items = []
        for category_name, items in self.index.items():
            if category_name == "meta":
                continue
            if category and category_name != category:
                continue
            all_items.extend(items)

        # Search across all fields
        for item in all_items:
            score = 0
            searchable_text = " ".join(str(v).lower() for v in item.values() if v)

            # Direct match
            if query in searchable_text:
                score += 10

            # Partial match
            if query in searchable_text or any(query in str(v).lower() for v in item.values()):
                score += 5

            # Field-specific scoring
            if "name" in item and query in item["name"].lower():
                score += 3
            if "description" in item and query in item["description"].lower():
                score += 2
            if "path" in item and query in item["path"].lower():
                score += 1

            if score > 0:
                results.append({**item, "_score": score})

        # Sort by score and limit
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        results = results[:limit]

        return {
            "query": query,
            "results": results,
            "total": len(results),
        }

    def _get_ucore_version(self) -> str:
        """Get uCore version from package.json."""
        try:
            package_json = FRONTEND_SRC.parent / "package.json"
            if package_json.exists():
                data = json.loads(package_json.read_text())
                return data.get("version", "unknown")
        except Exception as e:
            log.warning(f"Failed to read version: {e}")
        return "unknown"

    def _index_components(self):
        """Index all React components."""
        components_dir = FRONTEND_SRC / "components"
        if not components_dir.exists():
            return

        for component_file in components_dir.rglob("*.tsx"):
            if component_file.name.startswith("_"):
                continue

            try:
                content = component_file.read_text()
                name = component_file.stem

                # Extract component name from file
                import re
                match = re.search(r"export\s+(const|function)\s+(\w+)", content)
                if not match:
                    continue
                component_name = match.group(2)

                self.index["components"].append({
                    "name": component_name,
                    "type": "React Component",
                    "path": str(component_file.relative_to(FRONTEND_SRC)),
                    "description": self._extract_description(content),
                    "exports": self._extract_exports(content),
                })
            except Exception as e:
                log.debug(f"Failed to index component {component_file}: {e}")

    def _index_skills(self):
        """Index all skills."""
        skills_dir = BACKEND_APP / "skills" / "builtin"
        if not skills_dir.exists():
            return

        for skill_file in skills_dir.rglob("*.py"):
            if skill_file.name.startswith("_"):
                continue

            try:
                content = skill_file.read_text()
                name = skill_file.stem

                # Extract skill metadata
                import re
                match = re.search(r'class\s+(\w+)\(BaseSkill\):', content)
                if not match:
                    continue
                skill_name = match.group(1)

                # Extract description from docstring
                desc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
                description = desc_match.group(1).strip() if desc_match else "No description"

                self.index["skills"].append({
                    "name": skill_name,
                    "type": "Skill",
                    "path": str(skill_file.relative_to(BACKEND_APP)),
                    "description": description[:200],  # Truncate
                })
            except Exception as e:
                log.debug(f"Failed to index skill {skill_file}: {e}")

    def _index_mcp_servers(self):
        """Index MCP servers and tools."""
        mcp_dir = BACKEND_APP / "mcp"
        if not mcp_dir.exists():
            return

        # Check for MCP server files
        for mcp_file in mcp_dir.rglob("*.py"):
            if mcp_file.name.startswith("_"):
                continue

            try:
                content = mcp_file.read_text()
                name = mcp_file.stem

                # Extract MCP server info
                import re
                match = re.search(r'class\s+(\w+)\(.*MCP.*\):', content, re.IGNORECASE)
                if not match:
                    continue
                mcp_name = match.group(1)

                self.index["mcp_servers"].append({
                    "name": mcp_name,
                    "type": "MCP Server",
                    "path": str(mcp_file.relative_to(BACKEND_APP)),
                    "description": "MCP server for tool integration",
                })
            except Exception as e:
                log.debug(f"Failed to index MCP server {mcp_file}: {e}")

    def _index_surfaces(self):
        """Index all UI surfaces."""
        surfaces_dir = FRONTEND_SRC / "surfaces"
        if not surfaces_dir.exists():
            return

        for surface_file in surfaces_dir.rglob("*.tsx"):
            if surface_file.name.startswith("_"):
                continue

            try:
                content = surface_file.read_text()
                name = surface_file.stem

                # Extract surface info
                import re
                match = re.search(r'export\s+(const|function)\s+(\w+)', content)
                if not match:
                    continue
                surface_name = match.group(2)

                # Extract route if present
                route_match = re.search(r'path=["\']([^"\']+)["\']', content)
                route = route_match.group(1) if route_match else None

                self.index["surfaces"].append({
                    "name": surface_name,
                    "type": "Surface",
                    "path": str(surface_file.relative_to(FRONTEND_SRC)),
                    "route": route,
                    "description": self._extract_description(content),
                })
            except Exception as e:
                log.debug(f"Failed to index surface {surface_file}: {e}")

    def _index_config_files(self):
        """Index configuration files."""
        config_files = [
            "package.json",
            "pnpm-workspace.yaml",
            "pyproject.toml",
            "vite.config.ts",
            "tsconfig.json",
        ]

        for config_file in config_files:
            config_path = FRONTEND_SRC.parent / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text()
                    self.index["config_files"].append({
                        "name": config_file,
                        "type": "Configuration",
                        "path": str(config_path.relative_to(UCORE_ROOT)),
                        "size": len(content),
                    })
                except Exception as e:
                    log.debug(f"Failed to index config {config_file}: {e}")

    def _index_documentation(self):
        """Index documentation files."""
        if not DOCS_DIR.exists():
            return

        for doc_file in DOCS_DIR.rglob("*.md"):
            try:
                content = doc_file.read_text()
                name = doc_file.stem

                # Extract title from first heading
                import re
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else name

                self.index["documentation"].append({
                    "name": title,
                    "type": "Documentation",
                    "path": str(doc_file.relative_to(DOCS_DIR)),
                    "description": content[:150].strip(),
                })
            except Exception as e:
                log.debug(f"Failed to index doc {doc_file}: {e}")

    def _extract_description(self, content: str) -> str:
        """Extract component/surface description from file."""
        import re

        # Look for docstring
        doc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if doc_match:
            desc = doc_match.group(1).strip()
            # Clean up
            desc = re.sub(r'\s+', ' ', desc)
            return desc[:200]

        # Look for comment block
        comment_match = re.search(r'/\*\*(.*?)\*/', content, re.DOTALL)
        if comment_match:
            desc = comment_match.group(1).strip()
            desc = re.sub(r'\s+', ' ', desc)
            return desc[:200]

        return "No description available"

    def _extract_exports(self, content: str) -> List[str]:
        """Extract exported names from component."""
        import re

        exports = []
        # Find all export statements
        export_matches = re.findall(r'export\s+(?:const|function|class|interface|type)\s+(\w+)', content)
        exports.extend(export_matches)

        # Find default exports
        default_match = re.search(r'export\s+default\s+(\w+)', content)
        if default_match:
            exports.append(f"default: {default_match.group(1)}")

        return exports