from __future__ import annotations
import importlib.util, inspect, logging, sys, asyncio
from pathlib import Path
from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger("ucore.tools.registry")
_registry: dict[str, BaseTool] = {}
TOOLS_PATHS = [Path(__file__).parent]

def _discover():
    tools = {}
    for td in TOOLS_PATHS:
        sys.path.insert(0, str(td.parent))
        for f in td.iterdir():
            if f.suffix != ".py" or f.name.startswith("_"): continue
            try:
                spec = importlib.util.spec_from_file_location(f"tools_{f.stem}", f)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for _, obj in inspect.getmembers(mod):
                        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                            t = obj(); tools[t.id] = t
            except Exception as e:
                log.warning(f"Tool load fail {f.name}: {e}")
        sys.path.pop(0)
    return tools

def _ensure():
    global _registry; 
    if not _registry: _registry = _discover()

def list_tools() -> list[ToolInfo]:
    _ensure()
    return [asyncio.run(t.check()) for t in _registry.values()]

def get_tool(tool_id: str) -> BaseTool | None:
    _ensure(); return _registry.get(tool_id)

async def check_tool(tool_id: str) -> ToolInfo | dict:
    t = get_tool(tool_id)
    if not t: return {"installed": False, "error": f"Tool '{tool_id}' not found"}
    return await t.check()
