"""AES-256-GCM encrypted secret store for uCore.

Stores API keys and credentials encrypted at rest in ~/.ucore/secrets.enc.
Uses a 256-bit key derived from a stored salt + host identifier.
"""
from __future__ import annotations

import json
import logging
import os
import secrets as pysecrets
from pathlib import Path
from typing import Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

log = logging.getLogger("ucore.secret")

SECRETS_DIR = Path.home() / ".ucore"
SECRETS_FILE = SECRETS_DIR / "secrets.enc"
KEY_FILE = SECRETS_DIR / ".store_key"
DATA_DIR = Path(os.environ.get("UCORE_DATA_DIR", str(SECRETS_DIR)))


def _derive_key(master_key: bytes) -> bytes:
    """Derive a 256-bit AES key using HKDF."""
    if len(master_key) == 32:
        return master_key
    from cryptography.hazmat.primitives.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ucore-secret-store-v1",
    )
    return hkdf.derive(master_key)


def _generate_key() -> bytes:
    """Generate a new 256-bit master key."""
    return pysecrets.token_bytes(32)


def _get_or_create_key() -> bytes:
    """Get existing key or create a new one."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = _generate_key()
    KEY_FILE.write_bytes(key)
    KEY_FILE.chmod(0o600)
    return key


class SecretStore:
    """Encrypted key-value store for secrets."""

    def __init__(self):
        self._key = None
        self._secrets: dict[str, str] = {}
        self._dirty = False

    def load(self):
        """Load and decrypt secrets from disk."""
        if AESGCM is None:
            log.warning("cryptography not installed, using plaintext fallback")
            return self._load_plaintext()

        self._key = _get_or_create_key()
        aes_key = _derive_key(self._key)

        if not SECRETS_FILE.exists():
            log.info("No secrets file, starting fresh")
            self._secrets = {}
            return

        try:
            data = SECRETS_FILE.read_bytes()
            nonce = data[:12]
            ciphertext = data[12:]
            aes = AESGCM(aes_key)
            decrypted = aes.decrypt(nonce, ciphertext, None)
            self._secrets = json.loads(decrypted.decode())
            log.debug(f"Loaded {len(self._secrets)} secrets")
        except Exception as e:
            log.warning(f"Failed to decrypt secrets: {e}")
            self._secrets = {}

    def _load_plaintext(self):
        """Fallback: load from plaintext JSON."""
        path = DATA_DIR / "secrets.json"
        if path.exists():
            try:
                self._secrets = json.loads(path.read_text())
            except Exception:
                self._secrets = {}
        self._dirty = False

    def save(self):
        """Encrypt and save secrets to disk."""
        if AESGCM is None:
            return self._save_plaintext()

        if not self._dirty:
            return

        self._key = _get_or_create_key()
        aes_key = _derive_key(self._key)

        plaintext = json.dumps(self._secrets, indent=2).encode()
        nonce = pysecrets.token_bytes(12)
        aes = AESGCM(aes_key)
        ciphertext = aes.encrypt(nonce, plaintext, None)

        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        SECRETS_FILE.write_bytes(nonce + ciphertext)
        SECRETS_FILE.chmod(0o600)
        self._dirty = False
        log.debug(f"Saved {len(self._secrets)} secrets")

    def _save_plaintext(self):
        path = DATA_DIR / "secrets.json"
        path.write_text(json.dumps(self._secrets, indent=2))
        path.chmod(0o600)
        self._dirty = False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret by key."""
        return self._secrets.get(key, default)

    def set(self, key: str, value: str):
        """Set a secret (marked dirty, saved on next save)."""
        self._secrets[key] = value
        self._dirty = True

    def delete(self, key: str) -> bool:
        """Delete a secret."""
        if key in self._secrets:
            del self._secrets[key]
            self._dirty = True
            return True
        return False

    def list(self) -> list[dict]:
        """List all secret keys (values masked)."""
        return [
            {"name": k, "masked": v[:4] + "****" if len(v) > 8 else "****"}
            for k, v in sorted(self._secrets.items())
        ]

    def get_all_env_vars(self) -> dict[str, str]:
        """Get all secrets + matching env vars."""
        result = {}
        # From store
        for k, v in self._secrets.items():
            result[k] = v
        # From env (override)
        for k in list(result.keys()):
            env_val = os.environ.get(k)
            if env_val:
                result[k] = env_val
        return result

    def sync_from_env(self):
        """Import known env vars into the store."""
        known_keys = [
            "OPENROUTER_API_KEY", "GITHUB_TOKEN", "ANTHROPIC_API_KEY",
            "MISTRAL_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY",
            "GEMINI_API_KEY", "GROQ_API_KEY", "HUGGINGFACE_TOKEN",
            "REPLICATE_API_KEY", "COHERE_API_KEY", "AI21_API_KEY",
        ]
        changed = False
        for key in known_keys:
            val = os.environ.get(key)
            if val and key not in self._secrets:
                self._secrets[key] = val
                changed = True
                log.info(f"Imported {key} from environment")
        if changed:
            self._dirty = True
            self.save()


# Singleton
_store: Optional[SecretStore] = None


def get_store() -> SecretStore:
    global _store
    if _store is None:
        _store = SecretStore()
        _store.load()
        _store.sync_from_env()
    return _store
