"""Identity Module — uDos Identity System
=======================================
Every running instance needs a unique identity so services, surfaces, and skills
know who they're talking to.

Concepts:
  - User ID: Auto-generated uDos format ID (UDOS-YYYYMMDD-XXXXXX)
    Unique per device, generated once. Stable across restarts.
  - Codeword: Local human-readable name for network identification.
  - Installation ID: Which device/instance, e.g. "macbook-pro-m1"
  - Session ID: Current running session (ephemeral), auto-generated at server start

Storage:
  - ~/.config/udos/identity.json — User ID + Codeword + Installation ID
  - ~/.local/share/udos/session.json — Current session (created at server start)

Spec: UDN-IDENTITY-API-001
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "udos"
LOCAL_DIR = Path.home() / ".local" / "share" / "udos"
IDENTITY_FILE = CONFIG_DIR / "identity.json"
SESSION_FILE = LOCAL_DIR / "session.json"


def generate_udos_id() -> str:
    """Generate a uDos format User ID:
      UDOS-YYYYMMDD-XXXXXX

    Where XXXXXX is a 6-char hex fingerprint derived from hostname + machine.
    Deterministic for a given device.
    """
    today = datetime.now(UTC).strftime("%Y%m%d")
    hostname = socket.gethostname().lower()
    machine = __import__("platform").machine().lower()
    fingerprint = hashlib.sha256(f"{hostname}-{machine}".encode()).hexdigest()[:6].upper()
    return f"UDOS-{today}-{fingerprint}"


def generate_install_id() -> str:
    """Generate an installation ID from hostname + platform + machine."""
    import platform as _platform
    hostname = socket.gethostname().lower().replace(" ", "-")
    machine = _platform.machine().lower()
    system = _platform.system().lower()
    unique_suffix = uuid.uuid5(uuid.NAMESPACE_DNS, f"{hostname}-{machine}-{system}").hex[:8]
    return f"{hostname}-{machine}-{unique_suffix}"


# ─── Data Classes ───────────────────────────────────────────────────────

class Identity:
    """Persistent identity — User ID + Codeword + Installation ID."""

    def __init__(self, user_id: str = "", codeword: str = "", install_id: str = ""):
        self.user_id = user_id
        self.codeword = codeword
        self.install_id = install_id

    def to_dict(self) -> dict:
        return {"user_id": self.user_id, "codeword": self.codeword, "install_id": self.install_id}

    @classmethod
    def from_dict(cls, data: dict) -> Identity:
        return cls(user_id=data.get("user_id", ""), codeword=data.get("codeword", ""), install_id=data.get("install_id", ""))

    def is_valid(self) -> bool:
        return bool(self.user_id) and bool(self.install_id)


class Session:
    """Ephemeral session — created at server start."""

    def __init__(self, session_id: str = "", started_at: str = ""):
        self.session_id = session_id
        self.started_at = started_at

    def to_dict(self) -> dict:
        return {"session_id": self.session_id, "started_at": self.started_at}

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(session_id=data.get("session_id", ""), started_at=data.get("started_at", ""))


# ─── Load / Save ────────────────────────────────────────────────────────

def load_identity() -> Identity:
    if not IDENTITY_FILE.exists():
        return Identity()
    try:
        return Identity.from_dict(json.loads(IDENTITY_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return Identity()


def save_identity(identity: Identity) -> bool:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        IDENTITY_FILE.write_text(json.dumps(identity.to_dict(), indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def load_session() -> Session | None:
    if not SESSION_FILE.exists():
        return None
    try:
        return Session.from_dict(json.loads(SESSION_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def save_session(session: Session) -> bool:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        SESSION_FILE.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def create_session() -> Session:
    return Session(session_id=str(uuid.uuid4()), started_at=datetime.now(UTC).isoformat())


def get_or_create_session() -> Session:
    session = load_session()
    if not session:
        session = create_session()
        save_session(session)
    return session


def get_full_identity() -> dict:
    """Return the complete identity info for API responses and log tagging."""
    import platform as _platform
    identity = load_identity()
    session = get_or_create_session()
    return {
        "user_id": identity.user_id,
        "codeword": identity.codeword,
        "install_id": identity.install_id,
        "session_id": session.session_id,
        "started_at": session.started_at,
        "hostname": socket.gethostname(),
        "platform": _platform.system().lower(),
        "platform_version": _platform.version(),
        "machine": _platform.machine(),
    }


# ─── Init on first run ─────────────────────────────────────────────────

def ensure_identity() -> Identity:
    """Ensure identity exists, auto-initializing if needed."""
    identity = load_identity()
    if not identity.is_valid():
        identity = Identity(
            user_id=generate_udos_id(),
            codeword=os.environ.get("USER", "uCore"),
            install_id=generate_install_id(),
        )
        save_identity(identity)
    return identity


# ─── CLI ────────────────────────────────────────────────────────────────

def cmd_show() -> None:
    """Show current identity (CLI-friendly)."""
    identity = load_identity()
    session = get_or_create_session()
    import platform as _platform
    print(f"\n{'─' * 50}")
    print("  uDos Identity")
    print(f"{'─' * 50}")
    if identity.is_valid():
        print(f"  User ID:         {identity.user_id}")
        print(f"  Codeword:        {identity.codeword or '(not set)'}")
        print(f"  Installation ID: {identity.install_id}")
    else:
        print("  ⚠️  Not initialized. Run: system.identity")
    print(f"  Session ID:      {session.session_id}")
    print(f"  Started At:      {session.started_at}")
    print(f"  Hostname:        {socket.gethostname()}")
    print(f"  Platform:        {_platform.system()} ({_platform.machine()})")
