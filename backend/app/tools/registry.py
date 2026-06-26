"""Tool registry helpers for discovering and probing local tool probes.

This module discovers Python files under the `backend/app/tools` directory
that expose `BaseTool` subclasses and provides helpers to list and check
those tools.
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
import sys
from pathlib import Path

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger("ucore.tools.registry")

_registry: dict[str, BaseTool] = {}
TOOLS_PATHS = [Path(__file__).parent]


def _discover() -> dict[str, BaseTool]:
    """Discover and instantiate all Tool classes in the tools directory."""
    tools: dict[str, BaseTool] = {}
    for td in TOOLS_PATHS:
        sys.path.insert(0, str(td.parent))
        try:
            for f in td.iterdir():
                # only Python modules, skip private files
                if f.suffix != ".py" or f.name.startswith("_"):
                    continue
                try:
                    spec = importlib.util.spec_from_file_location(f"tools_{f.stem}", f)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        for _, obj in inspect.getmembers(mod):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, BaseTool)
                                and obj is not BaseTool
                            ):
                                t = obj()
                                tools[t.id] = t
                except Exception as exc:  # pragma: no cover - best-effort discovery
                    # Discovery should be best-effort; report and continue.
                    log.warning("Tool load fail %s: %s", f.name, exc)
        finally:
            sys.path.pop(0)
    return tools


def _ensure() -> None:
    """Populate the module registry cache if empty."""
    global _registry
    if not _registry:
        _registry = _discover()


async def list_tools() -> list[ToolInfo]:
    """Return checked ToolInfo for all registered tools."""
    _ensure()
    return [await t.check() for t in _registry.values()]


def get_tool(tool_id: str) -> BaseTool | None:
    """Return the probe instance for `tool_id` or None if unknown."""
    _ensure()
    return _registry.get(tool_id)


async def check_tool(tool_id: str) -> ToolInfo | dict:
    """Run the probe for a single tool and return its ToolInfo.

    If the tool is not registered, returns a dict with `installed: False`.
    """
    t = get_tool(tool_id)
    if not t:
        return {"installed": False, "error": f"Tool '{tool_id}' not found"}
    return await t.check()
