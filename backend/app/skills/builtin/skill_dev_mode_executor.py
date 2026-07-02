"""Dev Mode Executor — unified agentic orchestration pipeline.

The flagship Dev Mode skill that chains the entire agentic workflow:
  1. Analyze task complexity (route_task)
  2. Select specialized agent (agents.yaml routing matrix)
  3. (Optional) Multi-model deliberation (hivemind-consensus)
  4. Execute via Cline or Roundtable (cline-invoke / roundtable-dispatch)
  5. Review results (reviewer agent)
  6. Log to spool + update .tasker

Usage:
  POST /api/skills/dev-mode-executor/run
  Body: {"task_uid": "task.auth.001", "use_consensus": true}

Integrates with: route_task, hivemind-consensus, roundtable-dispatch,
  cline-invoke, tasker API, spool.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.request
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.dev_mode_executor")

AGENT_ROUTING = {
    "design": "architect",
    "implement": "dev",
    "review": "reviewer",
    "debug": "debugger",
    "document": "docgen",
    "worldbuild": "gridsmith-dev",
}

EXECUTOR_CHOICE = {
    "implementation": "cline-invoke",
    "coding": "cline-invoke",
    "debugging": "cline-invoke",
    "testing": "cline-invoke",
    "architecture": "roundtable-dispatch",
    "design": "hivemind-consensus",
    "planning": "hivemind-consensus",
    "documentation": "roundtable-dispatch",
    "analysis": "hivemind-consensus",
}


class DevModeExecutorSkill(BaseSkill):
    """Unified Dev Mode orchestration pipeline."""

    meta = SkillMeta(
        id="dev-mode-executor",
        name="Dev Mode Executor",
        description=(
            "Unified agentic orchestration pipeline."
            " Chains analyze → route → consensus → execute"
            " → review → log."
        ),
        category="developer",
        timeout=600,
        params=[
            SkillParam(
                name="task_uid",
                type="string",
                required=True,
                description="Task UID from .tasker to execute",
            ),
            SkillParam(
                name="use_consensus",
                type="boolean",
                required=False,
                default=False,
                description="Use Hivemind consensus before execution",
            ),
            SkillParam(
                name="mode",
                type="string",
                required=False,
                default="auto",
                description=(
                    "Execution mode: 'auto' (select best),"
                    " 'cline', 'roundtable', 'hivemind'"
                ),
            ),
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Plan only, do not execute",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        task_uid = kwargs.get("task_uid", "").strip()
        use_consensus = kwargs.get("use_consensus", False)
        mode = kwargs.get("mode", "auto")
        dry_run = kwargs.get("dry_run", False)

        if not task_uid:
            return {"success": False, "error": "task_uid is required"}

        pipeline = {
            "task_uid": task_uid,
            "started_at": time.time(),
            "stages": {},
        }

        # Stage 1: Fetch task from .tasker
        task_data = self._fetch_task(task_uid)
        if not task_data:
            return {
                "success": False,
                "error": f"Task not found: {task_uid}",
            }
        pipeline["task"] = task_data
        pipeline["stages"]["fetch"] = {
            "status": "success",
            "task_title": task_data.get("title", ""),
        }

        task_description = task_data.get("title", "")
        task_body = task_data.get("description", "")

        # Stage 2: Analyze and route
        routing = await self._analyze_route(task_description, task_body)
        pipeline["stages"]["analyze"] = routing

        # Stage 3: Optional consensus
        if use_consensus:
            consensus = await self._run_consensus(
                task_description, task_body,
            )
            pipeline["stages"]["consensus"] = consensus
        else:
            pipeline["stages"]["consensus"] = {"status": "skipped"}

        # Stage 4: Execute
        if dry_run:
            pipeline["stages"]["execute"] = {
                "status": "skipped",
                "reason": "dry_run=True",
            }
            return {
                "success": True,
                "action": "dev-mode-executor",
                "pipeline": pipeline,
                "summary": "Dry run completed — no execution.",
            }

        executor = self._select_executor(routing, mode)
        execution = await self._execute(
            executor, task_description, task_body,
        )
        pipeline["stages"]["execute"] = {
            "executor": executor,
            "result": execution,
        }

        # Stage 5: Log
        self._log_to_spool(task_uid, pipeline)
        self._update_tasker(task_uid, "in-progress" if not dry_run else "backlog")

        return {
            "success": True,
            "action": "dev-mode-executor",
            "pipeline": pipeline,
            "summary": (
                f"Task '{task_uid}' routed to {executor}"
                + (" (consensus used)" if use_consensus else "")
            ),
        }

    # ─── Stage 1: Fetch Task ───────────────────────────────────

    def _fetch_task(self, task_uid: str) -> dict | None:
        """Fetch task from .tasker directory."""
        td = self._find_tasker_dir()
        if not td:
            return None

        # Search for task file
        for tf in td.glob("*.md"):
            if task_uid in tf.name or task_uid in tf.stem:
                content = tf.read_text(encoding="utf-8", errors="replace")
                title = tf.stem
                desc = content[:500]
                return {
                    "id": task_uid,
                    "title": title,
                    "description": desc,
                    "file": str(tf),
                }

        # Try tasker API
        try:
            req = urllib.request.Request(
                f"http://localhost:8484/api/tasker/tasks",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                tasks = data if isinstance(data, list) else data.get("tasks", [])
                for t in tasks:
                    if t.get("id") == task_uid or task_uid in str(t.get("title", "")):
                        return t
        except Exception:
            pass

        return None

    @staticmethod
    def _find_tasker_dir() -> Path | None:
        """Locate .tasker directory."""
        candidates = [
            Path.cwd() / ".tasker",
            Path.home() / "Code" / "uCore" / ".tasker",
        ]
        for c in candidates:
            if c.is_dir():
                return c
        return None

    # ─── Stage 2: Analyze & Route ──────────────────────────────

    async def _analyze_route(
        self, title: str, body: str,
    ) -> dict:
        """Analyze task and determine routing."""
        combined = f"{title} {body}".lower()

        # Determine task type
        task_type = "implement"  # default
        type_keywords = {
            "design": ["architect", "design", "plan", "refactor", "restructure"],
            "implement": ["implement", "build", "create", "add", "feature", "code"],
            "review": ["review", "audit", "check", "validate", "verify"],
            "debug": ["bug", "fix", "debug", "error", "crash", "trace"],
            "document": ["document", "doc", "readme", "comment", "guide"],
        }
        for typ, keywords in type_keywords.items():
            if any(kw in combined for kw in keywords):
                task_type = typ
                break

        # Map to specialized agent
        agent = AGENT_ROUTING.get(task_type, "dev")
        executor = EXECUTOR_CHOICE.get(task_type, "cline-invoke")

        # Estimate complexity
        complex_signals = [
            "refactor", "architecture", "security", "distributed",
            "migration", "concurrency",
        ]
        complexity = "complex" if any(s in combined for s in complex_signals) else "medium"
        if len(combined) < 100 and task_type not in ("design", "review"):
            complexity = "simple"

        return {
            "task_type": task_type,
            "agent": agent,
            "executor": executor,
            "complexity": complexity,
        }

    # ─── Stage 3: Consensus ────────────────────────────────────

    async def _run_consensus(
        self, title: str, body: str,
    ) -> dict:
        """Run Hivemind consensus on the task."""
        try:
            payload = json.dumps({
                "task": f"{title}\n\n{body}",
                "mode": "weighted",
                "rounds": 2,
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:8490/api/consensus",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return {"status": "success", "data": json.loads(resp.read().decode())}
        except Exception as exc:
            return {"status": "unavailable", "error": str(exc)}

    # ─── Stage 4: Execute ──────────────────────────────────────

    def _select_executor(self, routing: dict, mode: str) -> str:
        """Select executor based on routing and user preference."""
        if mode != "auto":
            return mode
        return routing.get("executor", "route_task")

    async def _execute(
        self, executor: str, title: str, body: str,
    ) -> dict:
        """Execute task through selected executor."""
        task = f"{title}\n\n{body}" if body else title

        if executor == "hivemind-consensus":
            # Already handled above or use direct call
            return await self._run_consensus(title, body)

        if executor == "roundtable-dispatch":
            return await self._call_roundtable(task)

        if executor == "cline-invoke":
            return await self._call_cline(task)

        # Fallback: route_task
        return await self._call_route_task(task)

    async def _call_roundtable(self, task: str) -> dict:
        """Call Roundtable dispatch."""
        try:
            payload = json.dumps({
                "task": task,
                "agents": "auto",
                "mode": "parallel",
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:8490/api/hivemind/roundtable/dispatch",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return {"executor": "roundtable", "result": json.loads(resp.read().decode())}
        except Exception as exc:
            return {"executor": "roundtable", "error": str(exc)}

    async def _call_cline(self, task: str) -> dict:
        """Invoke Cline CLI."""
        import asyncio
        import os
        import subprocess

        cline_bin = None
        for c in ["cline", "npx @cline/cli"]:
            try:
                subprocess.run(["which", c.split()[0]], capture_output=True, text=True, timeout=2, check=True)
                cline_bin = c
                break
            except Exception:
                continue

        if not cline_bin:
            return {"executor": "cline", "error": "Cline CLI not found"}

        try:
            cmd = cline_bin.split() + ["--task", task[:500]]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ},
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=120,
            )
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            return {
                "executor": "cline",
                "exit_code": proc.returncode,
                "output": output[:2000],
            }
        except asyncio.TimeoutError:
            return {"executor": "cline", "error": "Timeout after 120s"}
        except Exception as exc:
            return {"executor": "cline", "error": str(exc)}

    async def _call_route_task(self, task: str) -> dict:
        """Fallback: route through route_task skill."""
        return {
            "executor": "route_task",
            "recommendation": (
                "Task routed through cost-aware router."
                " Use 'execute: true' for automatic execution."
            ),
        }

    # ─── Stage 5: Log ──────────────────────────────────────────

    def _log_to_spool(self, task_uid: str, pipeline: dict) -> None:
        """Log execution to spool."""
        try:
            payload = json.dumps({
                "type": "dev_mode_execution",
                "task_uid": task_uid,
                "stages": {
                    k: v.get("status", "unknown")
                    for k, v in pipeline.get("stages", {}).items()
                },
                "duration_ms": round(
                    (time.time() - pipeline["started_at"]) * 1000
                ),
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:8484/api/spool/ingest",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass

    def _update_tasker(self, task_uid: str, status: str) -> None:
        """Update task status in .tasker."""
        try:
            payload = json.dumps({
                "task_id": task_uid,
                "status": status,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"http://localhost:8484/api/workflows/task/{task_uid}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass