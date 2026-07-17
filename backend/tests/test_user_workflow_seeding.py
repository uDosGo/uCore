from __future__ import annotations

from pathlib import Path

import app.api.user_workflow as mod


def test_seed_user_tasks_emits_canonical_markdown(tmp_path: Path):
    result = mod._seed_user_tasks(tmp_path / ".tasker")

    assert result["created_count"] == 4
    for path_str in result["created"]:
        text = Path(path_str).read_text(encoding="utf-8")
        assert "- status:" in text
        assert "- priority:" in text
        assert "- mission:" in text
        assert "- task:" in text
        assert "- binder:" in text
        assert "- tags:" in text


def test_discover_appflowy_databases_safe_is_non_fatal(monkeypatch):
    def _boom():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(mod, "discover_databases", _boom)
    dbs, errors = mod._discover_appflowy_databases_safe()

    assert dbs == {}
    assert errors
    assert "database_discovery_failed" in errors[0]
