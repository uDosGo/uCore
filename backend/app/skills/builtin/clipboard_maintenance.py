from __future__ import annotations

from app.clipboard.clipboard_buffer import (
    DEFAULT_MAX_DAYS,
    DEFAULT_MAX_ITEMS,
    capture_current_clipboard,
    cleanup_history,
)
from app.core.logging import log
from app.skills.base import BaseSkill, SkillMeta, SkillParam


class ClipboardMaintenance(BaseSkill):
    meta = SkillMeta(
        id="clipboard_maintenance",
        name="Clipboard Maintenance",
        description=(
            "Capture current clipboard text and clean clipboard history"
        ),
        category="maintenance",
        timeout=30,
        params=[
            SkillParam(
                name="capture_current",
                type="boolean",
                required=False,
                default=True,
            ),
            SkillParam(
                name="source",
                type="string",
                required=False,
                default="maintenance",
            ),
            SkillParam(
                name="max_items",
                type="number",
                required=False,
                default=DEFAULT_MAX_ITEMS,
            ),
            SkillParam(
                name="max_days",
                type="number",
                required=False,
                default=DEFAULT_MAX_DAYS,
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        capture_current = bool(kwargs.get("capture_current", True))
        source = str(kwargs.get("source", "maintenance"))
        max_items = int(kwargs.get("max_items", DEFAULT_MAX_ITEMS))
        max_days = int(kwargs.get("max_days", DEFAULT_MAX_DAYS))

        capture_result: dict = {"status": "disabled"}
        if capture_current:
            try:
                item = capture_current_clipboard(
                    source=source,
                    metadata={"trigger": "maintenance_scheduler"},
                )
                capture_result = {
                    "status": "captured",
                    "item_id": item["id"],
                    "source": item["source"],
                }
            except ValueError as exc:
                capture_result = {"status": "skipped", "reason": str(exc)}
            except Exception as exc:
                log.warning(
                    "Clipboard capture during maintenance failed: %s",
                    exc,
                )
                capture_result = {"status": "error", "reason": str(exc)}

        cleanup_result = cleanup_history(
            max_items=max_items,
            max_days=max_days,
        )

        return {
            "success": True,
            "capture": capture_result,
            "cleanup": cleanup_result,
            "max_items": max_items,
            "max_days": max_days,
        }
