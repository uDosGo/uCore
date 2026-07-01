"""
Prototype MCP diagnostics endpoint helpers.
This module exposes a function to gather current MCP state for diagnostics.
"""
import json
import os
from pathlib import Path

UCORE_BACKEND_DIR = os.environ.get(
    "UCORE_BACKEND_DIR",
    str(Path.home() / "Code" / "uCore" / "backend"),
)
REGISTRY_PATH = Path(UCORE_BACKEND_DIR) / "mcp" / "mcp-manifest.json"

def read_registry():
    try:
        withREG = REGISTRY_PATH.read_text()
        return json.loads(withREG)
    except Exception:
        return {"error": "registry_unreadable"}

def list_tools():
    reg = read_registry()
    tools = reg.get("tools", []) if reg else []
    return tools

def health():
    return {"health": "ok"}
