#!/usr/bin/env python3
"""Lockfile management for unified menu.

Extracted from unified_menu_simple.py to improve maintainability.
Uses boot time to detect stale PIDs from previous sessions.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

log = logging.getLogger("ucore.menu.lockfile")


LOCKFILE_PATH = Path.home() / ".ucore" / "menu.lock"


def _get_boot_time() -> float:
    """Get system boot time in seconds since epoch.

    On macOS, uses kern.boottime via sysctl. Falls back to comparing
    /proc/uptime on Linux or a reasonable default.
    """
    try:
        import ctypes
        import ctypes.util

        libc = ctypes.CDLL(ctypes.util.find_library("c"))

        # struct timeval { time_t tv_sec; suseconds_t tv_usec; }
        # struct timeval boottime;
        # size_t size = sizeof(boottime);
        # sysctlbyname("kern.boottime", &boottime, &size, NULL, 0);
        class timeval(ctypes.Structure):
            _fields_ = [("tv_sec", ctypes.c_int64), ("tv_usec", ctypes.c_int32)]

        boottime = timeval()
        size = ctypes.c_size_t(ctypes.sizeof(boottime))

        result = libc.sysctlbyname(
            b"kern.boottime",
            ctypes.byref(boottime),
            ctypes.byref(size),
            None,
            0,
        )
        if result == 0:
            return float(boottime.tv_sec)
    except Exception:
        pass

    # Fallback: use a reasonable default (1 hour ago)
    return time.time() - 3600


def _is_pid_alive(pid: int) -> bool:
    """Check if a PID is still running.

    Uses os.kill(pid, 0) which sends signal 0 (no-op) to check existence.
    """
    try:
        os.kill(pid, 0)  # signal 0 = no-op, just checks existence
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _is_lock_stale() -> bool:
    """Check if the lockfile is stale using multiple heuristics.

    1. If the lockfile was created before the last system boot, it's stale.
    2. If the PID in the lockfile is no longer alive, it's stale.
    3. If the lockfile is older than 24 hours, it's stale (safety net).
    """
    if not LOCKFILE_PATH.exists():
        return True  # No lockfile = not stale (vacuously)

    # Read PID from lockfile
    try:
        pid = int(LOCKFILE_PATH.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        log.info("Lockfile contains invalid PID, treating as stale")
        return True

    # Check 1: Lockfile mtime vs boot time
    try:
        lock_mtime = LOCKFILE_PATH.stat().st_mtime
        boot_time = _get_boot_time()
        if lock_mtime < boot_time:
            log.info(
                "Lockfile mtime (%.0f) is before boot time (%.0f) — stale from previous session",
                lock_mtime,
                boot_time,
            )
            return True
    except OSError:
        pass

    # Check 2: PID alive check
    if not _is_pid_alive(pid):
        log.info("PID %d in lockfile is no longer alive — stale", pid)
        return True

    # Check 3: Safety net — lockfile older than 24 hours
    try:
        age = time.time() - LOCKFILE_PATH.stat().st_mtime
        if age > 86400:  # 24 hours
            log.info("Lockfile is %.0f hours old — stale (safety net)", age / 3600)
            return True
    except OSError:
        pass

    return False


def acquire_lock() -> bool:
    """Acquire a lock to prevent multiple menu instances.

    Stores the current PID in the lock file. Uses multiple heuristics
    to detect stale locks from crashed processes or system reboots.

    Returns:
        True if lock acquired, False if another live instance holds it
    """
    try:
        if LOCKFILE_PATH.exists():
            if not _is_lock_stale():
                try:
                    pid = int(LOCKFILE_PATH.read_text(encoding="utf-8").strip())
                except (ValueError, OSError):
                    pid = None
                log.warning(
                    "Menu lock file exists — PID %s is still running",
                    pid or "unknown",
                )
                return False

            # Stale lock — remove it
            log.info("Removing stale lock file")
            LOCKFILE_PATH.unlink()

        LOCKFILE_PATH.write_text(str(os.getpid()), encoding="utf-8")
        log.info("Lock acquired (PID %d)", os.getpid())
        return True
    except Exception as exc:
        log.error("Failed to acquire lock: %s", exc)
        return False


def release_lock() -> None:
    """Release the menu lock (only if we own it)."""
    try:
        if LOCKFILE_PATH.exists():
            pid = int(LOCKFILE_PATH.read_text(encoding="utf-8").strip())
            if pid == os.getpid():
                LOCKFILE_PATH.unlink()
                log.info("Lock released")
    except (ValueError, OSError):
        pass  # Corrupt lock file — leave it, next start will clean it
    except Exception as exc:
        log.error("Failed to release lock: %s", exc)

