"""Tests for LintFix skill."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_lint_fix_check():
    """Lint fix check action returns errors list."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    result = await skill.run(action="check")
    assert result["success"] is True
    assert result["action"] == "check"
    assert "total_errors" in result
    assert "files_with_errors" in result
    assert "errors_by_file" in result
    assert "summary" in result


@pytest.mark.asyncio
async def test_lint_fix_report():
    """Lint fix report action returns categorized errors."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    result = await skill.run(action="report")
    assert result["success"] is True
    assert result["action"] == "report"
    assert "errors_by_code" in result
    assert "fixable_files" in result


@pytest.mark.asyncio
async def test_lint_fix_fix():
    """Lint fix fix action attempts to fix errors."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    result = await skill.run(action="fix", safe_only=True)
    assert result["success"] is True
    assert result["action"] == "fix"
    assert "remaining_errors" in result
    assert "files_remaining" in result


@pytest.mark.asyncio
async def test_lint_fix_invalid_action():
    """Invalid action returns error."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    result = await skill.run(action="invalid_action")
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_lint_fix_nonexistent_target():
    """Nonexistent target returns error."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    result = await skill.run(action="check", target="/nonexistent/path")
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_lint_fix_specific_file():
    """Lint fix can target a specific file."""
    from app.skills.builtin.lint_fix import LintFix

    skill = LintFix()
    # Target a file that exists
    result = await skill.run(action="check", target=__file__)
    assert result["success"] is True
    assert result["action"] == "check"
