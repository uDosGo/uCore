"""Hivemind MCP Server — Multi-agent orchestration server.

Runs as a standalone aiohttp server on port 8490, exposing:
  - Agent management (list, describe, route)
  - Consensus engine (propose, vote, resolve)
  - LLM routing (chat completion via Roundtable/Ollama/OpenAI)
  - Workflow execution (run multi-step agent workflows)

Usage:
    python -m app.mcp.hivemind_server --port 8490
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from aiohttp import web

from app.mcp.consensus import ConsensusEngine, Vote
from app.mcp.llm_router import LLMRouter
from app.mcp.roundtable_integration import get_roundtable
from app.secret.store import get_store
from app.services.agent_specialization import SpecializedAgentRegistry
from app.services.cost_manager import get_cost_manager

log = logging.getLogger("ucore.mcp.hivemind")


# ─── Hivemind Server ───────────────────────────────────────


class HivemindServer:
    """Hivemind MCP server — multi-agent orchestration."""

    def __init__(
        self,
        agents_config: str | None = None,
        llm_config: str | None = None,
    ):
        # Use the canonical SpecializedAgentRegistry from agent_specialization.py
        self.registry = SpecializedAgentRegistry(agents_config)
        self.consensus = ConsensusEngine()
        # Wire LLM router to use Secret Store for API keys
        self.llm_router = LLMRouter(llm_config)
        self._store = get_store()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Set up HTTP routes."""
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/api/hivemind/agents", self.handle_list_agents)
        self.app.router.add_get(
            "/api/hivemind/agents/{agent_id}", self.handle_get_agent
        )
        self.app.router.add_post(
            "/api/hivemind/route", self.handle_route_task
        )
        self.app.router.add_get(
            "/api/hivemind/workflows", self.handle_list_workflows
        )
        self.app.router.add_get(
            "/api/hivemind/workflows/{workflow_id}", self.handle_get_workflow
        )
        self.app.router.add_post(
            "/api/hivemind/consensus/propose", self.handle_propose
        )
        self.app.router.add_post(
            "/api/hivemind/consensus/vote", self.handle_vote
        )
        self.app.router.add_get(
            "/api/hivemind/consensus/{proposal_id}", self.handle_proposal_status
        )
        self.app.router.add_get(
            "/api/hivemind/consensus", self.handle_list_proposals
        )
        self.app.router.add_post(
            "/api/hivemind/chat", self.handle_chat
        )
        self.app.router.add_get(
            "/api/hivemind/llm/health", self.handle_llm_health
        )
        self.app.router.add_post(
            "/api/hivemind/workflow/run", self.handle_run_workflow
        )
        self.app.router.add_get(
            "/api/hivemind/roundtable", self.handle_roundtable_status
        )
        self.app.router.add_get(
            "/api/hivemind/llm/cost", self.handle_cost_status
        )

    async def handle_health(self, request: web.Request) -> web.Response:
        """GET /health — Health check."""
        rt = get_roundtable()
        cm = get_cost_manager()
        return web.json_response({
            "status": "ok",
            "service": "hivemind",
            "version": "1.0.0",
            "agents": len(self.registry.agents),
            "active_proposals": len(self.consensus.list_active()),
            "roundtable": rt.summary(),
            "cost": cm.summary(),
        })

    async def handle_cost_status(
        self, request: web.Request
    ) -> web.Response:
        """GET /api/hivemind/llm/cost — Cost management status."""
        cm = get_cost_manager()
        return web.json_response(cm.summary())

    async def handle_list_agents(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/agents — List all agents."""
        agents = self.registry.list_agents()
        return web.json_response({
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "model": a.model,
                    "provider": a.provider,
                    "capabilities": a.capabilities,
                    "cost_per_task": a.cost_per_task,
                    "timeout": a.timeout,
                    "priority": a.priority,
                }
                for a in agents
            ],
        })

    async def handle_get_agent(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/agents/{agent_id} — Get agent details."""
        agent_id = request.match_info["agent_id"]
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return web.json_response(
                {"error": f"Agent '{agent_id}' not found"},
                status=404,
            )
        return web.json_response({
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "model": agent.model,
                "provider": agent.provider,
                "capabilities": agent.capabilities,
                "cost_per_task": agent.cost_per_task,
                "timeout": agent.timeout,
                "priority": agent.priority,
            }
        })

    async def handle_route_task(self, request: web.Request) -> web.Response:
        """POST /api/hivemind/route — Route a task to the best agent."""
        body = await request.json()
        task_type = body.get("task_type", "")
        complexity = body.get("complexity", "medium")
        try:
            agent = self.registry.get_best_agent_for_task(task_type, complexity)
        except RuntimeError:
            return web.json_response(
                {"error": f"No agent found for task type '{task_type}'"},
                status=404,
            )
        return web.json_response({
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "model": agent.model,
                "provider": agent.provider,
                "capabilities": agent.capabilities,
                "timeout": agent.timeout,
            }
        })

    async def handle_list_workflows(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/workflows — List all workflows."""
        workflows = []
        for wid, wt in self.registry.workflow_templates.items():
            workflows.append({
                "id": wid,
                "name": wt.name,
                "description": wt.description,
                "stages": [
                    {"role": s.role, "title": s.title}
                    for s in wt.stages
                ],
            })
        return web.json_response({"workflows": workflows})

    async def handle_get_workflow(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/workflows/{workflow_id} — Get workflow details."""
        workflow_id = request.match_info["workflow_id"]
        wt = self.registry.workflow_templates.get(workflow_id)
        if not wt:
            return web.json_response(
                {"error": f"Workflow '{workflow_id}' not found"},
                status=404,
            )
        return web.json_response({
            "workflow": {
                "id": wt.id,
                "name": wt.name,
                "description": wt.description,
                "task_types": wt.task_types,
                "stages": [
                    {"role": s.role, "title": s.title, "description": s.description}
                    for s in wt.stages
                ],
            }
        })

    async def handle_propose(self, request: web.Request) -> web.Response:
        """POST /api/hivemind/consensus/propose — Create a new proposal."""
        body = await request.json()
        agent_id = body.get("agent_id", "")
        title = body.get("title", "")
        description = body.get("description", "")
        actions = body.get("actions", [])

        if not agent_id or not title:
            return web.json_response(
                {"error": "agent_id and title are required"},
                status=400,
            )

        proposal = self.consensus.create_proposal(
            agent_id=agent_id,
            title=title,
            description=description,
            actions=actions,
        )
        return web.json_response({
            "proposal": {
                "id": proposal.id,
                "agent_id": proposal.agent_id,
                "title": proposal.title,
                "round": proposal.round,
            }
        })

    async def handle_vote(self, request: web.Request) -> web.Response:
        """POST /api/hivemind/consensus/vote — Cast a vote on a proposal."""
        body = await request.json()
        proposal_id = body.get("proposal_id", "")
        agent_id = body.get("agent_id", "")
        vote_str = body.get("vote", "")
        reasoning = body.get("reasoning", "")
        weight = body.get("weight", 1.0)

        if not proposal_id or not agent_id or not vote_str:
            return web.json_response(
                {"error": "proposal_id, agent_id, and vote are required"},
                status=400,
            )

        try:
            vote = Vote(vote_str)
        except ValueError:
            return web.json_response(
                {"error": f"Invalid vote '{vote_str}'. Use: approve, reject, abstain"},
                status=400,
            )

        result = self.consensus.cast_vote(
            proposal_id=proposal_id,
            agent_id=agent_id,
            vote=vote,
            reasoning=reasoning,
            weight=float(weight),
        )
        return web.json_response(result)

    async def handle_proposal_status(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/consensus/{proposal_id} — Get proposal status."""
        proposal_id = request.match_info["proposal_id"]
        status = self.consensus.get_status(proposal_id)
        if not status:
            return web.json_response(
                {"error": f"Proposal '{proposal_id}' not found"},
                status=404,
            )
        return web.json_response(status)

    async def handle_list_proposals(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/consensus — List all active proposals."""
        return web.json_response({
            "active_proposals": self.consensus.list_active(),
            "mode": self.consensus.mode.value,
        })

    async def handle_chat(self, request: web.Request) -> web.Response:
        """POST /api/hivemind/chat — Send a chat completion request."""
        body = await request.json()
        model = body.get("model", "")
        messages = body.get("messages", [])
        system_prompt = body.get("system_prompt")
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("max_tokens", 4096)

        if not model or not messages:
            return web.json_response(
                {"error": "model and messages are required"},
                status=400,
            )

        result = await self.llm_router.chat_completion(
            model=model,
            messages=messages,
            system_prompt=system_prompt,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
        return web.json_response(result)

    async def handle_roundtable_status(
        self, request: web.Request
    ) -> web.Response:
        """GET /api/hivemind/roundtable — Roundtable AI status."""
        rt = get_roundtable()
        return web.json_response(rt.summary())

    async def handle_llm_health(self, request: web.Request) -> web.Response:
        """GET /api/hivemind/llm/health — Check LLM backend health."""
        results = await self.llm_router.health_check()
        return web.json_response({"backends": results})

    async def handle_run_workflow(self, request: web.Request) -> web.Response:
        """POST /api/hivemind/workflow/run — Execute a multi-step workflow."""
        body = await request.json()
        workflow_id = body.get("workflow_id", "")
        context = body.get("context", {})

        wt = self.registry.workflow_templates.get(workflow_id)
        if not wt:
            return web.json_response(
                {"error": f"Workflow '{workflow_id}' not found"},
                status=404,
            )

        # Use LangGraph for agent orchestration if available
        try:
            return await self._run_workflow_langgraph(wt, context, workflow_id)
        except ImportError:
            log.info("LangGraph not available — using native execution")
            return await self._run_workflow_native(wt, context, workflow_id)

    async def _run_workflow_langgraph(self, wt, context, workflow_id):
        """Execute workflow using LangGraph StateGraph."""
        from typing import Annotated, TypedDict

        from langgraph.graph import END, StateGraph
        from langgraph.graph.message import add_messages

        class WorkflowState(TypedDict):
            messages: Annotated[list, add_messages]
            stage_results: list[dict]

        builder = StateGraph(WorkflowState)

        for i, stage in enumerate(wt.stages):
            agent = self.registry.get_agent(stage.role)

            stage_role = stage.role

            def make_node(agent_obj, stage_desc, stage_title, stage_role_val, ctx):
                async def node_fn(state: WorkflowState) -> dict:
                    from litellm import acompletion
                    msgs = [{"role": "user", "content": stage_desc}]
                    if ctx.get("input"):
                        msgs.append({
                            "role": "user",
                            "content": f"Context: {json.dumps(ctx['input'])}",
                        })
                    try:
                        resp = await acompletion(
                            model=agent_obj.model if agent_obj else "ollama/qwen2.5-coder:3b",
                            messages=msgs,
                        )
                        content = resp.choices[0].message.content
                        return {
                            "messages": [{"role": "assistant", "content": content}],
                            "stage_results": [{
                                "stage": stage_title,
                                "role": stage_role_val,
                                "agent": agent_obj.name if agent_obj else "default",
                                "result": content,
                            }],
                        }
                    except Exception as exc:
                        return {
                            "messages": [],
                            "stage_results": [{
                                "stage": stage_title,
                                "role": stage_role_val,
                                "error": str(exc),
                            }],
                        }
                return node_fn

            node_fn = make_node(agent, stage.description, stage.title, stage_role, context)
            node_name = f"stage_{i}"
            builder.add_node(node_name, node_fn)
            if i == 0:
                builder.set_entry_point(node_name)
            else:
                builder.add_edge(f"stage_{i-1}", node_name)

        builder.add_edge(f"stage_{len(wt.stages) - 1}", END)
        graph = builder.compile()
        result = await graph.ainvoke({"messages": [], "stage_results": []})

        return web.json_response({
            "workflow_id": workflow_id,
            "engine": "langgraph",
            "stages_completed": len(result.get("stage_results", [])),
            "results": result.get("stage_results", []),
        })

    async def _run_workflow_native(self, wt, context, workflow_id):
        """Fallback native workflow execution."""
        from app.services.provider_router import get_router
        router = get_router()
        results = []
        for stage in wt.stages:
            agent = self.registry.get_agent(stage.role)
            if not agent:
                results.append({
                    "stage": stage.title,
                    "role": stage.role,
                    "error": f"No agent found for role '{stage.role}'",
                })
                continue
            messages = [{"role": "user", "content": stage.description}]
            if context.get("input"):
                messages.append({
                    "role": "user",
                    "content": f"Context: {json.dumps(context['input'])}",
                })
            llm_result = await router.chat(
                messages=messages,
                model=agent.model,
            )
            results.append({
                "stage": stage.title,
                "role": stage.role,
                "agent": agent.name,
                "result": llm_result.get("content", ""),
            })
        return web.json_response({
            "workflow_id": workflow_id,
            "engine": "native",
            "stages_completed": len(results),
            "results": results,
        })


# ─── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hivemind MCP Server — Multi-agent orchestration"
    )
    parser.add_argument(
        "--port", type=int, default=8490,
        help="Port to listen on (default: 8490)",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--agents-config", type=str, default=None,
        help="Path to agents.yaml config file",
    )
    parser.add_argument(
        "--llm-config", type=str, default=None,
        help="Path to LLM router config file",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    # Resolve default config paths
    agents_config = args.agents_config
    if not agents_config:
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "agents.yaml",
        )
        if os.path.exists(default_path):
            agents_config = default_path

    log.info("╔══════════════════════════════════════════╗")
    log.info("║     Hivemind MCP Server v1.0.0          ║")
    log.info("╚══════════════════════════════════════════╝")
    log.info("Host: %s:%d", args.host, args.port)
    log.info("Agents config: %s", agents_config or "(defaults)")
    log.info("Debug: %s", args.debug)

    server = HivemindServer(
        agents_config=agents_config,
        llm_config=args.llm_config,
    )

    web.run_app(server.app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
