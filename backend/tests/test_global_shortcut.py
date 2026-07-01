"""Tests for shortcut_utils — macOS global shortcut parsing."""
from __future__ import annotations

from app.menu.shortcut_utils import (
    MOD_COMMAND,
    MOD_CONTROL,
    MOD_OPTION,
    MOD_SHIFT,
    parse_shortcut,
    shortcut_display,
)


class TestParseShortcut:
    def test_ctrl_cmd_v(self):
        result = parse_shortcut("ctrl+cmd+v")
        assert result is not None
        mods, key = result
        assert mods == (MOD_CONTROL | MOD_COMMAND)
        assert key == 9  # V key code

    def test_cmd_shift_v(self):
        result = parse_shortcut("cmd+shift+v")
        assert result is not None
        mods, key = result
        assert mods == (MOD_COMMAND | MOD_SHIFT)
        assert key == 9

    def test_ctrl_opt_c(self):
        result = parse_shortcut("ctrl+opt+c")
        assert result is not None
        mods, key = result
        assert mods == (MOD_CONTROL | MOD_OPTION)
        assert key == 8  # C key code

    def test_order_independent(self):
        """Modifier order in the string should not matter."""
        r1 = parse_shortcut("cmd+ctrl+v")
        r2 = parse_shortcut("ctrl+cmd+v")
        assert r1 == r2

    def test_alias_command(self):
        r1 = parse_shortcut("cmd+v")
        r2 = parse_shortcut("command+v")
        assert r1 is not None
        assert r1 == r2

    def test_alias_control(self):
        r1 = parse_shortcut("ctrl+v")
        r2 = parse_shortcut("control+v")
        assert r1 is not None
        assert r1 == r2

    def test_alias_option(self):
        r1 = parse_shortcut("opt+v")
        r2 = parse_shortcut("alt+v")
        r3 = parse_shortcut("option+v")
        assert r1 is not None
        assert r1 == r2 == r3

    def test_missing_key_returns_none(self):
        assert parse_shortcut("ctrl+cmd") is None

    def test_missing_modifier_returns_none(self):
        assert parse_shortcut("v") is None

    def test_unknown_token_returns_none(self):
        assert parse_shortcut("super+v") is None

    def test_empty_returns_none(self):
        assert parse_shortcut("") is None

    def test_extra_whitespace(self):
        result = parse_shortcut("ctrl + cmd + v")
        assert result is not None
        mods, key = result
        assert mods == (MOD_CONTROL | MOD_COMMAND)
        assert key == 9

    def test_digit_key(self):
        result = parse_shortcut("cmd+1")
        assert result is not None
        assert result[1] == 18  # key code for 1


class TestShortcutDisplay:
    def test_ctrl_cmd_v(self):
        assert shortcut_display("ctrl+cmd+v") == "⌃⌘V"

    def test_cmd_shift_v(self):
        assert shortcut_display("cmd+shift+v") == "⇧⌘V"

    def test_ctrl_opt_c(self):
        assert shortcut_display("ctrl+opt+c") == "⌃⌥C"

    def test_symbol_order(self):
        # Standard macOS order: ⌃ ⌥ ⇧ ⌘
        assert shortcut_display("cmd+shift+ctrl+opt+v") == "⌃⌥⇧⌘V"

    def test_unknown_returns_original(self):
        raw = "super+v"
        assert shortcut_display(raw) == raw

    def test_uppercase_key(self):
        assert shortcut_display("ctrl+cmd+V") == "⌃⌘V"


class TestSettings:
    def test_clipboard_shortcut_default(self):
        from app.core.settings import settings

        assert settings.clipboard_shortcut == "ctrl+cmd+v"

    def test_clipboard_shortcut_env_override(self, monkeypatch):
        monkeypatch.setenv("UCORE_CLIPBOARD_SHORTCUT", "cmd+shift+v")
        import importlib

        import app.core.settings as mod
        importlib.reload(mod)
        assert mod.settings.clipboard_shortcut == "cmd+shift+v"
        importlib.reload(mod)  # restore


class TestMetadataEndpoint:
    def test_system_info_includes_shortcut(self):
        from app.core.settings import settings
        assert hasattr(settings, "clipboard_shortcut")
        assert settings.clipboard_shortcut
