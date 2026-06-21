"""Focused tests for the local memory-layer skills."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_attach_context_includes_wisdom(tmp_path: Path):
    import app.skills.builtin.attach_context as mod

    context_file = tmp_path / "CONTEXT.md"
    wisdom_file = tmp_path / "wisdom.md"
    context_file.write_text("# Context\nBase architecture", encoding="utf-8")
    wisdom_file.write_text("# Wisdom\nLesson learned", encoding="utf-8")

    old_context = dict(mod.PROJECT_CONTEXT_FILES)
    old_wisdom = dict(mod.PROJECT_WISDOM_FILES)
    mod.PROJECT_CONTEXT_FILES = {"ucore": context_file, "default": context_file}
    mod.PROJECT_WISDOM_FILES = {"ucore": wisdom_file, "default": wisdom_file}
    try:
        result = await mod.AttachContext().run(project="ucore", format="raw", include_wisdom=True)
    finally:
        mod.PROJECT_CONTEXT_FILES = old_context
        mod.PROJECT_WISDOM_FILES = old_wisdom

    assert result["success"] is True
    assert result["has_wisdom"] is True
    assert "Base architecture" in result["content"]
    assert "Lesson learned" in result["content"]


@pytest.mark.asyncio
async def test_brain_sync_writes_wisdom(tmp_path: Path):
    import app.skills.builtin.brain_sync as mod

    project_root = tmp_path / "uCore"
    backend_dir = project_root / "backend"
    docs_dir = project_root / "docs"
    frontend_dir = project_root / "frontend"
    backend_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)
    frontend_dir.mkdir(parents=True)
    (backend_dir / "service.py").write_text("print('backend')\n", encoding="utf-8")
    (docs_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    old_root = mod.PROJECT_ROOT
    old_wisdom = mod.WISDOM_PATH
    try:
        mod.PROJECT_ROOT = project_root
        mod.WISDOM_PATH = project_root / "wisdom.md"
        result = await mod.BrainSync().run(hours=24, limit=10)
    finally:
        mod.PROJECT_ROOT = old_root
        mod.WISDOM_PATH = old_wisdom

    assert result["success"] is True
    assert result["count"] >= 2
    written = (project_root / "wisdom.md").read_text(encoding="utf-8")
    assert "Recent Change Scan" in written
    assert "backend/service.py" in written or "docs/guide.md" in written
