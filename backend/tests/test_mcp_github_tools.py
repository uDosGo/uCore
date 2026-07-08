"""Unit tests for GitHub MCP Tools (autonomous workflow automation)."""
from __future__ import annotations

from datetime import UTC
from unittest.mock import MagicMock, patch

import pytest

from app.services.mcp.github_client import GitHubClient
from app.services.mcp.github_tools import GitHubTools


@pytest.fixture
def tools(monkeypatch):
    """GitHubTools with mocked client."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    ght = GitHubTools(token="fake-token", org="test-org")
    ght.client = MagicMock(spec=GitHubClient)
    return ght


def test_publish_release_no_token(tools):
    """Publish release without PyGithub falls back to gh CLI."""
    tools.client.create_release.return_value = {
        "success": True,
        "release_url": "https://github.com/test-org/repo/releases/tag/v0.1.0",
        "tag": "v0.1.0",
    }
    result = tools.publish_release("repo", version="0.1.0")
    assert result["success"] is True
    assert result["tag"] == "v0.1.0"


def test_publish_release_draft(tools):
    """Publish draft release."""
    tools.client.create_release.return_value = {
        "success": True,
        "release_url": "https://github.com/test-org/repo/releases/tag/v0.2.0",
        "tag": "v0.2.0",
    }
    result = tools.publish_release("repo", version="0.2.0", draft=True)
    assert result["success"] is True


def test_publish_release_no_version(tools):
    """Auto-detect version when none provided."""
    tools.client.create_release.return_value = {
        "success": True,
        "release_url": "https://github.com/test-org/repo/releases/tag/v0.1.0",
        "tag": "v0.1.0",
    }
    result = tools.publish_release("repo", auto_tag=True)
    assert result["success"] is True
    assert "v0.1" in result["tag"]


def test_sync_repos_empty(tools):
    """Sync repos when no repos exist."""
    tools.client.list_repos.return_value = []
    result = tools.sync_repos()
    assert result["success"] is False
    assert "No repos found" in result.get("error", "")


def test_sync_repos_success(tools, tmp_path):
    """Sync repos clones missing and pulls existing."""
    tools.client.list_repos.return_value = [
        {"name": "repo1", "html_url": "https://github.com/test-org/repo1"},
    ]
    # Simulate repo doesn't exist locally → will try clone
    with patch("app.services.mcp.github_tools.Path.exists") as mock_exists:
        mock_exists.return_value = False
        with patch.object(tools, "_git_clone") as mock_clone:
            mock_clone.return_value = "ok"
            result = tools.sync_repos(local_dir=str(tmp_path))
            assert result["success"] is True
            assert result["total"] == 1


def test_sync_repos_pull_existing(tools, tmp_path):
    """Sync repos pulls existing repos."""
    tools.client.list_repos.return_value = [
        {"name": "repo1", "html_url": "https://github.com/test-org/repo1"},
    ]
    with patch("app.services.mcp.github_tools.Path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch.object(tools, "_git_pull") as mock_pull:
            mock_pull.return_value = "ok"
            result = tools.sync_repos(local_dir=str(tmp_path))
            assert result["success"] is True
            assert result["total"] == 1


def test_create_pr_no_branch(tools):
    """create_pr fails when no current branch."""
    with patch.object(tools, "_get_current_branch") as mock_branch:
        mock_branch.return_value = None
        result = tools.create_pr("repo")
        assert result["success"] is False


def test_create_pr_on_main_branch(tools):
    """create_pr fails when on base branch."""
    with patch.object(tools, "_get_current_branch") as mock_branch:
        mock_branch.return_value = "main"
        result = tools.create_pr("repo", base="main")
        assert result["success"] is False


def test_create_pr_success(tools):
    """create_pr succeeds with valid branch."""
    with patch.object(tools, "_get_current_branch") as mock_branch:
        mock_branch.return_value = "feature-xyz"
        tools.client.create_pr.return_value = {
            "success": True,
            "pr_url": "https://github.com/test-org/repo/pull/42",
            "pr_number": 42,
        }
        result = tools.create_pr("repo")
        assert result["success"] is True
        assert result["pr_number"] == 42


def test_create_pr_auto_title(tools):
    """Auto-generated title and body."""
    with patch.object(tools, "_get_current_branch") as mock_branch:
        mock_branch.return_value = "fix-crash-bug"
        tools.client.create_pr.return_value = {
            "success": True,
            "pr_url": "https://github.com/test-org/repo/pull/43",
            "pr_number": 43,
        }
        result = tools.create_pr("repo")
        assert result["success"] is True


def test_heal_issues_no_issues(tools):
    """heal_issues with no open issues."""
    tools.client.list_issues.return_value = []
    result = tools.heal_issues("repo")
    assert result["success"] is True
    assert "No open issues" in result["message"]


def test_heal_issues_auto_labels(tools):
    """Auto-label issues by title keywords."""
    tools.client.list_issues.return_value = [
        {"number": 1, "title": "Bug: crash on startup", "labels": []},
        {"number": 2, "title": "Feature: add dark mode", "labels": []},
    ]
    with patch.object(tools, "_add_labels") as mock_add:
        mock_add.return_value = True
        result = tools.heal_issues("repo", auto_label=True)
        assert result["success"] is True
        assert result["issues_processed"] == 2
        assert result["actions_taken"] >= 2


def test_heal_issues_stale_closing(tools):
    """Auto-close stale issues."""
    from datetime import datetime, timedelta
    stale_date = (datetime.now(UTC) - timedelta(days=60)).isoformat()
    tools.client.list_issues.return_value = [
        {"number": 5, "title": "Old issue", "labels": [], "updatedAt": stale_date},
    ]
    with patch.object(tools, "_add_labels") as mock_add:
        mock_add.return_value = True
        with patch.object(tools, "_close_issue") as mock_close:
            mock_close.return_value = True
            result = tools.heal_issues("repo", auto_label=True, auto_close_stale=True, stale_days=30)
            assert result["success"] is True
            assert mock_close.called


def test_actions_status_no_runs(tools):
    """Actions status with no workflows."""
    tools.client.list_repos.return_value = [{"name": "repo1"}]
    tools.client.list_workflow_runs.return_value = []
    result = tools.actions_status()
    assert result["success"] is True
    assert result["total_runs"] == 0


def test_actions_status_with_failures(tools):
    """Actions status reports failures."""
    tools.client.list_repos.return_value = [{"name": "repo1"}]
    tools.client.list_workflow_runs.return_value = [
        {"databaseId": 1, "status": "completed", "conclusion": "success", "name": "CI", "headBranch": "main"},
        {"databaseId": 2, "status": "completed", "conclusion": "failure", "name": "Lint", "headBranch": "main"},
    ]
    result = tools.actions_status()
    assert result["total_runs"] == 2
    assert result["failures"] == 1


def test_actions_status_auto_retry(tools):
    """Auto-retry failed workflows."""
    tools.client.list_repos.return_value = [{"name": "repo1"}]
    tools.client.list_workflow_runs.return_value = [
        {"databaseId": 2, "status": "completed", "conclusion": "failure", "name": "Lint", "headBranch": "main"},
    ]
    with patch.object(tools, "_retry_workflow") as mock_retry:
        mock_retry.return_value = {"success": True}
        result = tools.actions_status(auto_retry_failed=True)
        assert result["retries"] == 1


def test_approve_pr_mergeable(tools):
    """Approve a PR with all checks passing."""
    tools.client.run_gh_cli.return_value = {
        "success": True,
        "stdout": '{"title": "Fix", "state": "OPEN", "mergeable": "MERGEABLE"}',
    }
    with patch.object(tools, "_run_local_tests") as mock_tests:
        mock_tests.return_value = {"success": True}
        result = tools.approve_pr("repo", pr_number=1, auto_merge=False, run_tests=True)
        assert result["success"] is True
        assert result["approved"] is True


def test_approve_pr_not_mergeable(tools):
    """Approve fails when PR is not mergeable."""
    tools.client.run_gh_cli.return_value = {
        "success": True,
        "stdout": '{"title": "Fix", "state": "OPEN", "mergeable": "NOT_MERGEABLE"}',
    }
    result = tools.approve_pr("repo", pr_number=1, run_tests=False)
    assert result["success"] is False
    assert result["approved"] is False


def test_approve_pr_tests_fail(tools):
    """Approve fails when local tests fail."""
    tools.client.run_gh_cli.return_value = {
        "success": True,
        "stdout": '{"title": "Fix", "state": "OPEN", "mergeable": "MERGEABLE"}',
    }
    with patch.object(tools, "_run_local_tests") as mock_tests:
        mock_tests.return_value = {"success": False}
        result = tools.approve_pr("repo", pr_number=1, run_tests=True)
        assert result["success"] is False


def test_approve_pr_auto_merge(tools):
    """Approve + auto-merge when all checks pass."""
    tools.client.run_gh_cli.return_value = {
        "success": True,
        "stdout": '{"title": "Fix", "state": "OPEN", "mergeable": "MERGEABLE"}',
    }
    with patch.object(tools, "_run_local_tests") as mock_tests:
        mock_tests.return_value = {"success": True}
        result = tools.approve_pr("repo", pr_number=1, auto_merge=True, run_tests=False)
        assert result["success"] is True
        assert result["approved"] is True


def test_get_github_tools_singleton():
    """get_github_tools returns same instance."""
    from app.services.mcp.github_tools import get_github_tools
    t1 = get_github_tools()
    t2 = get_github_tools()
    assert t1 is t2


def test_detect_issue_labels_bug():
    tools = GitHubTools(token="", org="test")
    assert "bug" in tools._detect_issue_labels("Bug: crash on startup")


def test_detect_issue_labels_feature():
    tools = GitHubTools(token="", org="test")
    assert "enhancement" in tools._detect_issue_labels("Feature: add dark mode")


def test_detect_issue_labels_doc():
    tools = GitHubTools(token="", org="test")
    assert "documentation" in tools._detect_issue_labels("Update docs for API")


def test_detect_issue_labels_empty():
    tools = GitHubTools(token="", org="test")
    assert tools._detect_issue_labels("Refactor internal logic") == []
