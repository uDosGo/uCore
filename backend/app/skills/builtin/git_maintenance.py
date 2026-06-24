"""Git Maintenance Skill — detect and repair managed commits and branch merges.

Scans git repositories in the workspace for common structural issues:
- Uncommitted changes lingering too long
- Orphaned merged branches that should be deleted
- Divergent branches needing merge/rebase
- Detached HEAD states
- Interrupted rebase/merge/cherry-pick operations
- Non-conventional commit messages
"""
from __future__ import annotations
import asyncio
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.git_maintenance")

# ── constants ──────────────────────────────────────────────────────
CONVENTIONAL_PATTERN = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(\(.+?\))?!?:\s.+"
)
STALE_DAYS = 14
ORPHANED_DAYS = 7
STAGING_HOURS = 4

# Directories to ignore when scanning for repos
IGNORE_DIRS = {"node_modules", ".venv", "venv", "__pycache__",
               ".pytest_cache", ".mypy_cache", "dist", "build",
               ".git"}


# ── helpers (sync, called from async) ──────────────────────────────

def _find_git_repos(root: Path) -> list[Path]:
    """Return all directories under *root* that contain a `.git`."""
    repos: list[Path] = []
    try:
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            if entry.name in IGNORE_DIRS:
                continue
            git_dir = entry / ".git"
            if git_dir.exists():
                repos.append(entry)
    except PermissionError:
        pass
    return repos


