"""Local paths for generated project memory."""
from __future__ import annotations

from pathlib import Path

from app.core.settings import settings

PROJECT_ROOT = settings.udos_root / "uCore"
PRIVATE_MEMORY_DIR = settings.memory_dir / "uCore"

WISDOM_PATH = PRIVATE_MEMORY_DIR / "wisdom.md"
FIELDNOTES_PATH = PRIVATE_MEMORY_DIR / "fieldnotes.md"

WISDOM_TEMPLATE_PATH = PROJECT_ROOT / "docs/templates/wisdom.md"
FIELDNOTES_TEMPLATE_PATH = PROJECT_ROOT / "docs/templates/fieldnotes.md"

LEGACY_WISDOM_PATH = PROJECT_ROOT / "wisdom.md"
LEGACY_FIELDNOTES_PATH = PROJECT_ROOT / "fieldnotes.md"


def writable_wisdom_path() -> Path:
    """Return the private writable wisdom path, creating its parent."""
    WISDOM_PATH.parent.mkdir(parents=True, exist_ok=True)
    return WISDOM_PATH


def readable_wisdom_path() -> Path:
    """Prefer private wisdom, then local legacy, then the tracked template."""
    for path in (WISDOM_PATH, LEGACY_WISDOM_PATH, WISDOM_TEMPLATE_PATH):
        if path.exists():
            return path
    return WISDOM_PATH
