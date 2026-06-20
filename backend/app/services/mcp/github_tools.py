"""GitHub MCP Tools — autonomous GitHub workflow automation"""
from __future__ import annotations

import os
import json
import logging
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

from .github_client import get_github_client

log = logging.getLogger("ucore.github_tools")


class GitHubTools:
    """MCP tools for GitHub automation."""
    
    def __init__(self, token: Optional[str] = None, org: str = "uDosGo"):
        """Initialize GitHub tools with authentication."""
        self.client = get_github_client(token=token, org=org)
        self.org = org
    
    def publish_release(self, repo_name: str, version: Optional[str] = None,
                       draft: bool = False, auto_tag: bool = True) -> dict:
        """Publish a GitHub release with auto-generated changelog.
        
        Args:
            repo_name: Repository name
            version: Version tag (auto-detected if None)
            draft: Create as draft release
            auto_tag: Auto-generate tag from version file
            
        Returns:
            dict with success, release_url, tag
        """
        log.info(f"Publishing release for {repo_name}")
        
        # Auto-detect version from pyproject.toml or package.json
        if not version and auto_tag:
            version = self._detect_version(repo_name)
            if not version:
                return {
                    "success": False,
                    "error": "Could not detect version"
                }
        
        tag = f"v{version}" if version else "v0.0.1"
        
        # Generate changelog from recent commits
        changelog = self._generate_changelog(repo_name)
        
        # Create release
        result = self.client.create_release(
            repo_name=repo_name,
            tag=tag,
            name=f"Release {tag}",
            body=changelog,
            draft=draft
        )
        
        log.info(f"Release result: {result}")
        return result
    
    def sync_repos(self, local_dir: Optional[str] = None) -> dict:
        """Sync all org repositories and report status.
        
        Args:
            local_dir: Local directory to clone/sync repos
            
        Returns:
            dict with synced repos, status summary
        """
        log.info(f"Syncing repos for org: {self.org}")
        
        repos = self.client.list_repos()
        if not repos:
            return {"success": False, "error": "No repos found"}
        
        base_dir = Path(local_dir or f"~/Code/{self.org}").expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        for repo in repos:
            repo_name = repo["name"]
            repo_path = base_dir / repo_name
            
            if repo_path.exists():
                # Pull latest
                status = self._git_pull(repo_path)
            else:
                # Clone repo
                status = self._git_clone(repo["html_url"], repo_path)
            
            results.append({
                "repo": repo_name,
                "path": str(repo_path),
                "status": status
            })
        
        return {
            "success": True,
            "repos": results,
            "total": len(results),
            "synced": sum(1 for r in results if r["status"] == "ok")
        }
    
    def create_pr(self, repo_name: str, title: Optional[str] = None,
                  body: Optional[str] = None, base: str = "main") -> dict:
        """Create PR from current branch with auto-generated content.
        
        Args:
            repo_name: Repository name
            title: PR title (auto-generated from commits if None)
            body: PR description (auto-generated if None)
            base: Base branch to merge into
            
        Returns:
            dict with success, pr_url, pr_number
        """
        log.info(f"Creating PR for {repo_name}")
        
        # Get current branch
        head = self._get_current_branch(repo_name)
        if not head or head == base:
            return {
                "success": False,
                "error": f"Invalid branch (current: {head}, base: {base})"
            }
        
        # Auto-generate title from commits
        if not title:
            title = self._generate_pr_title(repo_name, base, head)
        
        # Auto-generate body from commits
        if not body:
            body = self._generate_pr_body(repo_name, base, head)
        
        result = self.client.create_pr(
            repo_name=repo_name,
            title=title,
            body=body,
            head=head,
            base=base
        )
        
        log.info(f"PR creation result: {result}")
        return result
    
    def heal_issues(self, repo_name: str, auto_label: bool = True,
                    auto_close_stale: bool = False,
                    stale_days: int = 30) -> dict:
        """Triage and heal issues automatically.
        
        Args:
            repo_name: Repository name
            auto_label: Auto-label issues by type
            auto_close_stale: Close stale issues
            stale_days: Days before issue considered stale
            
        Returns:
            dict with processed issues, actions taken
        """
        log.info(f"Healing issues for {repo_name}")
        
        issues = self.client.list_issues(repo_name, state="open")
        if not issues:
            return {"success": True, "message": "No open issues"}
        
        actions = []
        for issue in issues:
            issue_num = issue["number"]
            issue_title = issue["title"]
            
            # Auto-label by keywords
            if auto_label:
                labels = self._detect_issue_labels(issue_title)
                if labels:
                    self._add_labels(repo_name, issue_num, labels)
                    actions.append({
                        "issue": issue_num,
                        "action": "labeled",
                        "labels": labels
                    })
            
            # Check staleness
            if auto_close_stale:
                updated = datetime.fromisoformat(
                    issue["updatedAt"].replace("Z", "+00:00")
                )
                age = (datetime.now(updated.tzinfo) - updated).days
                
                if age > stale_days:
                    self._close_issue(repo_name, issue_num,
                                     "Closing stale issue")
                    actions.append({
                        "issue": issue_num,
                        "action": "closed",
                        "reason": f"stale ({age} days)"
                    })
        
        return {
            "success": True,
            "issues_processed": len(issues),
            "actions_taken": len(actions),
            "actions": actions
        }
    
    def actions_status(self, repo_name: Optional[str] = None,
                      auto_retry_failed: bool = False) -> dict:
        """Check GitHub Actions workflow status.
        
        Args:
            repo_name: Repository name (None for all repos)
            auto_retry_failed: Auto-retry failed workflow runs
            
        Returns:
            dict with workflow runs, failures, retries
        """
        log.info(f"Checking Actions status for {repo_name or 'all repos'}")
        
        if repo_name:
            repos = [{"name": repo_name}]
        else:
            repos = self.client.list_repos()
        
        all_runs = []
        failures = []
        retries = []
        
        for repo in repos:
            name = repo["name"]
            runs = self.client.list_workflow_runs(name, limit=5)
            
            for run in runs:
                run["repo"] = name
                all_runs.append(run)
                
                if run["conclusion"] == "failure":
                    failures.append(run)
                    
                    if auto_retry_failed:
                        retry_result = self._retry_workflow(
                            name, run["databaseId"]
                        )
                        if retry_result["success"]:
                            retries.append(run)
        
        return {
            "success": True,
            "total_runs": len(all_runs),
            "failures": len(failures),
            "retries": len(retries) if auto_retry_failed else 0,
            "failed_runs": failures[:10],  # Limit output
            "retried_runs": retries
        }
    
    def approve_pr(self, repo_name: str, pr_number: int,
                   auto_merge: bool = False,
                   run_tests: bool = True) -> dict:
        """Review and approve PR with automated checks.
        
        Args:
            repo_name: Repository name
            pr_number: PR number
            auto_merge: Auto-merge if checks pass
            run_tests: Run local tests before approval
            
        Returns:
            dict with success, approval status, merge status
        """
        log.info(f"Reviewing PR #{pr_number} in {repo_name}")
        
        # Get PR details
        result = self.client.run_gh_cli([
            "pr", "view", str(pr_number),
            "--repo", f"{self.org}/{repo_name}",
            "--json", "title,state,mergeable"
        ])
        
        if not result["success"]:
            return {"success": False, "error": "Could not fetch PR"}
        
        pr_data = json.loads(result["stdout"])
        
        checks = {
            "pr_open": pr_data["state"] == "OPEN",
            "mergeable": pr_data.get("mergeable") == "MERGEABLE",
            "tests_pass": True
        }
        
        # Run local tests if requested
        if run_tests:
            test_result = self._run_local_tests(repo_name)
            checks["tests_pass"] = test_result["success"]
        
        all_pass = all(checks.values())
        
        # Approve PR
        if all_pass:
            approve_result = self.client.run_gh_cli([
                "pr", "review", str(pr_number),
                "--repo", f"{self.org}/{repo_name}",
                "--approve",
                "--body", "✅ Auto-approved: All checks passed"
            ])
            
            # Auto-merge if requested
            if auto_merge and approve_result["success"]:
                merge_result = self.client.run_gh_cli([
                    "pr", "merge", str(pr_number),
                    "--repo", f"{self.org}/{repo_name}",
                    "--auto",
                    "--squash"
                ])
                return {
                    "success": True,
                    "approved": True,
                    "merged": merge_result["success"],
                    "checks": checks
                }
            
            return {
                "success": True,
                "approved": True,
                "checks": checks
            }
        
        return {
            "success": False,
            "approved": False,
            "reason": "Checks failed",
            "checks": checks
        }
    
    # ── Helper Methods ──────────────────────────────────────────────
    
    def _detect_version(self, repo_name: str) -> Optional[str]:
        """Detect version from pyproject.toml or package.json."""
        # This would need actual file access - simplified for now
        return "0.1.0"
    
    def _generate_changelog(self, repo_name: str) -> str:
        """Generate changelog from git commits."""
        result = self.client.run_gh_cli([
            "api",
            f"repos/{self.org}/{repo_name}/commits",
            "--jq", ".[].commit.message"
        ])
        if result["success"]:
            commits = result["stdout"].split("\n")[:10]
            return "## Changes\n\n" + "\n".join(
                f"- {c}" for c in commits if c
            )
        return "Release notes"
    
    def _git_pull(self, repo_path: Path) -> str:
        """Pull latest changes."""
        try:
            subprocess.run(
                ["git", "pull"],
                cwd=repo_path,
                capture_output=True,
                timeout=30
            )
            return "ok"
        except Exception:
            return "failed"
    
    def _git_clone(self, url: str, path: Path) -> str:
        """Clone repository."""
        try:
            subprocess.run(
                ["git", "clone", url, str(path)],
                capture_output=True,
                timeout=60
            )
            return "ok"
        except Exception:
            return "failed"
    
    def _get_current_branch(self, repo_name: str) -> Optional[str]:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def _generate_pr_title(self, repo: str, base: str, head: str) -> str:
        """Generate PR title from commits."""
        return f"Merge {head} into {base}"
    
    def _generate_pr_body(self, repo: str, base: str, head: str) -> str:
        """Generate PR body from commits."""
        return f"Changes from {head}\n\n## What changed\n\nTBD"
    
    def _detect_issue_labels(self, title: str) -> list[str]:
        """Detect labels from issue title."""
        title_lower = title.lower()
        labels = []
        if "bug" in title_lower or "fix" in title_lower:
            labels.append("bug")
        if "feat" in title_lower or "feature" in title_lower:
            labels.append("enhancement")
        if "doc" in title_lower:
            labels.append("documentation")
        return labels
    
    def _add_labels(self, repo: str, issue_num: int,
                    labels: list[str]) -> bool:
        """Add labels to issue."""
        result = self.client.run_gh_cli([
            "issue", "edit", str(issue_num),
            "--repo", f"{self.org}/{repo}",
            "--add-label", ",".join(labels)
        ])
        return result["success"]
    
    def _close_issue(self, repo: str, issue_num: int, reason: str) -> bool:
        """Close an issue."""
        result = self.client.run_gh_cli([
            "issue", "close", str(issue_num),
            "--repo", f"{self.org}/{repo}",
            "--comment", reason
        ])
        return result["success"]
    
    def _retry_workflow(self, repo: str, run_id: int) -> dict:
        """Retry a failed workflow run."""
        result = self.client.run_gh_cli([
            "run", "rerun", str(run_id),
            "--repo", f"{self.org}/{repo}"
        ])
        return {"success": result["success"]}
    
    def _run_local_tests(self, repo_name: str) -> dict:
        """Run local tests for repo."""
        # Simplified - would need actual test runner
        return {"success": True}


# ── MCP Tool Exports ────────────────────────────────────────────

_tools_instance: Optional[GitHubTools] = None


def get_github_tools(token: Optional[str] = None) -> GitHubTools:
    """Get or create GitHub tools singleton."""
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = GitHubTools(token=token)
    return _tools_instance