async def _git_async(repo: Path, *args: str) -> tuple[int, str, str]:
    """Run git command asynchronously, return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "git", "-C", str(repo), *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out_str = stdout.decode("utf-8", errors="replace").strip()
    err_str = stderr.decode("utf-8", errors="replace").strip()
    return proc.returncode or 0, out_str, err_str


async def _get_default_branch(repo: Path) -> str:
    """Detect default branch (main/master)."""
    rc, out, _ = await _git_async(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if rc == 0:
        return out.strip()
    return "main"


async def _list_branches(repo: Path) -> list[dict]:
    """Return list of local branches with metadata.

    Each entry: {name, is_current, commit_date, ahead, behind, merged_to_default}
    """
    branches: list[dict] = []
    default = await _get_default_branch(repo)

    # Get branch list with timestamps
    rc, out, _ = await _git_async(
        repo, "for-each-ref", "--format=%(refname:short)|%(committerdate:unix)|%(HEAD)",
        "refs/heads/"
    )
    if rc != 0 or not out:
        return branches

    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 2:
            continue
        name = parts[0]
        ts_str = parts[1]
        is_head = len(parts) > 2 and parts[2] == "*"

        try:
            ts = datetime.fromtimestamp(int(ts_str), tz=timezone.utc)
        except (ValueError, OSError):
            ts = datetime.now(timezone.utc)

        # Check if merged to default branch
        rc2, _, _ = await _git_async(
            repo, "branch", "--merged", default, "--list", name
        )
        merged_to_default = rc2 == 0 and name != default

        # Ahead/behind counts vs default
        ahead = behind = 0
        if name != default:
            rc3, out3, _ = await _git_async(
                repo, "rev-list", "--left-right", "--count",
                f"{name}...{default}"
            )
            if rc3 == 0 and out3:
                parts2 = out3.split()
                if len(parts2) == 2:
                    ahead, behind = int(parts2[0]), int(parts2[1])

        branches.append({
            "name": name,
            "is_current": is_head,
            "commit_date": ts.isoformat(),
            "age_days": (datetime.now(timezone.utc) - ts).days,
            "ahead": ahead,
            "behind": behind,
            "merged_to_default": merged_to_default,
        })
    return branches


async def _check_uncommitted(repo: Path) -> list[dict]:
    """Find uncommitted changes with file counts and age."""
    issues: list[dict] = []

    # Staged changes
    rc, out, _ = await _git_async(repo, "diff", "--staged", "--stat")
    staged_count = len(out.splitlines()) if rc == 0 and out else 0

    # Unstaged changes
    rc2, out2, _ = await _git_async(repo, "diff", "--stat")
    unstaged_count = len(out2.splitlines()) if rc2 == 0 and out2 else 0

    # Untracked files
    rc3, out3, _ = await _git_async(repo, "ls-files", "--others", "--exclude-standard")
    untracked_count = len(out3.splitlines()) if rc3 == 0 and out3 else 0

    total = staged_count + unstaged_count + untracked_count
    if total > 0:
        issues.append({
            "type": "uncommitted",
            "staged": staged_count,
            "unstaged": unstaged_count,
            "untracked": untracked_count,
            "total": total,
            "severity": "warning" if total > 5 else "info",
        })
    return issues


async def _check_detached_head(repo: Path) -> list[dict]:
    """Check if repo is in detached HEAD state."""
    rc, out, _ = await _git_async(repo, "branch", "--show-current")
    if rc == 0 and not out.strip():
        # Detached HEAD
        rc2, out2, _ = await _git_async(repo, "rev-parse", "--short", "HEAD")
        sha = out2.strip() if rc2 == 0 else "unknown"
        return [{"type": "detached_head", "sha": sha,
                 "severity": "warning",
                 "suggestion": "Create a branch: git checkout -b <name>"}]
    return []


async def _check_interrupted_operations(repo: Path) -> list[dict]:
    """Detect in-progress rebase, merge, cherry-pick, bisect."""
    issues: list[dict] = []
    git_dir = repo / ".git"

    # Rebase
    if (git_dir / "REBASE_HEAD").exists() or (git_dir / "rebase-merge").exists():
        issues.append({"type": "in_progress_rebase", "severity": "error",
                       "suggestion": "git rebase --abort or git rebase --continue"})
    # Merge
    if (git_dir / "MERGE_HEAD").exists():
        issues.append({"type": "in_progress_merge", "severity": "error",
                       "suggestion": "git merge --abort or resolve conflicts and git commit"})
    # Cherry-pick
    if (git_dir / "CHERRY_PICK_HEAD").exists():
        issues.append({"type": "in_progress_cherry_pick", "severity": "error",
                       "suggestion": "git cherry-pick --abort or git cherry-pick --continue"})
    # Bisect
    if (git_dir / "BISECT_LOG").exists():
        issues.append({"type": "in_progress_bisect", "severity": "warning",
                       "suggestion": "git bisect reset"})
    return issues


async def _check_commit_messages(repo: Path, max_count: int = 30) -> list[dict]:
    """Check recent commit messages for conventional commit format."""
    rc, out, _ = await _git_async(
        repo, "log", f"--max-count={max_count}", "--format=%H|%s"
    )
    if rc != 0 or not out:
        return []

    bad: list[dict] = []
    for line in out.splitlines():
        sha, msg = line.split("|", 1)
        if not CONVENTIONAL_PATTERN.match(msg):
            bad.append({
                "type": "non_conventional_commit",
                "sha": sha[:8],
                "message": msg,
                "severity": "info",
            })
    return bad


async def _detect_orphaned_branches(repo: Path, branches: list[dict]) -> list[dict]:
    """Find branches merged into default that can be pruned."""
    issues: list[dict] = []
    for b in branches:
        if b["merged_to_default"] and b["name"] != "HEAD" and not b["is_current"]:
            if b["age_days"] >= ORPHANED_DAYS:
                issues.append({
                    "type": "orphaned_branch",
                    "branch": b["name"],
                    "age_days": b["age_days"],
                    "severity": "info",
                    "suggestion": f"git branch -d {b['name']}",
                })
    return issues


async def _detect_stale_branches(repo: Path, branches: list[dict]) -> list[dict]:
    """Find branches with no recent commits that aren't merged."""
    issues: list[dict] = []
    for b in branches:
        if (not b["merged_to_default"]
                and b["age_days"] >= STALE_DAYS
                and not b["is_current"]
                and b["name"] != "HEAD"):
            issues.append({
                "type": "stale_branch",
                "branch": b["name"],
                "age_days": b["age_days"],
                "ahead": b["ahead"],
                "behind": b["behind"],
                "severity": "warning",
                "suggestion": f"Review and clean up: git branch -D {b['name']} (force)",
            })
    return issues


async def _detect_divergent_branches(repo: Path, branches: list[dict]) -> list[dict]:
    """Find branches that have diverged from default and need attention."""
    issues: list[dict] = []
    for b in branches:
        if b["name"] == "HEAD" or b["is_current"]:
            continue
        if b["behind"] > 0 and b["ahead"] > 0:
            issues.append({
                "type": "divergent_branch",
                "branch": b["name"],
                "ahead": b["ahead"],
                "behind": b["behind"],
                "severity": "warning",
                "suggestion": (f"git checkout {b['name']} && "
                               f"git rebase {await _get_default_branch(repo)}"),
            })
    return issues


# ── repair actions ──────────────────────────────────────────────

