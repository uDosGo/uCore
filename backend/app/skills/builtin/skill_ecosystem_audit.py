"""Ecosystem Audit Skill — comprehensive inventory of uCore ecosystem.

Discovers and catalogues:
  - Skills (name, file, category, description, params from SkillMeta)
  - Paths (file system paths used by skills, configs, vault, seeds)
  - Variables (scope, key, type, default from variable APIs)
  - Secrets (key, store, scope from config/env files)
  - MCP Servers (name, command, port, tools from mcp_config.json)
  - Routes (method, path, handler from routes.py)
  - Runtimes (name, file, endpoints, variables, commands from backend modules)

Generates seeds/ecosystem-registry.json for frontend consumption.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.ecosystem_audit")

ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend" / "app"
SKILLS_DIR = BACKEND_DIR / "skills" / "builtin"
UCODE_DIR = ROOT_DIR.parent / "uCode"
HOMENEST_DIR = ROOT_DIR.parent / "HomeNest"
REPO_MAP = {
    str(ROOT_DIR): "uCore",
    str(ROOT_DIR.parent / "uCode"): "uCode",
    str(ROOT_DIR.parent / "HomeNest"): "HomeNest",
}


def _repo_for(path: Path) -> str:
    """Determine which repo a path belongs to."""
    sp = str(path)
    for root, name in REPO_MAP.items():
        if sp.startswith(root):
            return name
    return "unknown"
API_DIR = BACKEND_DIR / "api"
ROUTES_FILE = API_DIR / "routes.py"
MCP_CONFIG_FILE = ROOT_DIR / "config" / "mcp_config.json"
ENV_FILE = ROOT_DIR.parent.parent / ".config" / "hivemind" / ".env"
VAULT_CONFIG = ROOT_DIR.parent / "uCode" / "config" / "vault.yaml"
SECRETS_API = API_DIR / "secret_store_api.py"
VARIABLES_API = API_DIR / "variables_api.py"
SEEDS_DIR = ROOT_DIR / "seeds"
OUTPUT_FILE = SEEDS_DIR / "ecosystem-registry.json"

EXCLUDES = {"__pycache__", "__archived__", ".mypy_cache", "__init__"}


class EcosystemAuditSkill(BaseSkill):
    meta = SkillMeta(
        id="ecosystem-audit",
        name="Ecosystem Auditor v1",
        description=(
            "Comprehensive ecosystem audit: skills, paths,"
            " variables, secrets, MCP servers, routes, runtimes."
            " Generates ecosystem-registry.json."
        ),
        category="developer",
        params=[
            SkillParam(
                name="action",
                type="string",
                description=(
                    "Action: 'audit-skills', 'audit-routes',"
                    " 'audit-secrets', 'audit-variables',"
                    " 'audit-mcp', 'audit-paths',"
                    " 'audit-runtimes', 'report', 'generate'"
                ),
                required=True,
            ),
            SkillParam(
                name="output",
                type="string",
                description="Output path for generated JSON",
                required=False,
            ),
        ],
        timeout=180,
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "report")
        output = kwargs.get("output", str(OUTPUT_FILE))

        actions = {
            "audit-skills": lambda: self._audit_skills(),
            "audit-routes": lambda: self._audit_routes(),
            "audit-secrets": lambda: self._audit_secrets(),
            "audit-variables": lambda: self._audit_variables(),
            "audit-mcp": lambda: self._audit_mcp(),
            "audit-paths": lambda: self._audit_paths(),
            "audit-runtimes": lambda: self._audit_runtimes(),
            "report": lambda: self._report(),
            "generate": lambda: self._generate(output),
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}"}
        return handler()

    # ─── Audit Skills ────────────────────────────────────────────────

    def _audit_skills(self) -> dict:
        """Discover all builtin skills with metadata."""
        skills = []
        if not SKILLS_DIR.exists():
            return {"success": True, "skills": []}

        for f in sorted(SKILLS_DIR.glob("*.py")):
            if f.name.startswith("_") or f.name in EXCLUDES:
                continue

            skill_info = self._parse_skill_file(f)
            if skill_info:
                skills.append(skill_info)

        return {"success": True, "skills": skills, "total": len(skills)}

    def _parse_skill_file(self, filepath: Path) -> dict | None:
        """Extract SkillMeta from a skill Python file."""
        try:
            content = filepath.read_text()
        except Exception:
            return None

        info: dict = {
            "file": str(filepath.relative_to(ROOT_DIR)),
            "name": filepath.stem.replace("skill_", "").replace("_", " "),
            "skill_id": "",
            "category": "unknown",
            "description": "",
            "params": [],
            "timeout": 0,
            "requires_confirmation": False,
        }

        # Extract skill id from SkillMeta
        id_match = re.search(r'id\s*=\s*"([^"]+)"', content)
        if id_match:
            info["skill_id"] = id_match.group(1)

        # Extract name
        name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
        if name_match:
            info["name"] = name_match.group(1)

        # Extract description
        desc_match = re.search(
            r'description\s*=\s*\(\s*\n?(.*?)\n?\s*\)',
            content, re.DOTALL,
        )
        if desc_match:
            desc = desc_match.group(1).strip().strip('"').strip("'")
            parts = desc.split()
            desc = " ".join([
                d.strip().strip('"').strip("'") for d in parts
            ])
            info["description"] = desc[:200]

        # Extract category
        cat_match = re.search(r'category\s*=\s*"([^"]+)"', content)
        if cat_match:
            info["category"] = cat_match.group(1)

        # Extract timeout
        timeout_match = re.search(r"timeout\s*=\s*(\d+)", content)
        if timeout_match:
            info["timeout"] = int(timeout_match.group(1))

        # Extract requires_confirmation
        if "requires_confirmation=True" in content:
            info["requires_confirmation"] = True

        # Extract SkillParams
        param_matches = re.findall(
            r'SkillParam\(\s*name\s*=\s*"([^"]+)"'
            r'.*?description\s*=\s*\(\s*(.*?)\s*\)',
            content, re.DOTALL,
        )
        for pname, pdesc in param_matches:
            pdesc_clean = " ".join(
                d.strip().strip('"').strip("'") for d in pdesc.split()
            )
            ptype = "string"
            type_match = re.search(
                rf'SkillParam\(\s*name\s*=\s*"{pname}".*?type\s*=\s*"([^"]+)"',
                content, re.DOTALL,
            )
            if type_match:
                ptype = type_match.group(1)
            info["params"].append({
                "name": pname,
                "type": ptype,
                "description": pdesc_clean[:120],
            })

        return info

    # ─── Audit Routes ─────────────────────────────────────────────────

    def _audit_routes(self) -> dict:
        """Extract all API routes from routes.py."""
        routes = []
        if not ROUTES_FILE.exists():
            return {"success": True, "routes": []}

        content = ROUTES_FILE.read_text()

        # Match: app.router.add_get("/api/...", handle_xyz)
        for match in re.finditer(
            r'app\.router\.add_(get|post|put|delete)\("([^"]+)"\s*,\s*(\w+)',
            content,
        ):
            routes.append({
                "method": match.group(1).upper(),
                "path": match.group(2),
                "handler": match.group(3),
            })

        # Also look for try/except block imports
        import_blocks = re.findall(
            r"from \.(\w+)\s+import\s+(\w+)", content,
        )
        modules_used = list(set(m[0] for m in import_blocks))

        return {
            "success": True,
            "routes": sorted(routes, key=lambda r: r["path"]),
            "total": len(routes),
            "modules_used": sorted(modules_used),
        }

    # ─── Audit Secrets ────────────────────────────────────────────────

    def _audit_secrets(self) -> dict:
        """Discover secret keys from env files and configs."""
        secrets = []

        # Check hivemind .env
        if ENV_FILE.exists():
            content = ENV_FILE.read_text()
            for match in re.finditer(
                r'(#\s*(.*?)\n)?\s*(\w+)\s*=\s*"[^"]*"', content,
            ):
                key = match.group(3)
                comment = match.group(2) or ""
                secrets.append({
                    "key": key,
                    "scope": "environment",
                    "store": "~/.config/hivemind/.env",
                    "description": comment.strip()[:100],
                })

        # Check vault.yaml for secret references
        if VAULT_CONFIG.exists():
            content = VAULT_CONFIG.read_text()
            key_matches = re.findall(r'-\s*"(\w+)"', content)
            for key in key_matches:
                if any(k.upper() in ("KEY", "TOKEN", "SECRET") for k in [key]):
                    secrets.append({
                        "key": key,
                        "scope": "vault",
                        "store": "~/.local/share/udos/Vault/",
                        "description": "Referenced in vault.yaml",
                    })

        return {"success": True, "secrets": secrets, "total": len(secrets)}

    # ─── Audit Variables ──────────────────────────────────────────────

    def _audit_variables(self) -> dict:
        """Discover variable scopes and keys."""
        variables = []

        # From vault.yaml
        if VAULT_CONFIG.exists():
            variables.append({
                "scope": "user",
                "file": "~/.local/share/udos/Vault/variables/user.yaml",
                "description": "User-level persistent variables",
                "examples": ["theme", "editor_font_size", "last_world"],
            })
            variables.append({
                "scope": "global",
                "file": "~/.local/share/udos/Vault/variables/global.yaml",
                "description": "System-wide variables",
                "examples": ["runtime_version", "engine"],
            })
            variables.append({
                "scope": "snack",
                "file": "snack manifest (per-container)",
                "description": "Per-snack container state",
                "examples": ["level", "player_hp"],
            })
            variables.append({
                "scope": "system",
                "file": "memory only (not persisted)",
                "description": "Runtime-only state",
                "examples": ["pid", "uptime_seconds"],
            })

        # From variables_api.py
        if VARIABLES_API.exists():
            content = VARIABLES_API.read_text()
            get_vars = re.findall(r'handle_get_(\w+)_variables', content)
            for gv in get_vars:
                variables.append({
                    "scope": gv,
                    "source": "variables_api.py",
                    "description": f"Exposed via /api/variables/{gv}",
                    "examples": [],
                })

        return {"success": True, "variables": variables, "total": len(variables)}

    # ─── Audit MCP ────────────────────────────────────────────────────

    def _audit_mcp(self) -> dict:
        """Discover MCP server configurations."""
        servers = []

        # From mcp_config.json
        if MCP_CONFIG_FILE.exists():
            try:
                data = json.loads(MCP_CONFIG_FILE.read_text())
                for name, config in data.get("mcpServers", {}).items():
                    servers.append({
                        "name": name,
                        "command": config.get("command", ""),
                        "cwd": config.get("cwd", ""),
                        "disabled": config.get("disabled", False),
                        "source": "config/mcp_config.json",
                    })
            except Exception:
                pass

        # Also check registered MCP tools in the backend
        mcp_tools_dir = BACKEND_DIR / "mcp"
        if mcp_tools_dir.exists():
            for mcp_mod in mcp_tools_dir.glob("*_server.py"):
                servers.append({
                    "name": mcp_mod.stem.replace("_server", ""),
                    "file": str(mcp_mod.relative_to(ROOT_DIR)),
                    "source": "backend auto-discovery",
                    "command": f"python3 -m app.mcp.{mcp_mod.stem}",
                    "cwd": str(BACKEND_DIR),
                })

        return {"success": True, "servers": servers, "total": len(servers)}

    # ─── Audit Paths ──────────────────────────────────────────────────

    def _audit_paths(self) -> dict:
        """Discover all important file system paths used by the ecosystem."""
        paths = []

        # Config paths
        config_dirs = [
            str(ROOT_DIR / "config"),
            str(ROOT_DIR / "seeds"),
            str(ROOT_DIR / "docs"),
            str(ROOT_DIR / "backend" / "config"),
            str(ROOT_DIR / "frontend-vue" / "src" / "styles"),
        ]
        for d in config_dirs:
            path = Path(d)
            if path.exists():
                paths.append({
                    "path": str(path.relative_to(ROOT_DIR)),
                    "type": "config",
                    "description": "Configuration directory",
                })

        # Runtime paths
        runtime_paths = [
            "~/.config/hivemind/.env",
            "~/.config/cline/mcp_config.json",
            "~/.local/share/udos/Vault/",
            "~/.local/share/udos/programs/",
            "~/.local/share/udos/snacks/",
        ]
        for p in runtime_paths:
            paths.append({
                "path": p,
                "type": "runtime",
                "description": "User runtime path",
            })

        # Skills directory
        paths.append({
            "path": "backend/app/skills/builtin/",
            "type": "skills",
            "description": "Builtin skills directory",
        })

        # API directory
        paths.append({
            "path": "backend/app/api/",
            "type": "api",
            "description": "REST API handlers",
        })

        # MCP directory
        paths.append({
            "path": "backend/app/mcp/",
            "type": "mcp",
            "description": "MCP servers directory",
        })

        # Services
        paths.append({
            "path": "backend/app/services/",
            "type": "services",
            "description": "Backend service modules",
        })

        return {"success": True, "paths": paths, "total": len(paths)}

    # ─── Audit Runtimes ───────────────────────────────────────────────

    def _audit_runtimes(self) -> dict:
        """Discover backend runtime service modules."""
        runtimes = {}

        candidate_modules: dict[str, Path] = {
            "dev_layer": BACKEND_DIR / "services" / "dev_layer.py",
            "feed_server": BACKEND_DIR / "mcp" / "feed" / "feed_server.py",
            "feed_consumer": BACKEND_DIR / "services" / "feed_consumer.py",
            "hivemind_server": BACKEND_DIR / "mcp" / "hivemind_server.py",
            "llm_router": BACKEND_DIR / "mcp" / "llm_router.py",
            "cost_manager": BACKEND_DIR / "services" / "cost_manager.py",
            "template_manager": BACKEND_DIR / "services" / "template_manager.py",
            "tasker_ingest": BACKEND_DIR / "mcp" / "tasker_ingest.py",
        }

        for name, path in candidate_modules.items():
            if not path.exists():
                continue
            content = path.read_text()

            endpoints = []
            for match in re.findall(
                r'"([a-z_]+)"\s*:\s*self\._[a-z_]+', content,
            ):
                endpoints.append(match)
            for match in re.findall(r'name="([a-z_]+)"', content):
                endpoints.append(match)

            variables = {}
            for match in re.findall(
                r"self\.([a-z_]+)\s*=\s*([^#\n]+)", content,
            ):
                key, val = match
                if len(key) > 2 and not key.startswith("_"):
                    variables[key] = val.strip().rstrip(",")

            commands = []
            for match in re.findall(r"(?:async )?def ([a-z_]+)\(", content):
                if not match.startswith("_"):
                    commands.append(match)

            runtimes[name] = {
                "file": str(path.relative_to(ROOT_DIR)),
                "endpoints": sorted(set(endpoints)),
                "variables": variables,
                "commands": sorted(set(commands)),
            }

        return {"success": True, "runtimes": runtimes, "total": len(runtimes)}

    # ─── Report / Generate ────────────────────────────────────────────

    def _report(self) -> dict:
        """Full ecosystem report."""
        skills = self._audit_skills()
        routes = self._audit_routes()
        secrets = self._audit_secrets()
        variables = self._audit_variables()
        mcp = self._audit_mcp()
        paths = self._audit_paths()
        runtimes = self._audit_runtimes()

        return {
            "success": True,
            "action": "report",
            "ecosystem": {
                "skills": {
                    "total": skills.get("total", 0),
                    "items": skills.get("skills", []),
                },
                "routes": {
                    "total": routes.get("total", 0),
                    "items": routes.get("routes", []),
                },
                "secrets": {
                    "total": secrets.get("total", 0),
                    "items": secrets.get("secrets", []),
                },
                "variables": {
                    "total": variables.get("total", 0),
                    "items": variables.get("variables", []),
                },
                "mcp_servers": {
                    "total": mcp.get("total", 0),
                    "items": mcp.get("servers", []),
                },
                "paths": {
                    "total": paths.get("total", 0),
                    "items": paths.get("paths", []),
                },
                "runtimes": {
                    "total": runtimes.get("total", 0),
                    "items": runtimes.get("runtimes", {}),
                },
            },
            "summary": {
                "total_skills": skills.get("total", 0),
                "total_routes": routes.get("total", 0),
                "total_secrets": secrets.get("total", 0),
                "total_variables": variables.get("total", 0),
                "total_mcp_servers": mcp.get("total", 0),
                "total_paths": paths.get("total", 0),
                "total_runtimes": runtimes.get("total", 0),
            },
        }

    def _generate(self, output_path: str) -> dict:
        """Generate ecosystem-registry.json to disk."""
        report = self._report()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, default=str),
        )
        return {
            "success": True,
            "action": "generate",
            "output": str(output),
            "size_bytes": output.stat().st_size,
            "summary": report.get("summary", {}),
        }