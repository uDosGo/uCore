#!/usr/bin/env python3
"""Simple macOS clipboard watcher for Snackbar clipboard buffer.

Polls pbpaste at a small interval and appends changed text content into the
clipboard buffer feed. Intended for local launchd or manual run.
"""
from __future__ import annotations

import argparse
import time

from app.clipboard.clipboard_buffer import (
    add_clipboard_item,
    cleanup_history,
    read_clipboard_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch macOS clipboard and spool changes")
    parser.add_argument("--interval", type=float, default=0.8, help="Polling interval seconds")
    parser.add_argument("--max-items", type=int, default=500, help="Maximum non-pinned history items")
    parser.add_argument("--max-days", type=int, default=30, help="Maximum age for non-pinned items")
    parser.add_argument("--source", default="user_copy", help="Source label for captured entries")
    args = parser.parse_args()

    last = None
    while True:
        try:
            current = read_clipboard_text()
            if current and current != last:
                last = current
                add_clipboard_item(
                    source=args.source,
                    type="text",
                    content=current.strip("\n"),
                    metadata={"watcher": "pbpaste-poll"},
                    pinned=False,
                )
                cleanup_history(max_items=args.max_items, max_days=args.max_days)
        except KeyboardInterrupt:
            return 0
        except Exception:
            # Keep watcher resilient; transient pbpaste errors should not crash it.
            pass
        time.sleep(max(0.2, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
