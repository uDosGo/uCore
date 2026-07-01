"""Tests for episodic_store and episodic_log skill."""
from __future__ import annotations

from pathlib import Path

import pytest
from app.services.episodic_store import (
    append_entry,
    read_entries,
    summarize_entries,
)


def test_append_entry_creates_file_and_roundtrips(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    entry = append_entry(
        entry_type="correction",
        description="Fixed import error",
        context="Surfaced by tests",
        severity="medium",
        tags=["python"],
        source="test",
        log_path=log,
    )
    assert log.exists()
    assert entry["type"] == "correction"
    assert entry["description"] == "Fixed import error"
    assert entry["severity"] == "medium"
    assert entry["tags"] == ["python"]
    assert entry["source"] == "test"
    assert "timestamp" in entry


def test_append_entry_rejects_invalid_type(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    with pytest.raises(ValueError, match="Invalid type"):
        append_entry(
            entry_type="bogus",
            description="Should fail",
            log_path=log,
        )


def test_append_entry_rejects_invalid_severity(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    with pytest.raises(ValueError, match="Invalid severity"):
        append_entry(
            entry_type="lesson",
            description="Severity test",
            severity="critical",
            log_path=log,
        )


def test_read_entries_newest_first(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    append_entry(
        entry_type="lesson",
        description="First lesson",
        log_path=log,
    )
    append_entry(
        entry_type="correction",
        description="Second correction",
        log_path=log,
    )
    entries = read_entries(hours=48, log_path=log)
    assert len(entries) == 2
    # newest first
    assert entries[0]["description"] == "Second correction"
    assert entries[1]["description"] == "First lesson"


def test_read_entries_filters_by_type(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    append_entry(
        entry_type="lesson",
        description="A lesson",
        log_path=log,
    )
    append_entry(
        entry_type="correction",
        description="A correction",
        log_path=log,
    )
    entries = read_entries(hours=48, entry_type="correction", log_path=log)
    assert len(entries) == 1
    assert entries[0]["type"] == "correction"


def test_read_entries_filters_by_severity(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    append_entry(
        entry_type="lesson",
        description="Low severity",
        severity="low",
        log_path=log,
    )
    append_entry(
        entry_type="lesson",
        description="High severity",
        severity="high",
        log_path=log,
    )
    entries = read_entries(hours=48, severity="high", log_path=log)
    assert len(entries) == 1
    assert entries[0]["severity"] == "high"


def test_read_entries_empty_if_no_file(tmp_path: Path):
    log = tmp_path / "missing.jsonl"
    entries = read_entries(hours=24, log_path=log)
    assert entries == []


def test_summarize_entries_returns_markdown(tmp_path: Path):
    log = tmp_path / "corrections.jsonl"
    append_entry(
        entry_type="correction",
        description="Fixed a bug",
        log_path=log,
    )
    append_entry(
        entry_type="lesson",
        description="Write smaller patches",
        log_path=log,
    )
    summary = summarize_entries(hours=48, log_path=log)
    assert summary is not None
    assert "Episodic Log" in summary
    assert "Correction" in summary
    assert "Lesson" in summary
    assert "Fixed a bug" in summary


def test_summarize_entries_none_if_empty(tmp_path: Path):
    log = tmp_path / "missing.jsonl"
    assert summarize_entries(hours=24, log_path=log) is None


@pytest.mark.asyncio
async def test_episodic_log_skill_writes_entry(tmp_path: Path, monkeypatch):
    import app.services.episodic_store as store_mod
    import app.skills.builtin.episodic_log as skill_mod

    log_path = tmp_path / "corrections.jsonl"
    monkeypatch.setattr(store_mod, "EPISODIC_LOG", log_path)
    monkeypatch.setattr(
        store_mod, "EPISODIC_DIR", tmp_path,
    )

    skill = skill_mod.EpisodicLog()
    result = await skill.run(
        type="lesson",
        description="Prefer monkeypatching module-level constants",
        context="Testing pattern",
        severity="low",
        tags=["testing", "python"],
    )

    assert result["success"] is True
    assert result["entry"]["type"] == "lesson"
    assert result["entry"]["description"] == (
        "Prefer monkeypatching module-level constants"
    )
    assert log_path.exists()


@pytest.mark.asyncio
async def test_episodic_log_skill_rejects_invalid_type(monkeypatch):
    import app.skills.builtin.episodic_log as skill_mod
    skill = skill_mod.EpisodicLog()
    result = await skill.run(
        type="invalid_type",
        description="Should fail",
    )
    assert result["success"] is False
    assert "Invalid type" in result["error"]


@pytest.mark.asyncio
async def test_episodic_log_skill_requires_description(monkeypatch):
    import app.skills.builtin.episodic_log as skill_mod
    skill = skill_mod.EpisodicLog()
    result = await skill.run(type="lesson", description="")
    assert result["success"] is False
    assert "description" in result["error"]


@pytest.mark.asyncio
async def test_episodic_log_accepts_comma_separated_tags(
    tmp_path: Path, monkeypatch,
):
    import app.services.episodic_store as store_mod
    import app.skills.builtin.episodic_log as skill_mod

    log_path = tmp_path / "corrections.jsonl"
    monkeypatch.setattr(store_mod, "EPISODIC_LOG", log_path)
    monkeypatch.setattr(store_mod, "EPISODIC_DIR", tmp_path)

    skill = skill_mod.EpisodicLog()
    result = await skill.run(
        type="observation",
        description="Comma-separated tags test",
        tags="python, imports, testing",
    )
    assert result["success"] is True
    assert "python" in result["entry"]["tags"]
    assert "imports" in result["entry"]["tags"]


@pytest.mark.asyncio
async def test_brain_sync_includes_episodic_summary(tmp_path: Path):
    import app.services.episodic_store as store_mod
    import app.skills.builtin.brain_sync as mod

    project_root = tmp_path / "uCore"
    backend_dir = project_root / "backend"
    backend_dir.mkdir(parents=True)
    (backend_dir / "service.py").write_text(
        "print('backend')\n", encoding="utf-8",
    )

    log_path = tmp_path / "corrections.jsonl"
    append_entry(
        entry_type="correction",
        description="Restored missing import",
        severity="medium",
        log_path=log_path,
    )

    old_root = mod.PROJECT_ROOT
    old_wisdom = mod.WISDOM_PATH
    old_log = store_mod.EPISODIC_LOG
    try:
        mod.PROJECT_ROOT = project_root
        mod.WISDOM_PATH = project_root / "wisdom.md"
        store_mod.EPISODIC_LOG = log_path
        result = await mod.BrainSync().run(
            hours=24,
            limit=10,
            include_spool=False,
            include_appflowy=False,
        )
    finally:
        mod.PROJECT_ROOT = old_root
        mod.WISDOM_PATH = old_wisdom
        store_mod.EPISODIC_LOG = old_log

    assert result["success"] is True
    assert result["episodic_included"] is True
    written = (project_root / "wisdom.md").read_text(encoding="utf-8")
    assert "Episodic Log" in written
    assert "Restored missing import" in written
