"""GitHub API Client — wrapper for GitHub operations"""
from __future__ import annotations

import os
import logging
from typing import Optional, Any
from pathlib import Path
import subprocess
import json

try:
    from github import Github, GithubException
    HAS_PYGITHUB = True
except ImportError:
    HAS_PYGITHUB = False

log = logging.getLogger("ucore.github")


class GitHubClient:
    """GitHub API client for uCore MCP tools."""
    
    def __init__(self, token: Optional[str] = None, org: str = "uDosGo"):
        """Initialize GitHub client.
        
        Args:
            token: GitHub Personal Access Token (defaults to env GITHUB_TOKEN)
            org: GitHub organization name
        """
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.org = org
        self._gh = None
        self._org_obj = None
        
        if HAS_PYGITHUB and self.token:
            try:
                self._gh = Github(self.token)
                self._org_obj = self._gh.get_organization(self.org)
                log.info(f"GitHub client initialized for org: {self.org}")
            except GithubException as e:
                log.error(f"Failed to initialize GitHub client: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if GitHub authentication is valid."""
        if not self._gh:
            return False
        try:
            self._gh.get_user().login
            return True
        except Exception:
            return False
    
    def run_gh_cli(self, args: list[str]) -> dict:
        """Execute GitHub CLI command.
        
        Args:
            args: Command arguments (e.g., ['repo', 'list'])
            
        Returns:
            dict with success, stdout, stderr
        """
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "GITHUB_TOKEN": self.token}
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_repos(self) -> list[dict]:
        """List all repositories in the organization."""
        if self._org_obj:
            try:
                repos = []
                for repo in self._org_obj.get_repos():
                    repos.append({
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "private": repo.private,
                        "default_branch": repo.default_branch,
                        "html_url": repo.html_url,
                    })
                return repos
            except Exception as e:
                log.error(f"Failed to list repos: {e}")
        
        # Fallback to gh CLI
        result = self.run_gh_cli(["repo", "list", self.org, "--json", "name,url"])
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return []
        return []
    
    def get_repo(self, repo_name: str):
        """Get repository object."""
        if self._org_obj:
            try:
                return self._org_obj.get_repo(repo_name)
            except Exception as e:
                log.error(f"Failed to get repo {repo_name}: {e}")
        return None
    
    def create_release(self, repo_name: str, tag: str, name: str, 
                       body: str, draft: bool = False) -> dict:
        """Create a GitHub release.
        
        Args:
            repo_name: Repository name
            tag: Git tag for release
            name: Release title
            body: Release description/changelog
            draft: Whether to create as draft
            
        Returns:
            dict with success, release_url
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                release = repo.create_git_release(
                    tag=tag,
                    name=name,
                    message=body,
                    draft=draft
                )
                return {
                    "success": True,
                    "release_url": release.html_url,
                    "tag": tag
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Fallback to gh CLI
        args = [
            "release", "create", tag,
            "--repo", f"{self.org}/{repo_name}",
            "--title", name,
            "--notes", body
        ]
        if draft:
            args.append("--draft")
        
        result = self.run_gh_cli(args)
        if result["success"]:
            return {
                "success": True,
                "tag": tag,
                "output": result["stdout"]
            }
        return {"success": False, "error": result.get("stderr", "Unknown error")}
    
    def create_pr(self, repo_name: str, title: str, body: str, 
                  head: str, base: str = "main") -> dict:
        """Create a pull request.
        
        Args:
            repo_name: Repository name
            title: PR title
            body: PR description
            head: Branch to merge from
            base: Branch to merge into
            
        Returns:
            dict with success, pr_url, pr_number
        """
        repo = self.get_repo(repo_name)
        if repo:
            try:
                pr = repo.create_pull(
                    title=title,
                    body=body,
                    head=head,
                    base=base
                )
                return {
                    "success": True,
                    "pr_url": pr.html_url,
                    "pr_number": pr.number
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Fallback to gh CLI
        result = self.run_gh_cli([
            "pr", "create",
            "--repo", f"{self.org}/{repo_name}",
            "--title", title,
            "--body", body,
            "--head", head,
            "--base", base
        ])
        
        if result["success"]:
            return {
                "success": True,
                "output": result["stdout"]
            }
        return {"success": False, "error": result.get("stderr", "Unknown error")}
    
    def list_workflow_runs(self, repo_name: str, limit: int = 10) -> list[dict]:
        """List recent workflow runs."""
        result = self.run_gh_cli([
            "run", "list",
            "--repo", f"{self.org}/{repo_name}",
            "--limit", str(limit),
            "--json", "databaseId,status,conclusion,name,headBranch,createdAt"
        ])
        
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return []
        return []
    
    def list_issues(self, repo_name: str, state: str = "open", 
                    labels: Optional[list[str]] = None) -> list[dict]:
        """List issues in repository."""
        args = [
            "issue", "list",
            "--repo", f"{self.org}/{repo_name}",
            "--state", state,
            "--json", "number,title,labels,createdAt,updatedAt,author"
        ]
        
        if labels:
            for label in labels:
                args.extend(["--label", label])
        
        result = self.run_gh_cli(args)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return []
        return []


def get_github_client(token: Optional[str] = None, org: str = "uDosGo") -> GitHubClient:
    """Get or create singleton GitHub client."""
    return GitHubClient(token=token, org=org)
