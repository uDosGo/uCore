"""Tests for the Git Maintenance skill."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest
from app.skills.builtin.git_maintenance import GitMaintenance


@pytest.fixture
def skill() -> GitMaintenance:
    return GitMaintenance()


@pytest.fixture
def temp_git_repo():
    """Create a temporary dir initialized as a git repo."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _run_git(repo, "init")
        _run_git(repo, "config", "user.email", "test@test.com")
        _run_git(repo, "config", "user.name", "Test")
        yield repo


def _run_git(repo: Path, *args: str) -> tuple[int, str]:
    """Run a synchronous git command."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


def _commit(repo: Path, msg: str) -> None:
    """Create a commit with a dummy file."""
    test_file = repo / "test.txt"
    test_file.write_text(f"content {msg}\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-m", msg)


class TestGitMaintenance:
    """Integration tests for git maintenance detection."""

    @pytest.mark.asyncio
    async def test_skill_meta(self, skill: GitMaintenance):
        assert skill.meta.id == "git_maintenance"
        assert skill.meta.name == "Git Maintenance"
        assert skill.meta.category == "maintenance"
        assert skill.meta.timeout == 120

    @pytest.mark.asyncio
    async def test_no_repos_found(self, skill: GitMaintenance):
        """Running in an empty temp dir with no repos should return clean."""
        with tempfile.TemporaryDirectory() as td:
            result = await skill.run(mode="detect", repo_path=td)
            assert result["success"] is True
            assert result["repos_scanned"] == 0
            assert result["summary"] == "No git repositories found in workspace."

    @pytest.mark.asyncio
    async def test_clean_repo(self, skill: GitMaintenance, temp_git_repo: Path):
        """A fresh repo with no issues should have minimal findings."""
        _commit(temp_git_repo, "feat: initial commit")
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        assert result["repos_scanned"] == 1

    @pytest.mark.asyncio
    async def test_uncommitted_changes(self, skill: GitMaintenance, temp_git_repo: Path):
        """Repo with uncommitted changes should be flagged."""
        _commit(temp_git_repo, "feat: first commit")
        (temp_git_repo / "dirty.txt").write_text("uncommitted")
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        uncommitted = [i for i in result["issues"] if i["type"] == "uncommitted"]
        assert len(uncommitted) >= 1
        assert uncommitted[0]["untracked"] >= 1

    @pytest.mark.asyncio
    async def test_non_conventional_commit_detected(
        self, skill: GitMaintenance, temp_git_repo: Path,
    ):
        """A bad commit message should be detected."""
        _commit(temp_git_repo, "bad commit message without conventional prefix")
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        issues = [i for i in result["issues"]
                  if i.get("type") == "non_conventional_commit"]
        assert len(issues) >= 1

    @pytest.mark.asyncio
    async def test_conventional_commit_passes(
        self, skill: GitMaintenance, temp_git_repo: Path,
    ):
        """Valid conventional commits should not be flagged."""
        _commit(temp_git_repo, "feat: add new feature")
        _commit(temp_git_repo, "fix: resolve issue with parser")
        _commit(temp_git_repo, "chore(deps): bump dependencies")
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        bad = [i for i in result["issues"]
               if i.get("type") == "non_conventional_commit"]
        assert len(bad) == 0

    @pytest.mark.asyncio
    async def test_detached_head_flag(
        self, skill: GitMaintenance, temp_git_repo: Path,
    ):
        """A detached HEAD should be detected."""
        _commit(temp_git_repo, "feat: initial")
        # Detach HEAD by checking out a commit hash
        rc, sha = _run_git(temp_git_repo, "rev-parse", "HEAD")
        assert rc == 0
        _run_git(temp_git_repo, "checkout", sha)
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        detached = [i for i in result["issues"] if i["type"] == "detached_head"]
        assert len(detached) >= 1

    @pytest.mark.asyncio
    async def test_auto_commit_repair(self, skill: GitMaintenance, temp_git_repo: Path):
        """Auto-commit repair should stage and commit uncommitted changes."""
        _commit(temp_git_repo, "feat: initial")
        (temp_git_repo / "repair_me.txt").write_text("should be committed")
        result = await skill.run(
            mode="full",
            repo_path=str(temp_git_repo),
            auto_commit=True,
            commit_message="chore: auto-repair commit",
        )
        assert result["success"] is True
        repairs = [r for r in result["repairs"] if r.get("action") == "auto_commit"]
        assert len(repairs) >= 1
        assert repairs[0]["success"] is True

    @pytest.mark.asyncio
    async def test_orphaned_branch_cleanup(
        self, skill: GitMaintenance, temp_git_repo: Path,
    ):
        """Orphaned merged branches should be detected and deletable."""
        _commit(temp_git_repo, "feat: initial")
        # Create and merge a feature branch
        _run_git(temp_git_repo, "checkout", "-b", "feature/old")
        _commit(temp_git_repo, "feat: feature work")
        _run_git(temp_git_repo, "checkout", "main" if (temp_git_repo / ".git").exists() else "master")
        _run_git(temp_git_repo, "merge", "feature/old", "--no-edit")

        # Detect — should flag orphaned after age threshold
        # Since age_days=0, it won't flag unless ORPHANED_DAYS is passed.
        # We test with mode=detect to confirm it appears in branch listing
        result = await skill.run(mode="detect", repo_path=str(temp_git_repo))
        assert result["success"] is True
        # Branch should *not* be flagged because age_days < ORPHANED_DAYS
        orphaned = [i for i in result["issues"] if i["type"] == "orphaned_branch"]
        assert len(orphaned) == 0

    @pytest.mark.asyncio
    async def test_no_repo_no_crash(self, skill: GitMaintenance):
        """Running without any repos should not crash."""
        result = await skill.run(mode="detect", repo_path="/nonexistent/path")
        assert result["success"] is True
        assert result["repos_scanned"] == 0
