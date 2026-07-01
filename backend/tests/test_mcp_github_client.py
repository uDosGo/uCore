"""Unit tests for the GitHub API client — No network calls required."""
from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from app.services.mcp.github_client import GitHubClient


@pytest.fixture
def client(monkeypatch):
    """GitHubClient with no token (no network calls)."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return GitHubClient(token="", org="test-org")


def test_init_no_token(client):
    """Client initializes without error even without a token."""
    assert client.token == ""
    assert client.org == "test-org"
    assert client._gh is None


def test_is_authenticated_no_token(client):
    """Without token, auth check returns False."""
    assert client.is_authenticated() is False


def test_list_repos_fallback_to_gh_cli(client):
    """When pygithub unavailable, falls back to gh CLI."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": json.dumps([
            {"name": "repo1", "url": "https://github.com/test-org/repo1"},
            {"name": "repo2", "url": "https://github.com/test-org/repo2"},
        ])}
        repos = client.list_repos()
        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"


def test_list_repos_gh_cli_fails(client):
    """When gh CLI fails, returns empty list."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": False, "stderr": "not authenticated"}
        repos = client.list_repos()
        assert repos == []


def test_run_gh_cli_success(client):
    """run_gh_cli returns parsed result."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = client.run_gh_cli(["version"])
        assert result["success"] is True
        assert result["stdout"] == "hello"


def test_run_gh_cli_failure(client):
    """run_gh_cli handles non-zero return code."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: not logged in"
        mock_run.return_value = mock_result

        result = client.run_gh_cli(["pr", "list"])
        assert result["success"] is False
        assert "error" in result.get("stderr", "")


def test_run_gh_cli_timeout(client):
    """run_gh_cli handles timeout gracefully."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gh", timeout=30)
        result = client.run_gh_cli(["api", "slow-endpoint"])
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()


def test_run_gh_cli_exception(client):
    """run_gh_cli handles unexpected exceptions."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("gh not found")
        result = client.run_gh_cli(["repo", "list"])
        assert result["success"] is False


def test_create_release_fallback(client):
    """create_release uses gh CLI when no pygithub."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": "https://github.com/test-org/repo/releases/tag/v1.0"}
        result = client.create_release("repo", "v1.0", "Release v1.0", body="Changelog notes", draft=False)
        assert result["success"] is True


def test_create_release_fallback_fail(client):
    """create_release returns error when gh CLI fails."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": False, "stderr": "tag already exists"}
        result = client.create_release("repo", "v1.0", "Release v1.0", body="notes")
        assert result["success"] is False


def test_create_pr_fallback(client):
    """create_pr uses gh CLI when no pygithub."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": "https://github.com/test-org/repo/pull/42"}
        result = client.create_pr("repo", title="My PR", body="Description", head="feature", base="main")
        assert result["success"] is True


def test_create_pr_fallback_fail(client):
    """create_pr returns error when gh CLI fails."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": False, "stderr": "no commits"}
        result = client.create_pr("repo", title="My PR", body="Desc", head="feature")
        assert result["success"] is False


def test_list_workflow_runs(client):
    """list_workflow_runs parses gh CLI JSON output."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": json.dumps([
            {"databaseId": 123, "status": "completed", "conclusion": "success", "name": "CI", "headBranch": "main"},
        ])}
        runs = client.list_workflow_runs("repo")
        assert len(runs) == 1
        assert runs[0]["databaseId"] == 123


def test_list_workflow_runs_empty(client):
    """list_workflow_runs returns empty list on failure."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": False, "stderr": "error"}
        runs = client.list_workflow_runs("repo")
        assert runs == []


def test_list_issues(client):
    """list_issues parses gh CLI JSON output."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": json.dumps([
            {"number": 1, "title": "Bug: crash on start", "labels": [], "author": {"login": "user"}},
        ])}
        issues = client.list_issues("repo")
        assert len(issues) == 1
        assert issues[0]["number"] == 1


def test_list_issues_with_labels(client):
    """list_issues passes label filters to gh CLI."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": True, "stdout": "[]"}
        client.list_issues("repo", labels=["bug"])
        # Verify the label argument was passed
        labels_flag_index = None
        for i, arg in enumerate(mock_run.call_args[0][0]):
            if arg == "--label":
                labels_flag_index = i
                break
        assert labels_flag_index is not None


def test_list_issues_fail(client):
    """list_issues returns empty list on failure."""
    with patch.object(client, "run_gh_cli") as mock_run:
        mock_run.return_value = {"success": False, "stderr": "not found"}
        issues = client.list_issues("repo")
        assert issues == []
