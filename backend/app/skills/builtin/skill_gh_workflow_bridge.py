"""GitHub Workflow Bridge Skill — bridge tasks to GitHub Actions/CLI.

Bridges uCore tasks to GitHub Actions and CLI workflows:
  - trigger-ci: trigger a GitHub Actions workflow run
  - create-pr: create a pull request
  - run-workflow: execute a specific workflow by name
  - status: check CI status for a repo

Integrates with: gh CLI, GitHub API, tasker.
"""
from __future__ import annotations

import asyncio
import logging
import subprocess

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.gh_workflow_bridge")


def _find_gh_binary() -> str | None:
    """Locate the gh CLI binary."""
    try:
        result = subprocess.run(
            ["which", "gh"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _is_gh_authenticated() -> bool:
    """Check if gh is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


class GHWorkflowBridgeSkill(BaseSkill):
    """Bridge uCore tasks to GitHub Actions and CLI workflows."""

    meta = SkillMeta(
        id="gh-workflow-bridge",
        name="GitHub Workflow Bridge",
        description=(
            "Bridge tasks to GitHub Actions/CLI."
            " Trigger CI, create PRs, run workflows."
        ),
        category="developer",
        timeout=180,
        params=[
            SkillParam(
                name="action",
                type="string",
                required=True,
                description=(
                    "GitHub action: 'trigger-ci', 'create-pr',"
                    " 'run-workflow', or 'status'"
                ),
            ),
            SkillParam(
                name="repo",
                type="string",
                required=False,
                default="",
                description=(
                    "GitHub repo in owner/repo format"
                    " (default: uDosGo/uCore)"
                ),
            ),
            SkillParam(
                name="workflow",
                type="string",
                required=False,
                default="",
                description="Workflow name or ID (for run-workflow)",
            ),
            SkillParam(
                name="branch",
                type="string",
                required=False,
                default="main",
                description="Branch name (for create-pr)",
            ),
            SkillParam(
                name="title",
                type="string",
                required=False,
                default="",
                description="PR title (for create-pr)",
            ),
            SkillParam(
                name="body",
                type="string",
                required=False,
                default="",
                description="PR description body (for create-pr)",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        action = kwargs.get("action", "").strip()
        repo = kwargs.get("repo", "uDosGo/uCore").strip()
        workflow = kwargs.get("workflow", "").strip()
        branch = kwargs.get("branch", "main").strip()
        title = kwargs.get("title", "").strip()
        body = kwargs.get("body", "").strip()

        if not action:
            return {"success": False, "error": "action is required"}

        # Check gh CLI availability
        gh_bin = _find_gh_binary()
        if not gh_bin:
            return {
                "success": False,
                "error": (
                    "GitHub CLI (gh) not found."
                    " Install: brew install gh && gh auth login"
                ),
            }

        if not _is_gh_authenticated():
            return {
                "success": False,
                "error": "gh not authenticated. Run: gh auth login",
            }

        actions = {
            "trigger-ci": self._trigger_ci,
            "create-pr": self._create_pr,
            "run-workflow": self._run_workflow,
            "status": self._check_status,
        }

        handler = actions.get(action)
        if not handler:
            return {
                "success": False,
                "error": (
                    f"Unknown action: {action}."
                    " Use: trigger-ci, create-pr, run-workflow, status"
                ),
            }

        result = await handler(repo, workflow, branch, title, body)
        return {
            "success": True,
            "action": action,
            "repo": repo,
            **result,
        }

    async def _trigger_ci(
        self, repo: str, workflow: str, branch: str,
        title: str, body: str,
    ) -> dict:
        """Trigger a CI workflow run."""
        wf_ref = workflow or "ci"
        try:
            proc = await asyncio.create_subprocess_exec(
                "gh", "workflow", "run", wf_ref,
                "--repo", repo,
                "--ref", branch,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30,
            )
            output = stdout.decode().strip() if stdout else ""
            err = stderr.decode().strip() if stderr else ""

            if proc.returncode != 0:
                return {
                    "triggered": False,
                    "error": err or "Unknown error",
                    "workflow": wf_ref,
                }

            # Extract run ID from output
            run_id = ""
            for line in output.splitlines():
                if "run" in line.lower() and any(c.isdigit() for c in line):
                    import re
                    digits = re.findall(r'\d+', line)
                    if digits:
                        run_id = digits[0]
                        break

            return {
                "triggered": True,
                "workflow": wf_ref,
                "run_id": run_id,
                "output": output,
            }
        except asyncio.TimeoutError:
            return {"triggered": False, "error": "Timeout after 30s"}
        except Exception as exc:
            return {"triggered": False, "error": str(exc)}

    async def _create_pr(
        self, repo: str, workflow: str, branch: str,
        title: str, body: str,
    ) -> dict:
        """Create a pull request."""
        if not title:
            return {"error": "PR title is required"}

        cmd = [
            "gh", "pr", "create",
            "--repo", repo,
            "--base", branch,
            "--title", title,
        ]
        if body:
            cmd.extend(["--body", body])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30,
            )
            output = stdout.decode().strip() if stdout else ""
            err = stderr.decode().strip() if stderr else ""

            if proc.returncode != 0:
                return {
                    "created": False,
                    "error": err or "Unknown error",
                }

            # Extract PR URL
            pr_url = ""
            for line in output.splitlines():
                if "http" in line and "pull" in line:
                    pr_url = line.strip()
                    break

            return {
                "created": proc.returncode == 0,
                "pr_url": pr_url,
                "output": output,
            }
        except asyncio.TimeoutError:
            return {"created": False, "error": "Timeout after 30s"}
        except Exception as exc:
            return {"created": False, "error": str(exc)}

    async def _run_workflow(
        self, repo: str, workflow: str, branch: str,
        title: str, body: str,
    ) -> dict:
        """Run a specific workflow."""
        if not workflow:
            return {"error": "workflow name or ID is required"}
        return await self._trigger_ci(
            repo, workflow, branch, title, body,
        )

    async def _check_status(
        self, repo: str, workflow: str, branch: str,
        title: str, body: str,
    ) -> dict:
        """Check CI status for a repo."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "gh", "run", "list",
                "--repo", repo,
                "--limit", "5",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=15,
            )
            output = stdout.decode().strip() if stdout else ""
            err = stderr.decode().strip() if stderr else ""

            if proc.returncode != 0:
                return {"status": "error", "error": err or "Unknown error"}

            # Parse runs
            runs = []
            for line in output.splitlines():
                if line.strip():
                    runs.append(line.strip())

            # Determine overall status
            status = "healthy"
            for line in runs:
                if "fail" in line.lower():
                    status = "failing"
                    break

            return {
                "status": status,
                "recent_runs": runs,
            }
        except asyncio.TimeoutError:
            return {"status": "unknown", "error": "Timeout after 15s"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}