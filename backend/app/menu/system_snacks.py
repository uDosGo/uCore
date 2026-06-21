"""System snack definitions and execution for macOS menu bar integrations.

Implements:
- Core Apple snacks (Reminders, Mail VIP, Contacts, Notes, Calendar, Permissions)
- Apple Intelligence shortcuts snack
- Markdown snack backed by markdown-it

All executions are spooled to replies.jsonl for auditability.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.menu.clipboard_buffer import add_clipboard_item, copy_text_to_clipboard


SPOOL_PATH = Path(
    os.getenv("UCORE_SNACKS_REPLIES", "~/.local/share/snackmachine/replies.jsonl")
).expanduser()

MARKDOWN_SNACK_DIR = Path(__file__).resolve().parents[2] / "tools" / "markdown_snack"
MARKDOWN_SNACK_JS = MARKDOWN_SNACK_DIR / "markdown-snack.js"


@dataclass(frozen=True)
class SystemSnack:
    id: str
    name: str
    kind: str
    icon: str
    refresh_seconds: int | None = None
    actions: tuple[str, ...] = ()


SYSTEM_SNACKS: tuple[SystemSnack, ...] = (
    SystemSnack("reminders", "Reminders", "badge", "✅", 30),
    SystemSnack("mail-vip", "Mail VIP", "badge", "📧", 60),
    SystemSnack("contacts-vip", "Contacts VIP", "badge", "👥", 300),
    SystemSnack("notes", "Notes", "action", "🗒️"),
    SystemSnack("calendar", "Calendar", "action", "📅"),
    SystemSnack("permissions-helper", "Permissions Helper", "action", "🔐"),
    SystemSnack(
        "apple-intelligence",
        "AI Tools",
        "multi-action",
        "🧠",
        actions=("summarise", "rewrite-professional", "compose"),
    ),
    SystemSnack(
        "markdown-tools",
        "Markdown Tools",
        "multi-action",
        "📝",
        actions=("format", "to-html", "validate"),
    ),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_spool(payload: dict[str, Any]) -> None:
    SPOOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SPOOL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _run_osascript(script: str, timeout: int = 8) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript execution failed")
    return proc.stdout.strip()


def _run_shell(command: list[str], cwd: Path | None = None, timeout: int = 20) -> tuple[int, str, str]:
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _snack_by_id(snack_id: str) -> SystemSnack | None:
    for snack in SYSTEM_SNACKS:
        if snack.id == snack_id:
            return snack
    return None


def _read_badge(snack_id: str) -> dict[str, Any]:
    if snack_id == "reminders":
        output = _run_osascript(
            'tell application "Reminders" to count (reminders whose completed is false)'
        )
        return {"count": int(output or "0")}

    if snack_id == "mail-vip":
        output = _run_osascript(
            'tell application "Mail" to count (messages of inbox whose vip status is true and read status is false)'
        )
        return {"count": int(output or "0")}

    if snack_id == "contacts-vip":
        output = _run_osascript(
            'tell application "Contacts" to get name of every person whose organization is false and note contains "VIP"'
        )
        names = [line.strip() for line in output.split(",") if line.strip()] if output else []
        return {"count": len(names), "names": names[:20]}

    raise ValueError(f"Unsupported badge snack: {snack_id}")


def _run_action(snack_id: str) -> dict[str, Any]:
    if snack_id == "notes":
        _run_osascript('tell application "Notes" to activate')
        return {"opened": "Notes"}

    if snack_id == "calendar":
        _run_osascript('tell application "Calendar" to activate')
        return {"opened": "Calendar"}

    if snack_id == "permissions-helper":
        _run_shell(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"])
        return {"opened": "System Settings > Privacy > Automation"}

    raise ValueError(f"Unsupported action snack: {snack_id}")


def _run_apple_intelligence(action: str, text: str | None = None) -> dict[str, Any]:
    shortcut_map = {
        "summarise": "AI - Summarise",
        "rewrite-professional": "AI - Rewrite Professional",
        "compose": "AI - Compose",
    }
    shortcut = shortcut_map.get(action)
    if not shortcut:
        raise ValueError(f"Unknown apple-intelligence action: {action}")

    if shutil.which("shortcuts") is None:
        raise RuntimeError("shortcuts CLI not available")

    cmd = ["shortcuts", "run", shortcut]
    if text:
        cmd.extend(["--input", text])

    code, out, err = _run_shell(cmd, timeout=60)
    if code != 0:
        raise RuntimeError(err or f"Shortcut '{shortcut}' failed")

    if text:
        add_clipboard_item(
            source="ai_snack",
            type="text",
            content=text,
            metadata={"role": "prompt", "action": action, "shortcut": shortcut},
            pinned=False,
        )
    if out:
        add_clipboard_item(
            source="ai_snack",
            type="text",
            content=out,
            metadata={"role": "reply", "action": action, "shortcut": shortcut},
            pinned=False,
        )
        copy_text_to_clipboard(out)

    return {"shortcut": shortcut, "output": out}


def _run_markdown_tool(action: str, text: str | None = None) -> dict[str, Any]:
    if action not in {"format", "to-html", "validate"}:
        raise ValueError(f"Unknown markdown action: {action}")

    if shutil.which("node") is None:
        raise RuntimeError("node is required for markdown snack")

    if not MARKDOWN_SNACK_JS.exists():
        raise RuntimeError(f"markdown snack script missing: {MARKDOWN_SNACK_JS}")

    cmd = ["node", str(MARKDOWN_SNACK_JS), action]
    if text:
        cmd.append(text)

    code, out, err = _run_shell(cmd, cwd=MARKDOWN_SNACK_DIR, timeout=30)
    if code != 0:
        raise RuntimeError(err or "markdown snack execution failed")

    if text:
        add_clipboard_item(
            source="markdown_snack",
            type="text",
            content=text,
            metadata={"role": "input", "action": action},
            pinned=False,
        )
    if out:
        add_clipboard_item(
            source="markdown_snack",
            type="text",
            content=out,
            metadata={"role": "output", "action": action},
            pinned=False,
        )

    payload: dict[str, Any] = {"action": action, "output": out}
    if action == "validate":
        try:
            payload["validation"] = json.loads(out)
        except json.JSONDecodeError:
            payload["validation"] = {"valid": False, "error": "invalid validator output"}
    return payload


def list_system_snacks() -> list[dict[str, Any]]:
    return [
        {
            "id": s.id,
            "name": s.name,
            "kind": s.kind,
            "icon": s.icon,
            "refresh_seconds": s.refresh_seconds,
            "actions": list(s.actions),
        }
        for s in SYSTEM_SNACKS
    ]


def read_system_badges() -> list[dict[str, Any]]:
    badges: list[dict[str, Any]] = []
    for snack in SYSTEM_SNACKS:
        if snack.kind != "badge":
            continue
        try:
            data = _read_badge(snack.id)
            badges.append({"id": snack.id, "ok": True, **data})
        except Exception as exc:
            badges.append({"id": snack.id, "ok": False, "error": str(exc)})
    return badges


def run_system_snack(snack_id: str, action: str | None = None, text: str | None = None) -> dict[str, Any]:
    snack = _snack_by_id(snack_id)
    if snack is None:
        raise ValueError(f"Unknown system snack: {snack_id}")

    started = _utc_now()
    try:
        if snack.kind == "badge":
            result = _read_badge(snack.id)
        elif snack.kind == "action":
            result = _run_action(snack.id)
        elif snack.id == "apple-intelligence":
            if not action:
                raise ValueError("action is required for apple-intelligence")
            result = _run_apple_intelligence(action, text)
        elif snack.id == "markdown-tools":
            if not action:
                raise ValueError("action is required for markdown-tools")
            result = _run_markdown_tool(action, text)
        else:
            raise ValueError(f"Unsupported system snack: {snack_id}")

        payload = {
            "timestamp": started,
            "type": "system_snack",
            "snack_id": snack_id,
            "action": action,
            "status": "success",
            "result": result,
        }
        _append_spool(payload)
        return payload
    except Exception as exc:
        payload = {
            "timestamp": started,
            "type": "system_snack",
            "snack_id": snack_id,
            "action": action,
            "status": "error",
            "error": str(exc),
        }
        _append_spool(payload)
        return payload