async def _repair_commit(repo: Path, message: str) -> dict:
    """Stage all changes and commit with provided message."""
    rc_add, _, err_add = await _git_async(repo, "add", "-A")
    if rc_add != 0:
        return {"success": False, "error": f"git add -A failed: {err_add}"}
    rc_commit, out_commit, err_commit = await _git_async(repo, "commit", "-m", message)
    if rc_commit != 0:
        return {"success": False, "error": f"git commit failed: {err_commit}"}
    return {"success": True, "message": out_commit}


async def _repair_delete_branch(repo: Path, branch: str, force: bool = False) -> dict:
    """Delete a branch (safe delete, or force)."""
    args = ["branch", "-d" if not force else "-D", branch]
    rc, out, err = await _git_async(repo, *args)
    if rc != 0:
        return {"success": False, "error": err}
    return {"success": True, "message": out}


async def _repair_merge_branch(repo: Path, branch: str,
                                strategy: str = "rebase") -> dict:
    """Merge or rebase a branch onto the default branch."""
    default = await _get_default_branch(repo)
    if strategy == "merge":
        rc, out, err = await _git_async(repo, "merge", branch)
    else:
        rc, out, err = await _git_async(repo, "rebase", default)
    if rc != 0:
        return {"success": False, "error": err,
                "note": "Conflicts may need manual resolution"}
    return {"success": True, "message": out}


async def _repair_abort_operation(repo: Path, op_type: str) -> dict:
    """Abort an in-progress git operation."""
    git_cmd = {
        "merge": "merge --abort",
        "rebase": "rebase --abort",
        "cherry_pick": "cherry-pick --abort",
        "bisect": "bisect reset",
    }.get(op_type)
    if not git_cmd:
        return {"success": False, "error": f"Unknown operation: {op_type}"}
    rc, out, err = await _git_async(repo, *git_cmd.split())
    if rc != 0:
        return {"success": False, "error": err}
    return {"success": True, "message": out}


# ── skill class ─────────────────────────────────────────────────

