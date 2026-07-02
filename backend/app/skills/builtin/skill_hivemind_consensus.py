"""Hivemind Consensus Skill — multi-model deliberation via Hivemind server.

Triggers the Hivemind consensus engine (port 8490) to deliberate on
tasks using 3+ models in parallel, returning weighted consensus.

Consensus modes:
  - majority: at least 2 of 3 models agree
  - unanimous: all models must agree
  - weighted: each model's vote weighted by confidence
  - deliberative: models discuss and refine across rounds

Integrates with: Hivemind server, consensus engine, OpenRouter.
"""
from __future__ import annotations

import json
import logging
import urllib.request

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.hivemind_consensus")

HIVEMIND_URL = "http://localhost:8490"


class HivemindConsensusSkill(BaseSkill):
    """Multi-model deliberation through Hivemind consensus engine."""

    meta = SkillMeta(
        id="hivemind-consensus",
        name="Hivemind Consensus",
        description=(
            "Trigger multi-model deliberation via Hivemind server."
            " Calls 3+ models in parallel, returns weighted consensus."
        ),
        category="assist",
        timeout=120,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Task or question requiring deliberation",
            ),
            SkillParam(
                name="mode",
                type="string",
                required=False,
                default="weighted",
                description=(
                    "Consensus mode: 'majority', 'unanimous',"
                    " 'weighted', or 'deliberative'"
                ),
            ),
            SkillParam(
                name="models",
                type="string",
                required=False,
                default="",
                description=(
                    "Comma-separated model list. Empty = default set"
                    " (architect + dev agent models)"
                ),
            ),
            SkillParam(
                name="rounds",
                type="integer",
                required=False,
                default=3,
                description="Max deliberation rounds (deliberative mode only)",
            ),
            SkillParam(
                name="context",
                type="string",
                required=False,
                default="",
                description="Additional context for deliberation",
            ),
        ],
        requires_confirmation=False,
    )

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        mode = kwargs.get("mode", "weighted").lower()
        models_str = kwargs.get("models", "")
        rounds = int(kwargs.get("rounds", 3))
        context = kwargs.get("context", "")

        if not task:
            return {"success": False, "error": "task is required"}

        # Validate mode
        valid_modes = {"majority", "unanimous", "weighted", "deliberative"}
        if mode not in valid_modes:
            mode = "weighted"

        # Resolve models
        models = self._resolve_models(models_str, mode)

        # Build payload
        payload = {
            "task": task,
            "mode": mode,
            "models": models,
            "rounds": rounds,
            "context": context,
        }

        # Call Hivemind server
        try:
            result = await self._call_hivemind(payload)
            return {
                "success": True,
                "action": "hivemind-consensus",
                "mode": mode,
                "models_used": models,
                "result": result,
            }
        except Exception as exc:
            log.warning("Hivemind consensus unavailable: %s", exc)
            return {
                "success": False,
                "error": f"Hivemind server not reachable: {exc}",
                "mode": mode,
                "models_used": models,
                "fallback": (
                    "Start Hivemind on port 8490 or use"
                    " roundtable-dispatch instead"
                ),
            }

    def _resolve_models(self, models_str: str, mode: str) -> list[str]:
        """Resolve model list from user input or defaults."""
        if models_str:
            return [m.strip() for m in models_str.split(",") if m.strip()]

        # Default models per consensus mode
        defaults = {
            "majority": [
                "qwen2.5-coder:3b",
                "qwen2.5-coder:7b",
                "llama3.2",
            ],
            "unanimous": [
                "qwen2.5-coder:7b",
                "llama3.2",
                "mistral",
            ],
            "weighted": [
                "glm-5.1",  # architect
                "qwen2.5-coder:7b",  # dev
                "claude-opus-4.7",  # reviewer
            ],
            "deliberative": [
                "glm-5.1",
                "qwen2.5-coder:7b",
                "deepseek-v4-flash",
            ],
        }
        return defaults.get(mode, defaults["weighted"])

    async def _call_hivemind(self, payload: dict) -> dict:
        """Call Hivemind server's consensus endpoint."""
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{HIVEMIND_URL}/api/consensus",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))