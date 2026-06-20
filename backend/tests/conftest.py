"""uCore test configuration."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ is on sys.path so `from app import ...` works
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