class GitMaintenance(BaseSkill):
    meta = SkillMeta(
        id="git_maintenance",
        name="Git Maintenance",
        description=(
            "Detect and repair managed commits and branch merges. "
            "Scans workspace git repos for uncommitted changes, orphaned "
            "or stale branches, divergent branches, detached HEAD, "
            "interrupted operations, and non-conventional commit messages."
        ),
        category="maintenance",
        timeout=120,
        params=[
            SkillParam(name="mode", type="string", required=False,
                       default="detect",
                       description="Operation mode: 'detect' (default), 'repair', or 'full'"),
            SkillParam(name="repo_path", type="string", required=False,
                       default="",
                       description="Optional path to a single repo to scan"),
            SkillParam(name="auto_commit", type="boolean", required=False,
                       default=False,
                       description="Auto-commit uncommitted changes when repairing"),
            SkillParam(name="commit_message", type="string", required=False,
                       default="chore: auto-maintenance commit",
                       description="Commit message template for auto-commit"),
            SkillParam(name="prune_orphaned", type="boolean", required=False,
                       default=False,
                       description="Delete orphaned merged branches"),
            SkillParam(name="prune_stale", type="boolean", required=False,
                       default=False,
                       description="Delete stale unmerged branches"),
            SkillParam(name="abort_interrupted", type="boolean", required=False,
                       default=False,
                       description="Abort in-progress rebase/merge/cherry-pick"),
        ],
    )

    async def run(self, **kwargs) -> dict:
        mode = kwargs.get("mode", "detect")
        auto_commit = kwargs.get("auto_commit", False)
        commit_msg = kwargs.get("commit_message", "chore: auto-maintenance commit")
        prune_orphaned = kwargs.get("prune_orphaned", False)
        prune_stale = kwargs.get("prune_stale", False)
        abort_interrupted = kwargs.get("abort_interrupted", False)

        # Determine repos to scan
        explicit_repo = kwargs.get("repo_path", "")
        if explicit_repo:
            repo_path = Path(explicit_repo).resolve()
            repos = [repo_path] if (repo_path / ".git").exists() else []
        else:
            root = Path.cwd()
            repos = _find_git_repos(root)
            # Also check cwd itself
            if (root / ".git").exists() and root not in repos:
                repos.insert(0, root)

        if not repos:
            return {
                "success": True,
                "repos_scanned": 0,
                "issues": [],
                "repairs": [],
                "summary": "No git repositories found in workspace.",
            }

        all_issues: list[dict] = []
        all_repairs: list[dict] = []
        repo_results: list[dict] = []

        for repo in repos:
            repo_name = repo.name
            log.info("Scanning repo: %s", repo_name)

            issues: list[dict] = []
            repairs: list[dict] = []

            # ── detect ──
            repo_issues = await self._detect_all(repo)
            issues.extend(repo_issues)

            # ── repair (if mode allows) ──
            if mode in ("repair", "full"):
                repo_repairs = await self._repair_all(
                    repo, issues, auto_commit, commit_msg,
                    prune_orphaned, prune_stale, abort_interrupted,
                )
                repairs.extend(repo_repairs)

            repo_results.append({
                "repo": repo_name,
                "path": str(repo),
                "issues_count": len(issues),
                "repairs_count": len(repairs),
            })

            # Collect for summary
            for i in issues:
                i["repo"] = repo_name
            all_issues.extend(issues)
            for r in repairs:
                r["repo"] = repo_name
            all_repairs.extend(repairs)

        # Count by severity
        errors = [i for i in all_issues if i.get("severity") == "error"]
        warnings = [i for i in all_issues if i.get("severity") == "warning"]
        infos = [i for i in all_issues if i.get("severity") == "info"]

        summary_lines = [
            f"Scanned {len(repos)} repo(s). "
            f"Found {len(all_issues)} issue(s): "
            f"{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s)."
        ]
        if all_repairs:
            applied = sum(1 for r in all_repairs if r.get("success"))
            failed = sum(1 for r in all_repairs if not r.get("success"))
            summary_lines.append(
                f"Applied {applied} repair(s), {failed} failed."
            )

        # Breakdown by type
        type_counts: dict[str, int] = {}
        for i in all_issues:
            t = i.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        if type_counts:
            breakdown = "; ".join(f"{k}: {v}" for k, v in sorted(type_counts.items()))
            summary_lines.append(f"Breakdown: {breakdown}")

        return {
            "success": True,
            "repos_scanned": len(repos),
            "issues": all_issues,
            "repairs": all_repairs,
            "repo_results": repo_results,
            "summary": "\n".join(summary_lines),
        }

    # ── internal detection ──────────────────────────────────────────

    async def _detect_all(self, repo: Path) -> list[dict]:
        """Run all detection checks on a single repo."""
        issues: list[dict] = []

        # 1. Uncommitted changes
        issues.extend(await _check_uncommitted(repo))

        # 2. Detached HEAD
        issues.extend(await _check_detached_head(repo))

        # 3. Interrupted operations
        issues.extend(await _check_interrupted_operations(repo))

        # 4. Branches
        branches = await _list_branches(repo)

        # 5. Orphaned branches (merged & stale)
        issues.extend(await _detect_orphaned_branches(repo, branches))

        # 6. Stale branches (unmerged & old)
        issues.extend(await _detect_stale_branches(repo, branches))

        # 7. Divergent branches
        issues.extend(await _detect_divergent_branches(repo, branches))

        # 8. Commit message quality
        issues.extend(await _check_commit_messages(repo, max_count=30))

        return issues

    # ── internal repair ────────────────────────────────────────────

    async def _repair_all(
        self,
        repo: Path,
        issues: list[dict],
        auto_commit: bool,
        commit_msg: str,
        prune_orphaned: bool,
        prune_stale: bool,
        abort_interrupted: bool,
    ) -> list[dict]:
        """Apply repairs based on detected issues and flags."""
        repairs: list[dict] = []

        # Auto-commit uncommitted changes
        if auto_commit:
            uncommitted = [i for i in issues if i["type"] == "uncommitted"]
            if uncommitted:
                result = await _repair_commit(repo, commit_msg)
                result["action"] = "auto_commit"
                repairs.append(result)

        # Abort interrupted operations
        if abort_interrupted:
            for op_type in ("rebase", "merge", "cherry_pick", "bisect"):
                matches = [i for i in issues if i["type"] == f"in_progress_{op_type}"]
                if matches:
                    result = await _repair_abort_operation(repo, op_type)
                    result["action"] = f"abort_{op_type}"
                    repairs.append(result)

        # Prune orphaned merged branches
        if prune_orphaned:
            for i in issues:
                if i["type"] == "orphaned_branch":
                    branch = i["branch"]
                    result = await _repair_delete_branch(repo, branch, force=False)
                    result["action"] = f"delete_orphaned:{branch}"
                    repairs.append(result)

        # Prune stale branches
        if prune_stale:
            for i in issues:
                if i["type"] == "stale_branch":
                    branch = i["branch"]
                    result = await _repair_delete_branch(repo, branch, force=True)
                    result["action"] = f"delete_stale:{branch}"
                    repairs.append(result)

        return repairs
