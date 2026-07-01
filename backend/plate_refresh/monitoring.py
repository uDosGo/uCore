"""Template Monitoring & Audit Logging System.

Tracks template usage, maintains audit trails, and provides health checks
for corruption and version drift detection.

Features:
- Usage tracking (who used which plate, when, and how)
- Audit trail (all plate operations logged to SPOOL)
- Health checks (corruption detection, version drift)
- Usage statistics and reporting

Usage:
    from plate_refresh.monitoring import PlateMonitor

    monitor = PlateMonitor()
    monitor.log_usage("vault.user_vault_seed", "render", "user")
    monitor.log_audit("vault.user_vault_seed", "verify", {"passed": True})
    report = monitor.health_check("vault.user_vault_seed")
    stats = monitor.get_usage_stats("vault.user_vault_seed")
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from plate_refresh.models import PlateMeta
from plate_refresh.refresh import discover_plates, load_plate

log = logging.getLogger("ucore.plate_refresh.monitoring")

ROOT = Path(__file__).resolve().parents[2]
MONITOR_DB = Path.home() / ".ucore" / "plate_monitor.db"


# ─── Database Setup ───────────────────────────────────────


def _get_db() -> sqlite3.Connection:
    """Get or create the monitoring database connection."""
    MONITOR_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MONITOR_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Initialize the monitoring database schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS plate_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            user_id TEXT DEFAULT 'unknown',
            timestamp TEXT NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            success INTEGER DEFAULT 1,
            details TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS plate_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            version_before TEXT,
            version_after TEXT,
            checksum_before TEXT,
            checksum_after TEXT,
            actor TEXT DEFAULT 'system',
            details TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS plate_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id TEXT NOT NULL UNIQUE,
            last_check TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unknown',
            version TEXT,
            checksum TEXT,
            drift_detected INTEGER DEFAULT 0,
            corruption_detected INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            last_error TEXT,
            details TEXT DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_usage_plate ON plate_usage(plate_id);
        CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON plate_usage(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_plate ON plate_audit(plate_id);
        CREATE INDEX IF NOT EXISTS idx_audit_event ON plate_audit(event_type);
        CREATE INDEX IF NOT EXISTS idx_health_status ON plate_health(status);
    """)


# ─── PlateMonitor ─────────────────────────────────────────


