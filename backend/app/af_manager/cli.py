#!/usr/bin/env python3
"""AppFlowy Unified Knowledge Manager — CLI entry point.

Usage:
  python -m app.af_manager.cli import --all          # Import all vaults
  python -m app.af_manager.cli import --source Vault  # Import single vault
  python -m app.af_manager.cli watch                  # Watch mode (requires watchdog)
  python -m app.af_manager.cli status                 # Show sync status
  python -m app.af_manager.cli setup                  # Configure AppFlowy data path
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("af_manager")


def cmd_import(args: argparse.Namespace) -> None:
    """Run vault import."""
    from .config import load_config
    from .sync import run_import, scan_vault

    config = load_config()

    if args.source:
        # Import single source
        sources = [s for s in config.get("sources", []) if s["name"] == args.source]
        if not sources:
            log.error("Source '%s' not found in config", args.source)
            sys.exit(1)
        config["sources"] = sources

    def progress(msg: str, pct: int):
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r  [{bar}] {pct}% — {msg}", end="", flush=True)
        if pct >= 100:
            print()

    result = run_import(config, progress_callback=progress)
    print()
    print("  ✅ Import complete!")
    print(f"     Created: {result['total_imported']}")
    print(f"     Updated: {result['total_updated']}")
    print(f"     Errors:  {result['total_errors']}")
    print(f"     DB:      {result['db_path']}")
    print()


def cmd_watch(args: argparse.Namespace) -> None:
    """Watch vault directories for changes (continuous sync)."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        log.error(
            "watchdog not installed. Install with: pip install watchdog"
        )
        sys.exit(1)

    from .config import load_config, get_source_dirs
    from .sync import run_import

    config = load_config()

    class VaultSyncHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            if event.src_path.endswith((".md", ".json", ".yaml", ".yml")):
                log.info("Change detected: %s — re-running import", event.src_path)
                run_import(config)

    observer = Observer()
    sources = get_source_dirs(config)
    for source in sources:
        path = Path(source["local_path"]).expanduser()
        if path.exists():
            log.info("Watching: %s", path)
            observer.schedule(VaultSyncHandler(), str(path), recursive=True)

    if not observer._watchers:
        log.warning("No source directories to watch")
        sys.exit(1)

    log.info("File watcher started. Press Ctrl+C to stop.")
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def cmd_status(args: argparse.Namespace) -> None:
    """Show sync status."""
    from .config import load_config, get_source_dirs
    from .sync import scan_vault

    config = load_config()
    sources = get_source_dirs(config)

    print()
    print("  ═══════════════════════════════════════")
    print("  AppFlowy Unified Knowledge Manager")
    print("  ═══════════════════════════════════════")
    print()

    total_files = 0
    for source in sources:
        records = scan_vault(source["local_path"], tags=source.get("tags"))
        total_files += len(records)
        print(f"  📂 {source['name']}:")
        print(f"     Path:   {source['local_path']}")
        print(f"     Files:  {len(records)}")
        print(f"     Tags:   {', '.join(source.get('tags', []))}")
        print()

    print(f"  Total files across all vaults: {total_files}")
    print()


def cmd_setup(args: argparse.Namespace) -> None:
    """Configure AppFlowy to use a custom data directory.

    This modifies the AppFlowy appflowy.yaml config to point to a
    central data directory specified in sync_config.yaml.
    """
    from .config import load_config

    config = load_config()
    data_dir = config.get("appflowy", {}).get("data_dir", "")

    if not data_dir:
        log.error("No data_dir configured in sync_config.yaml")
        sys.exit(1)

    target_path = Path(data_dir).expanduser()
    appflowy_config = Path.home() / "Library/Application Support/com.appflowy.appflowy.flutter/appflowy.yaml"

    if args.dry_run:
        print(f"  Would configure AppFlowy data dir: {target_path}")
        print(f"  Target config: {appflowy_config}")
        return

    # Check or create appflowy.yaml
    if appflowy_config.exists():
        import yaml
        with open(appflowy_config) as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    cfg["appflowy_data_dir"] = str(target_path)

    appflowy_config.parent.mkdir(parents=True, exist_ok=True)
    with open(appflowy_config, "w") as f:
        yaml.dump(cfg, f)

    print(f"  ✅ Configured AppFlowy data dir: {target_path}")
    print(f"     Config file: {appflowy_config}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AppFlowy Unified Knowledge Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # import
    p_import = sub.add_parser("import", help="Import vaults into AppFlowy")
    p_import.add_argument("--all", action="store_true", help="Import all sources")
    p_import.add_argument("--source", type=str, help="Import a specific source by name")

    # watch
    p_watch = sub.add_parser("watch", help="Watch vaults for changes (continuous sync)")

    # status
    p_status = sub.add_parser("status", help="Show vault sync status")

    # setup
    p_setup = sub.add_parser("setup", help="Configure AppFlowy data path")
    p_setup.add_argument("--dry-run", action="store_true", help="Show what would be done")

    args = parser.parse_args()

    if args.command == "import":
        if args.source:
            cmd_import(args)
        elif args.all:
            cmd_import(args)
        else:
            print("Use --all to import all vaults, or --source NAME for a specific vault")
            sys.exit(1)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "setup":
        cmd_setup(args)


if __name__ == "__main__":
    main()
