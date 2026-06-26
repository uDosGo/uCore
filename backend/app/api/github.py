"""GitHub API — web endpoints for GitHub automation"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

from aiohttp import web

from ..services.mcp.github_tools import get_github_tools

log = logging.getLogger("ucore.api.github")

# GitHub webhook secret (set via env var)
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def register_github_routes(app: web.Application) -> None:
    """Register GitHub API routes."""
    app.router.add_get("/api/github/status", github_status_handler)
    app.router.add_post("/api/github/webhook", github_webhook_handler)
    app.router.add_post("/api/github/trigger/{tool}", github_trigger_handler)
    app.router.add_get("/api/github/repos", github_repos_handler)
    log.info("GitHub API routes registered")


async def github_status_handler(request: web.Request) -> web.Response:
    """Get GitHub organization status dashboard.
    
    GET /api/github/status
    
    Returns summary of repos, workflows, issues across org.
    """
    try:
        token = request.query.get("token") or os.getenv("GITHUB_TOKEN")
        tools = get_github_tools(token=token)

        # Get repos
        repos = tools.client.list_repos()

        # Get CI status for all repos
        ci_status = tools.actions_status()

        # Count issues across repos
        total_issues = 0
        for repo in repos:
            issues = tools.client.list_issues(repo["name"])
            total_issues += len(issues)

        return web.json_response({
            "success": True,
            "org": tools.org,
            "repos": {
                "total": len(repos),
                "list": repos[:10],  # Limit response size
            },
            "ci": {
                "total_runs": ci_status.get("total_runs", 0),
                "failures": ci_status.get("failures", 0),
                "failed_runs": ci_status.get("failed_runs", []),
            },
            "issues": {
                "total_open": total_issues,
            },
        })
    except Exception as e:
        log.error(f"GitHub status error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e),
        }, status=500)


async def github_webhook_handler(request: web.Request) -> web.Response:
    """Handle GitHub webhook events.
    
    POST /api/github/webhook
    
    Processes GitHub webhooks for automation triggers.
    """
    try:
        # Verify webhook signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        body = await request.read()

        if WEBHOOK_SECRET and not verify_webhook_signature(
            body, signature, WEBHOOK_SECRET,
        ):
            return web.json_response({
                "success": False,
                "error": "Invalid signature",
            }, status=401)

        # Parse event
        event_type = request.headers.get("X-GitHub-Event", "")
        payload = json.loads(body)

        log.info(f"Received GitHub webhook: {event_type}")

        token = os.getenv("GITHUB_TOKEN")
        tools = get_github_tools(token=token)

        result = {"success": True, "event": event_type}

        # Handle different event types
        if event_type == "push":
            # On push to main, check CI status
            if payload.get("ref") == "refs/heads/main":
                repo_name = payload["repository"]["name"]
                ci_result = tools.actions_status(
                    repo_name=repo_name,
                    auto_retry_failed=True,
                )
                result["ci_check"] = ci_result

        elif event_type == "pull_request":
            # On PR opened, could auto-label or check
            action = payload.get("action")
            if action == "opened":
                pr_number = payload["pull_request"]["number"]
                repo_name = payload["repository"]["name"]
                result["action"] = f"PR #{pr_number} opened"

        elif event_type == "issues":
            # On issue opened, auto-triage
            action = payload.get("action")
            if action == "opened":
                repo_name = payload["repository"]["name"]
                heal_result = tools.heal_issues(
                    repo_name=repo_name,
                    auto_label=True,
                )
                result["triage"] = heal_result

        elif event_type == "workflow_run":
            # On workflow completion, check for failures
            conclusion = payload.get("workflow_run", {}).get("conclusion")
            if conclusion == "failure":
                repo_name = payload["repository"]["name"]
                run_id = payload["workflow_run"]["id"]
                result["workflow_failed"] = {
                    "repo": repo_name,
                    "run_id": run_id,
                }

        return web.json_response(result)

    except Exception as e:
        log.error(f"Webhook error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e),
        }, status=500)


async def github_trigger_handler(request: web.Request) -> web.Response:
    """Manually trigger a GitHub tool.
    
    POST /api/github/trigger/{tool}
    
    Body: tool-specific parameters
    """
    try:
        tool_name = request.match_info["tool"]
        params = await request.json() if request.body_exists else {}

        token = params.get("token") or os.getenv("GITHUB_TOKEN")
        tools = get_github_tools(token=token)

        # Route to appropriate tool
        if tool_name == "publish_release":
            result = tools.publish_release(
                repo_name=params.get("repo_name"),
                version=params.get("version"),
                draft=params.get("draft", False),
            )

        elif tool_name == "sync_repos":
            result = tools.sync_repos(
                local_dir=params.get("local_dir"),
            )

        elif tool_name == "create_pr":
            result = tools.create_pr(
                repo_name=params.get("repo_name"),
                title=params.get("title"),
                body=params.get("body"),
                base=params.get("base", "main"),
            )

        elif tool_name == "heal_issues":
            result = tools.heal_issues(
                repo_name=params.get("repo_name"),
                auto_label=params.get("auto_label", True),
                auto_close_stale=params.get("auto_close_stale", False),
            )

        elif tool_name == "actions_status":
            result = tools.actions_status(
                repo_name=params.get("repo_name"),
                auto_retry_failed=params.get("auto_retry_failed", False),
            )

        elif tool_name == "approve_pr":
            result = tools.approve_pr(
                repo_name=params.get("repo_name"),
                pr_number=params.get("pr_number"),
                auto_merge=params.get("auto_merge", False),
            )

        else:
            return web.json_response({
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }, status=400)

        return web.json_response(result)

    except Exception as e:
        log.error(f"Tool trigger error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e),
        }, status=500)


async def github_repos_handler(request: web.Request) -> web.Response:
    """List all org repositories.
    
    GET /api/github/repos
    """
    try:
        token = request.query.get("token") or os.getenv("GITHUB_TOKEN")
        tools = get_github_tools(token=token)

        repos = tools.client.list_repos()

        return web.json_response({
            "success": True,
            "count": len(repos),
            "repos": repos,
        })
    except Exception as e:
        log.error(f"List repos error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e),
        }, status=500)


def verify_webhook_signature(payload: bytes, signature: str,
                             secret: str) -> bool:
    """Verify GitHub webhook signature.
    
    Args:
        payload: Request body bytes
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret
        
    Returns:
        True if signature is valid

    """
    if not signature.startswith("sha256="):
        return False

    expected_sig = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received_sig = signature[7:]  # Remove "sha256=" prefix

    return hmac.compare_digest(expected_sig, received_sig)