class PlateMonitor:
    """Monitor and audit plate usage, health, and drift."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else MONITOR_DB
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            _init_schema(self._conn)
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ─── Usage Tracking ───────────────────────────────────

    def log_usage(
        self,
        plate_id: str,
        operation: str,
        user_id: str = "unknown",
        duration_ms: int = 0,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> int:
        """Log a plate usage event.

        Args:
            plate_id: The plate ID that was used
            operation: The operation performed (render, validate, destroy, etc.)
            user_id: Who performed the operation
            duration_ms: How long the operation took
            success: Whether the operation succeeded
            details: Additional details about the usage

        Returns:
            The ID of the inserted usage record
        """
        now = datetime.now(UTC).isoformat()
        cursor = self.conn.execute(
            """INSERT INTO plate_usage
               (plate_id, operation, user_id, timestamp, duration_ms, success, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                plate_id,
                operation,
                user_id,
                now,
                duration_ms,
                1 if success else 0,
                json.dumps(details or {}),
            ),
        )
        self.conn.commit()
        log.debug("Logged usage: %s/%s by %s", plate_id, operation, user_id)
        return cursor.lastrowid or 0

    def get_usage_stats(
        self,
        plate_id: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get usage statistics for plates.

        Args:
            plate_id: Optional plate ID to filter by
            since: ISO timestamp to filter from
            limit: Maximum number of records to return

        Returns:
            List of usage records
        """
        query = "SELECT * FROM plate_usage WHERE 1=1"
        params: list[Any] = []

        if plate_id:
            query += " AND plate_id = ?"
            params.append(plate_id)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_usage_summary(
        self,
        plate_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a summary of usage statistics.

        Args:
            plate_id: Optional plate ID to filter by

        Returns:
            Summary dict with counts and stats
        """
        if plate_id:
            cursor = self.conn.execute(
                """SELECT
                    COUNT(*) as total_uses,
                    SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failed,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(DISTINCT operation) as unique_operations
                   FROM plate_usage WHERE plate_id = ?""",
                (plate_id,),
            )
        else:
            cursor = self.conn.execute(
                """SELECT
                    COUNT(*) as total_uses,
                    SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failed,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(DISTINCT operation) as unique_operations,
                    COUNT(DISTINCT plate_id) as unique_plates
                   FROM plate_usage""",
            )

        row = cursor.fetchone()
        if not row:
            return {}

        result = dict(row)

        # Get top operations
        if plate_id:
            op_cursor = self.conn.execute(
                """SELECT operation, COUNT(*) as count
                   FROM plate_usage WHERE plate_id = ?
                   GROUP BY operation ORDER BY count DESC LIMIT 10""",
                (plate_id,),
            )
        else:
            op_cursor = self.conn.execute(
                """SELECT operation, COUNT(*) as count
                   FROM plate_usage
                   GROUP BY operation ORDER BY count DESC LIMIT 10""",
            )
        result["top_operations"] = [dict(r) for r in op_cursor.fetchall()]

        return result

    # ─── Audit Trail ──────────────────────────────────────

    def log_audit(
        self,
        plate_id: str,
        event_type: str,
        actor: str = "system",
        version_before: str | None = None,
        version_after: str | None = None,
        checksum_before: str | None = None,
        checksum_after: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> int:
        """Log an audit event for a plate.

        Args:
            plate_id: The plate ID
            event_type: Type of event (create, update, destroy, promote, verify)
            actor: Who performed the action
            version_before: Version before the change
            version_after: Version after the change
            checksum_before: Checksum before the change
            checksum_after: Checksum after the change
            details: Additional details

        Returns:
            The ID of the inserted audit record
        """
        now = datetime.now(UTC).isoformat()
        cursor = self.conn.execute(
            """INSERT INTO plate_audit
               (plate_id, event_type, timestamp, version_before, version_after,
                checksum_before, checksum_after, actor, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                plate_id,
                event_type,
                now,
                version_before,
                version_after,
                checksum_before,
                checksum_after,
                actor,
                json.dumps(details or {}),
            ),
        )
        self.conn.commit()
        log.info("Audit: %s/%s by %s", plate_id, event_type, actor)
        return cursor.lastrowid or 0

    def get_audit_trail(
        self,
        plate_id: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get the audit trail for plates.

        Args:
            plate_id: Optional plate ID to filter by
            event_type: Optional event type to filter by
            since: ISO timestamp to filter from
            limit: Maximum number of records

        Returns:
            List of audit records
        """
        query = "SELECT * FROM plate_audit WHERE 1=1"
        params: list[Any] = []

        if plate_id:
            query += " AND plate_id = ?"
            params.append(plate_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ─── Health Checks ────────────────────────────────────

    def health_check(
        self,
        plate_id: str,
    ) -> dict[str, Any]:
        """Run a health check on a specific plate.

        Checks for:
        - Plate existence and loadability
        - Version drift (compared to last known version)
        - Checksum drift (content changed unexpectedly)
        - Corruption (missing required fields, parse errors)

        Args:
            plate_id: The plate ID to check

        Returns:
            Health report dict
        """
        now = datetime.now(UTC).isoformat()
        errors: list[str] = []
        warnings: list[str] = []
        drift_detected = False
        corruption_detected = False

        # Check plate exists and loads
        loaded = load_plate(plate_id)
        if not loaded:
            corruption_detected = True
            errors.append(f"Plate '{plate_id}' not found or failed to load")

            self._update_health(
                plate_id=plate_id,
                status="corrupted",
                version="unknown",
                checksum="",
                drift_detected=False,
                corruption_detected=True,
                error_count=len(errors),
                last_error=errors[-1] if errors else "",
                details={"errors": errors, "warnings": warnings},
            )
            return {
                "plate_id": plate_id,
                "status": "corrupted",
                "healthy": False,
                "errors": errors,
                "warnings": warnings,
                "drift_detected": False,
                "corruption_detected": True,
                "checked_at": now,
            }

        meta, raw, path = loaded

        # Check for version drift
        last_health = self._get_last_health(plate_id)
        if last_health and last_health.get("version"):
            if last_health["version"] != meta.version:
                drift_detected = True
                warnings.append(
                    f"Version drift: was {last_health['version']}, "
                    f"now {meta.version}"
                )

        # Check for checksum drift
        if meta.checksum:
            content = path.read_text()
            if not meta.validate_checksum(content):
                drift_detected = True
                warnings.append("Checksum mismatch — content has drifted")

        # Check for corruption
        if not meta.id:
            corruption_detected = True
            errors.append("Missing plate.id")
        if not meta.version:
            corruption_detected = True
            errors.append("Missing plate.version")

        # Check file integrity
        try:
            file_size = path.stat().st_size
            if file_size == 0:
                corruption_detected = True
                errors.append("Plate file is empty")
        except OSError as exc:
            corruption_detected = True
            errors.append(f"Cannot read plate file: {exc}")

        # Determine overall status
        if corruption_detected:
            status = "corrupted"
        elif drift_detected:
            status = "drifted"
        elif errors:
            status = "degraded"
        else:
            status = "healthy"

        healthy = not corruption_detected and not drift_detected and len(errors) == 0

        # Update health record
        self._update_health(
            plate_id=plate_id,
            status=status,
            version=meta.version,
            checksum=meta.checksum,
            drift_detected=drift_detected,
            corruption_detected=corruption_detected,
            error_count=len(errors),
            last_error=errors[-1] if errors else "",
            details={"errors": errors, "warnings": warnings},
        )

        # Log audit event for health check
        self.log_audit(
            plate_id=plate_id,
            event_type="health_check",
            actor="system",
            version_before=last_health.get("version") if last_health else None,
            version_after=meta.version,
            checksum_before=last_health.get("checksum") if last_health else None,
            checksum_after=meta.checksum,
            details={"status": status, "healthy": healthy},
        )

        log.info(
            "Health check for %s: %s (drift=%s, corruption=%s)",
            plate_id, status, drift_detected, corruption_detected,
        )

        return {
            "plate_id": plate_id,
            "version": meta.version,
            "status": status,
            "healthy": healthy,
            "errors": errors,
            "warnings": warnings,
            "drift_detected": drift_detected,
            "corruption_detected": corruption_detected,
            "checked_at": now,
        }

    def health_check_all(self) -> list[dict[str, Any]]:
        """Run health checks on all discovered plates."""
        plates = discover_plates()
        results = []
        for pid in plates:
            result = self.health_check(pid)
            results.append(result)
        return results

    def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of all plate health statuses."""
        cursor = self.conn.execute(
            """SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='healthy' THEN 1 ELSE 0 END) as healthy,
                SUM(CASE WHEN status='drifted' THEN 1 ELSE 0 END) as drifted,
                SUM(CASE WHEN status='corrupted' THEN 1 ELSE 0 END) as corrupted,
                SUM(CASE WHEN status='degraded' THEN 1 ELSE 0 END) as degraded,
                SUM(CASE WHEN status='unknown' THEN 1 ELSE 0 END) as unknown
               FROM plate_health"""
        )
        row = cursor.fetchone()
        base = dict(row) if row else {}

        # Get plates needing attention
        cursor = self.conn.execute(
            """SELECT plate_id, status, version, last_check, error_count
               FROM plate_health
               WHERE status IN ('corrupted', 'drifted', 'degraded')
               ORDER BY error_count DESC LIMIT 20"""
        )
        base["plates_needing_attention"] = [dict(r) for r in cursor.fetchall()]

        return base

    def _get_last_health(self, plate_id: str) -> dict[str, Any] | None:
        """Get the last health record for a plate."""
        cursor = self.conn.execute(
            "SELECT * FROM plate_health WHERE plate_id = ?",
            (plate_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def _update_health(
        self,
        plate_id: str,
        status: str,
        version: str,
        checksum: str,
        drift_detected: bool,
        corruption_detected: bool,
        error_count: int,
        last_error: str,
        details: dict[str, Any],
    ) -> None:
        """Update or insert a health record."""
        now = datetime.now(UTC).isoformat()
        self.conn.execute(
            """INSERT INTO plate_health
               (plate_id, last_check, status, version, checksum,
                drift_detected, corruption_detected, error_count,
                last_error, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(plate_id) DO UPDATE SET
               last_check=excluded.last_check,
               status=excluded.status,
               version=excluded.version,
               checksum=excluded.checksum,
               drift_detected=excluded.drift_detected,
               corruption_detected=excluded.corruption_detected,
               error_count=excluded.error_count,
               last_error=excluded.last_error,
               details=excluded.details""",
            (
                plate_id,
                now,
                status,
                version,
                checksum,
                1 if drift_detected else 0,
                1 if corruption_detected else 0,
                error_count,
                last_error,
                json.dumps(details),
            ),
        )
        self.conn.commit()

    # ─── Reporting ────────────────────────────────────────

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive monitoring report."""
        health_summary = self.get_health_summary()
        usage_summary = self.get_usage_summary()

        # Recent audit events
        recent_audit = self.get_audit_trail(limit=20)

        # Most used plates
        cursor = self.conn.execute(
            """SELECT plate_id, COUNT(*) as use_count
               FROM plate_usage
               GROUP BY plate_id
               ORDER BY use_count DESC LIMIT 10"""
        )
        most_used = [dict(r) for r in cursor.fetchall()]

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "health": health_summary,
            "usage": usage_summary,
            "most_used_plates": most_used,
            "recent_audit_events": recent_audit,
        }


# ─── CLI Integration ──────────────────────────────────────


def add_monitoring_args(parser: Any) -> None:
    """Add monitoring arguments to an argparse parser."""
    parser.add_argument(
        "--monitor-health", type=str, nargs="?", const="all", default=None,
        help="Run health check on a specific plate or 'all'",
    )
    parser.add_argument(
        "--monitor-usage", type=str, nargs="?", const=None, default=None,
        help="Show usage stats for a specific plate or all",
    )
    parser.add_argument(
        "--monitor-audit", type=str, nargs="?", const=None, default=None,
        help="Show audit trail for a specific plate or all",
    )
    parser.add_argument(
        "--monitor-report", action="store_true",
        help="Generate comprehensive monitoring report",
    )


def handle_monitoring_commands(args: Any) -> None:
    """Handle monitoring CLI commands."""
    monitor = PlateMonitor()

    if args.monitor_health:
        if args.monitor_health == "all":
            results = monitor.health_check_all()
        else:
            results = [monitor.health_check(args.monitor_health)]

        for r in results:
            status_icon = {
                "healthy": "OK",
                "drifted": "DRIFT",
                "corrupted": "CORRUPT",
                "degraded": "DEGRADED",
                "unknown": "UNKNOWN",
            }.get(r.get("status", "unknown"), "UNKNOWN")

            print(f"\n  {r['plate_id']}: [{status_icon}]")
            print(f"    Version: {r.get('version', 'unknown')}")
            print(f"    Healthy: {r.get('healthy', False)}")
            for e in r.get("errors", []):
                print(f"    ERROR: {e}")
            for w in r.get("warnings", []):
                print(f"    WARN: {w}")

    if args.monitor_usage:
        if args.monitor_usage == "all":
            stats = monitor.get_usage_summary()
            print(f"\n  Usage Summary:")
            print(f"    Total uses: {stats.get('total_uses', 0)}")
            print(f"    Successful: {stats.get('successful', 0)}")
            print(f"    Failed: {stats.get('failed', 0)}")
            print(f"    Unique plates: {stats.get('unique_plates', 0)}")
            print(f"    Avg duration: {stats.get('avg_duration_ms', 0):.0f}ms")
        else:
            stats = monitor.get_usage_summary(args.monitor_usage)
            print(f"\n  Usage for {args.monitor_usage}:")
            print(f"    Total uses: {stats.get('total_uses', 0)}")
            print(f"    Successful: {stats.get('successful', 0)}")
            print(f"    Failed: {stats.get('failed', 0)}")
            print(f"    Avg duration: {stats.get('avg_duration_ms', 0):.0f}ms")
            print(f"    Top operations:")
            for op in stats.get("top_operations", []):
                print(f"      {op['operation']}: {op['count']}")

    if args.monitor_audit:
        if args.monitor_audit == "all":
            records = monitor.get_audit_trail(limit=50)
        else:
            records = monitor.get_audit_trail(
                plate_id=args.monitor_audit, limit=50
            )

        if not records:
            print("\n  No audit records found.")
        else:
            print(f"\n  Audit Trail ({len(records)} records):")
            for r in records:
                print(
                    f"  [{r['timestamp']}] {r['plate_id']}/{r['event_type']} "
                    f"by {r['actor']}"
                )
                if r.get("version_before") or r.get("version_after"):
                    print(
                        f"    Version: {r.get('version_before', '-')} -> "
                        f"{r.get('version_after', '-')}"
                    )

    if args.monitor_report:
        report = monitor.generate_report()
        print(f"\n  Plate Monitoring Report")
        print(f"  {'=' * 40}")
        print(f"  Generated: {report['generated_at']}")
        print()
        print(f"  Health Summary:")
        h = report.get("health", {})
        print(f"    Total: {h.get('total', 0)}")
        print(f"    Healthy: {h.get('healthy', 0)}")
        print(f"    Drifted: {h.get('drifted', 0)}")
        print(f"    Corrupted: {h.get('corrupted', 0)}")
        print(f"    Degraded: {h.get('degraded', 0)}")
        print()
        print(f"  Usage Summary:")
        u = report.get("usage", {})
        print(f"    Total uses: {u.get('total_uses', 0)}")
        print(f"    Failed: {u.get('failed', 0)}")
        print()
        print(f"  Most Used Plates:")
        for p in report.get("most_used_plates", []):
            print(f"    {p['plate_id']}: {p['use_count']} uses")
        print()
        print(f"  Plates Needing Attention:")
        for p in h.get("plates_needing_attention", []):
            print(f"    {p['plate_id']}: {p['status']} ({p['error_count']} errors)")

    monitor.close()
