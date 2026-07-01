from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.logging import log
from app.core.settings import settings
from app.skills.registry import run_skill_by_id


@dataclass(frozen=True)
class MaintenanceJob:
    skill_id: str
    time_hhmm: str
    params: dict


DEFAULT_JOBS = (
    MaintenanceJob("daily_backup", "03:00", {"type": "full"}),
    MaintenanceJob("vault_sync", "04:00", {"summary_only": True}),
    MaintenanceJob(
        "tasker_sync",
        "04:05",
        {
            "db": "database",
            "board": "inbox",
        },
    ),
    MaintenanceJob(
        "brain_sync",
        "04:15",
        {
            "hours": 24,
            "limit": 20,
            "include_spool": True,
            "include_appflowy": True,
        },
    ),
    MaintenanceJob(
        "clipboard_maintenance",
        "04:30",
        {"capture_current": True},
    ),
    MaintenanceJob(
        "spool_maintenance",
        "04:35",
        {"max_age_days": 14},
    ),
)


_scheduler: MaintenanceScheduler | None = None


def get_maintenance_scheduler() -> MaintenanceScheduler | None:
    return _scheduler


def set_maintenance_scheduler(
    scheduler: MaintenanceScheduler | None,
) -> None:
    global _scheduler
    _scheduler = scheduler


class MaintenanceScheduler:
    def __init__(
        self,
        *,
        state_path: Path | None = None,
        jobs: tuple[MaintenanceJob, ...] = DEFAULT_JOBS,
        interval_seconds: int = 60,
    ) -> None:
        self.state_path = (
            state_path or (settings.data_dir / "maintenance_state.json")
        )
        self.jobs = jobs
        self.interval_seconds = max(15, int(interval_seconds))
        self._state = self._load_state()
        self._task: asyncio.Task | None = None

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"last_run": {}, "last_result": {}, "started_at": None}
        try:
            import json

            with self.state_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"last_run": {}, "last_result": {}, "started_at": None}

    def _save_state(self) -> None:
        import json

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2, sort_keys=True)

    def status(self) -> dict:
        return {
            "jobs": [
                {
                    "skill_id": job.skill_id,
                    "time": job.time_hhmm,
                    "params": job.params,
                    "last_run": self._state.get("last_run", {}).get(
                        job.skill_id,
                    ),
                    "last_result": self._state.get("last_result", {}).get(
                        job.skill_id,
                    ),
                }
                for job in self.jobs
            ],
            "started_at": self._state.get("started_at"),
            "interval_seconds": self.interval_seconds,
        }

    async def start(self) -> None:
        if self._task is not None:
            return
        self._state["started_at"] = datetime.now().isoformat()
        self._save_state()
        self._task = asyncio.create_task(self.run_forever())
        log.info("Maintenance scheduler started with %d jobs", len(self.jobs))

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        log.info("Maintenance scheduler stopped")

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_due()
            except Exception as exc:
                log.warning("Maintenance scheduler cycle failed: %s", exc)
            await asyncio.sleep(self.interval_seconds)

    async def run_due(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now()
        ran: list[dict] = []
        for job in self.jobs:
            if not self._is_due(job, now):
                continue
            result = await run_skill_by_id(job.skill_id, **job.params)
            self._state.setdefault("last_run", {})[
                job.skill_id
            ] = now.date().isoformat()
            self._state.setdefault("last_result", {})[job.skill_id] = {
                "success": result.get("success", False),
                "timestamp": now.isoformat(),
            }
            self._save_state()
            ran.append({"skill_id": job.skill_id, "result": result})
            log.info(
                "Maintenance job ran: %s success=%s",
                job.skill_id,
                result.get("success"),
            )
        return ran

    def _is_due(self, job: MaintenanceJob, now: datetime) -> bool:
        last_run = self._state.get("last_run", {}).get(job.skill_id)
        if last_run == now.date().isoformat():
            return False
        hour_str, minute_str = job.time_hhmm.split(":", 1)
        due_hour = int(hour_str)
        due_minute = int(minute_str)
        return (now.hour, now.minute) >= (due_hour, due_minute)
