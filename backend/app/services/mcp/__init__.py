"""MCP Bridge — Cross-Machine Tool & Skill Execution (uCore integrated).

Provides remote tool calling, peer management, and AI provider routing
using uCore's logging and settings infrastructure.

Usage:
    from app.services.mcp import get_bridge, MCPBridge
    bridge = get_bridge()
    result = await bridge.call_tool("forge", "copernicus.search", {"query": "test"})
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

try:
    from aiohttp import ClientSession, ClientTimeout
except ImportError:
    ClientSession = None
    ClientTimeout = None

from app.core.logging import log as ucore_log

# Use uCore's logger
log = ucore_log.getChild("mcp_bridge")

# ─── Default Peers ─────────────────────────────────────────────────

DEFAULT_PEERS: dict[str, dict] = {
    "wizard": {
        "id": "wizard",
        "name": "Mac Studio (local)",
        "endpoint": "http://localhost:8484",
        "transport": "http",
        "status": "unknown",
    },
    "forge": {
        "id": "forge",
        "name": "Linux Mint (NAS)",
        "endpoint": "http://192.168.1.100:8484",
        "transport": "snackmachine",
        "status": "unknown",
        "snackmachine": {
            "commands_path": str(Path.home() / ".local/share/snackmachine/commands.jsonl"),
            "replies_path": str(Path.home() / ".local/share/snackmachine/replies.jsonl"),
            "poll_interval": 0.5,
            "poll_timeout": 60,
        },
    },
    "ollama": {
        "id": "ollama",
        "name": "Local Ollama",
        "endpoint": "http://localhost:11434",
        "transport": "http",
        "status": "unknown",
    },
}


# ─── Snackmachine Transport ────────────────────────────────────────


class SnackmachineTransport:
    """File-based transport for communicating with Snackmachine on Linux."""

    def __init__(self, config: dict):
        self.commands_path = Path(
            config.get("commands_path", "~/.local/share/snackmachine/commands.jsonl"),
        ).expanduser()
        self.replies_path = Path(
            config.get("replies_path", "~/.local/share/snackmachine/replies.jsonl"),
        ).expanduser()
        self.poll_interval = config.get("poll_interval", 0.5)
        self.poll_timeout = config.get("poll_timeout", 60)
        self.commands_path.parent.mkdir(parents=True, exist_ok=True)

    def write_command(self, cmd: dict) -> str:
        correlation_id = str(uuid.uuid4())
        cmd["correlation_id"] = correlation_id
        cmd["timestamp"] = time.time()
        with open(self.commands_path, "a") as f:
            f.write(json.dumps(cmd) + "\n")
        log.debug("Wrote command %s to %s", correlation_id, self.commands_path)
        return correlation_id

    def poll_for_reply(self, correlation_id: str, timeout: float | None = None) -> dict | None:
        timeout = timeout or self.poll_timeout
        deadline = time.time() + timeout
        last_size = 0
        if self.replies_path.exists():
            last_size = self.replies_path.stat().st_size
        while time.time() < deadline:
            if self.replies_path.exists():
                current_size = self.replies_path.stat().st_size
                if current_size > last_size:
                    with open(self.replies_path) as f:
                        f.seek(last_size)
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                                if entry.get("correlation_id") == correlation_id:
                                    return entry
                            except json.JSONDecodeError:
                                continue
                    last_size = current_size
            time.sleep(self.poll_interval)
        return None

    def check_health(self) -> bool:
        return self.replies_path.exists()

    def list_available(self) -> dict:
        spices, skills = [], []
        if self.replies_path.exists():
            with open(self.replies_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "list_spices":
                            spices = entry.get("spices", [])
                        elif entry.get("type") == "list_skills":
                            skills = entry.get("skills", [])
                    except json.JSONDecodeError:
                        continue
        return {"spices": spices, "skills": skills}


# ─── MCP Bridge ────────────────────────────────────────────────────


class MCPBridge:
    """Cross-machine MCP tool and skill execution bridge."""

    def __init__(self, peers: dict | None = None):
        self.peers = peers or DEFAULT_PEERS.copy()
        self._session: ClientSession | None = None
        self._timeout = ClientTimeout(total=30) if ClientTimeout else None
        self._snackmachine_transports: dict[str, SnackmachineTransport] = {}

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            if ClientSession is None:
                raise RuntimeError("aiohttp is required for MCP bridge")
            self._session = ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_snackmachine_transport(self, peer_id: str) -> SnackmachineTransport | None:
        if peer_id not in self._snackmachine_transports:
            peer = self.peers.get(peer_id)
            if not peer or "snackmachine" not in peer:
                return None
            self._snackmachine_transports[peer_id] = SnackmachineTransport(peer["snackmachine"])
        return self._snackmachine_transports[peer_id]

    # ── Peer Management ──────────────────────────────────────────

    def get_peers(self) -> dict:
        return self.peers

    def get_peer(self, peer_id: str) -> dict | None:
        return self.peers.get(peer_id)

    def set_peer_status(self, peer_id: str, status: str):
        if peer_id in self.peers:
            self.peers[peer_id]["status"] = status

    async def check_peer_health(self, peer_id: str) -> dict:
        peer = self.peers.get(peer_id)
        if not peer:
            return {"peer": peer_id, "status": "unknown", "error": "Unknown peer"}
        transport = peer.get("transport", "http")

        if transport == "snackmachine":
            sm = self._get_snackmachine_transport(peer_id)
            if sm and sm.check_health():
                self.peers[peer_id]["status"] = "online"
                return {"peer": peer_id, "status": "online", "transport": "snackmachine", "latency_ms": 0}
            self.peers[peer_id]["status"] = "offline"
            return {"peer": peer_id, "status": "offline", "transport": "snackmachine", "error": "Snackmachine replies file not found"}

        endpoint = peer["endpoint"]
        try:
            session = await self._get_session()
            start = time.time()
            async with session.get(
                urljoin(endpoint + "/", "v1/health"),
                timeout=self._timeout,
            ) as resp:
                latency_ms = int((time.time() - start) * 1000)
                if resp.status == 200:
                    data = await resp.json()
                    self.peers[peer_id]["status"] = "online"
                    return {"peer": peer_id, "status": "online", "latency_ms": latency_ms, "version": data.get("version", "unknown")}
                self.peers[peer_id]["status"] = "offline"
                return {"peer": peer_id, "status": "offline", "error": f"HTTP {resp.status}"}
        except Exception as e:
            self.peers[peer_id]["status"] = "offline"
            return {"peer": peer_id, "status": "offline", "error": str(e)}

    async def check_all_peers(self) -> list[dict]:
        results = []
        for peer_id in self.peers:
            result = await self.check_peer_health(peer_id)
            results.append(result)
        return results

    # ── MCP Tool Bridge ─────────────────────────────────────────

    async def call_tool(self, peer_id: str, tool: str, params: dict | None = None) -> dict:
        peer = self.peers.get(peer_id)
        if not peer:
            return {"success": False, "error": f"Unknown peer: {peer_id}"}
        transport = peer.get("transport", "http")
        if transport == "snackmachine":
            return await self._call_tool_snackmachine(peer_id, tool, params)
        return await self._call_tool_http(peer_id, tool, params)

    async def _call_tool_snackmachine(self, peer_id: str, tool: str, params: dict | None = None) -> dict:
        sm = self._get_snackmachine_transport(peer_id)
        if not sm:
            return {"success": False, "error": f"No Snackmachine transport for peer: {peer_id}"}
        if not sm.check_health():
            self.peers[peer_id]["status"] = "offline"
            return {"success": False, "error": f"Peer {peer_id} is offline (replies file not found)"}
        self.peers[peer_id]["status"] = "online"
        start = time.time()
        cmd = {
            "type": "run_spice" if tool.startswith("spice:") else "run_skill",
            "name": tool.replace("spice:", "").replace("skill:", ""),
            "params": params or {},
        }
        correlation_id = sm.write_command(cmd)
        reply = sm.poll_for_reply(correlation_id)
        latency_ms = int((time.time() - start) * 1000)
        if reply is None:
            return {"success": False, "error": "Timeout waiting for Snackmachine reply", "peer": peer_id, "latency_ms": latency_ms}
        return {"success": reply.get("status") == "success", "result": {"output": reply.get("output", ""), "error": reply.get("error", ""), "status": reply.get("status", "unknown")}, "peer": peer_id, "latency_ms": latency_ms}

    async def _call_tool_http(self, peer_id: str, tool: str, params: dict | None = None) -> dict:
        peer = self.peers.get(peer_id)
        if not peer:
            return {"success": False, "error": f"Unknown peer: {peer_id}"}
        if peer["status"] == "offline":
            health = await self.check_peer_health(peer_id)
            if health["status"] != "online":
                return {"success": False, "error": f"Peer {peer_id} is offline"}
        endpoint = peer["endpoint"]
        payload = {"tool": tool, "params": params or {}}
        try:
            session = await self._get_session()
            start = time.time()
            async with session.post(urljoin(endpoint + "/", "v1/mcp/call"), json=payload, timeout=self._timeout) as resp:
                latency_ms = int((time.time() - start) * 1000)
                if resp.status == 200:
                    result = await resp.json()
                    return {"success": True, "result": result.get("result", result), "peer": peer_id, "latency_ms": latency_ms}
                error_text = await resp.text()
                return {"success": False, "error": f"Remote error (HTTP {resp.status}): {error_text}", "peer": peer_id, "latency_ms": latency_ms}
        except Exception as e:
            self.peers[peer_id]["status"] = "offline"
            return {"success": False, "error": str(e), "peer": peer_id}

    async def list_remote_tools(self, peer_id: str) -> dict:
        peer = self.peers.get(peer_id)
        if not peer:
            return {"success": False, "error": f"Unknown peer: {peer_id}"}
        transport = peer.get("transport", "http")
        if transport == "snackmachine":
            sm = self._get_snackmachine_transport(peer_id)
            if not sm:
                return {"success": False, "error": f"No Snackmachine transport for peer: {peer_id}"}
            available = sm.list_available()
            tools = []
            for spice in available.get("spices", []):
                tools.append({"name": f"spice:{spice}", "description": f"Snackmachine spice: {spice}", "server": peer_id})
            for skill in available.get("skills", []):
                tools.append({"name": f"skill:{skill}", "description": f"Snackmachine skill: {skill}", "server": peer_id})
            return {"success": True, "peer": peer_id, "tools": tools}
        endpoint = peer["endpoint"]
        try:
            session = await self._get_session()
            async with session.get(urljoin(endpoint + "/", "v1/mcp/tools"), timeout=self._timeout) as resp:
                if resp.status == 200:
                    tools = await resp.json()
                    return {"success": True, "peer": peer_id, "tools": tools.get("tools", tools)}
                return {"success": False, "error": f"HTTP {resp.status}", "peer": peer_id}
        except Exception as e:
            return {"success": False, "error": str(e), "peer": peer_id}

    async def get_mesh_tools(self) -> dict:
        local_tools, remote_tools = [], []
        for peer_id, peer in self.peers.items():
            if peer["status"] != "online":
                continue
            result = await self.list_remote_tools(peer_id)
            if result.get("success"):
                tools = result.get("tools", [])
                for tool in tools:
                    entry = {"name": tool.get("name", tool) if isinstance(tool, str) else tool, "server": peer_id, "enabled": True}
                    if peer_id in ("wizard", "localhost"):
                        local_tools.append(entry)
                    else:
                        remote_tools.append(entry)
        return {"local": local_tools, "remote": remote_tools, "total": len(local_tools) + len(remote_tools)}

    async def run_skill(self, peer_id: str, skill_id: str, params: dict | None = None) -> dict:
        peer = self.peers.get(peer_id)
        if not peer:
            return {"success": False, "error": f"Unknown peer: {peer_id}"}
        transport = peer.get("transport", "http")
        if transport == "snackmachine":
            sm = self._get_snackmachine_transport(peer_id)
            if not sm:
                return {"success": False, "error": f"No Snackmachine transport for peer: {peer_id}"}
            if not sm.check_health():
                self.peers[peer_id]["status"] = "offline"
                return {"success": False, "error": f"Peer {peer_id} is offline"}
            self.peers[peer_id]["status"] = "online"
            start = time.time()
            cmd = {"type": "run_skill", "name": skill_id, "params": params or {}}
            correlation_id = sm.write_command(cmd)
            reply = sm.poll_for_reply(correlation_id)
            duration_ms = int((time.time() - start) * 1000)
            if reply is None:
                return {"success": False, "error": "Timeout waiting for Snackmachine reply", "peer": peer_id, "duration_ms": duration_ms}
            return {"success": reply.get("status") == "success", "output": reply.get("output", ""), "error": reply.get("error", ""), "peer": peer_id, "duration_ms": duration_ms}
        if peer["status"] == "offline":
            health = await self.check_peer_health(peer_id)
            if health["status"] != "online":
                return {"success": False, "error": f"Peer {peer_id} is offline"}
        endpoint = peer["endpoint"]
        payload = {"params": params or {}}
        try:
            session = await self._get_session()
            start = time.time()
            async with session.post(urljoin(endpoint + "/", f"v1/skills/{skill_id}/run"), json=payload, timeout=self._timeout) as resp:
                duration_ms = int((time.time() - start) * 1000)
                if resp.status == 200:
                    result = await resp.json()
                    return {"success": True, "output": result.get("output", result), "peer": peer_id, "duration_ms": duration_ms}
                error_text = await resp.text()
                return {"success": False, "error": f"Remote error (HTTP {resp.status}): {error_text}", "peer": peer_id, "duration_ms": duration_ms}
        except Exception as e:
            self.peers[peer_id]["status"] = "offline"
            return {"success": False, "error": str(e), "peer": peer_id}

    async def get_mesh_status(self) -> dict:
        peer_health = await self.check_all_peers()
        mesh_tools = await self.get_mesh_tools()
        online_count = sum(1 for p in peer_health if p["status"] == "online")
        offline_count = sum(1 for p in peer_health if p["status"] == "offline")
        return {"peers": peer_health, "tools": mesh_tools, "summary": {"total_peers": len(peer_health), "online": online_count, "offline": offline_count, "total_tools": mesh_tools["total"]}}


# ─── Singleton ─────────────────────────────────────────────────────

_bridge_instance: MCPBridge | None = None


def get_bridge() -> MCPBridge:
    """Get or create the singleton MCPBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = MCPBridge()
    return _bridge_instance
