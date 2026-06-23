"""Secret Store API — Manage API keys and credentials through the UI."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess

from aiohttp import web

from app.core.settings import settings
from app.secret.store import get_store

log = logging.getLogger("ucore.api.secrets")

PROVIDER_SECRET_KEYS = [
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "DEEPSEEK_API_KEY",
    "GROQ_API_KEY",
    "GITHUB_TOKEN",
    "HUGGINGFACE_TOKEN",
    "REPLICATE_API_KEY",
    "COHERE_API_KEY",
    "AI21_API_KEY",
    "XAI_API_KEY",
    "TOGETHER_API_KEY",
    "PERPLEXITY_API_KEY",
    "FIREWORKS_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "UCORE_OLLAMA_MODEL",
    "UCORE_OLLAMA_FALLBACK_MODEL",
    # OAuth current + future-ready entries.
    "GITHUB_OAUTH_CLIENT_ID",
    "GITHUB_OAUTH_CLIENT_SECRET",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "DISCORD_OAUTH_CLIENT_ID",
    "DISCORD_OAUTH_CLIENT_SECRET",
    "SLACK_OAUTH_CLIENT_ID",
    "SLACK_OAUTH_CLIENT_SECRET",
    "NOTION_OAUTH_CLIENT_ID",
    "NOTION_OAUTH_CLIENT_SECRET",
    "LINEAR_OAUTH_CLIENT_ID",
    "LINEAR_OAUTH_CLIENT_SECRET",
]


def _mask(value: str) -> str:
    if len(value) > 8:
        return value[:4] + "****" + value[-4:]
    return "****"


def _actor_from_request(request: web.Request) -> str:
    header_actor = request.headers.get("X-Actor", "").strip()
    if header_actor:
        return header_actor
    peer = request.remote or "unknown"
    return f"api:{peer}"


def _dotenv_candidates() -> list[Path]:
    cwd = Path.cwd()
    candidates = [
        cwd / ".env",
        cwd / "backend" / ".env",
        settings.config_dir / ".env",
        Path.home() / ".config" / "udos" / ".env",
    ]
    seen: set[str] = set()
    deduped: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    return deduped


def _is_provider_secret_key(name: str) -> bool:
    return (
        name in PROVIDER_SECRET_KEYS
        or name.endswith("_API_KEY")
        or "_OAUTH_" in name
        or name in {"GITHUB_TOKEN", "HUGGINGFACE_TOKEN"}
    )


def _resolve_dotenv_target(path_str: str) -> Path | None:
    raw = (path_str or "").strip()
    if not raw:
        return None

    expanded = Path(raw).expanduser()
    requested = expanded if expanded.is_absolute() else (Path.cwd() / expanded)
    requested_norm = str(requested.resolve(strict=False))

    allowed = {str(p.resolve(strict=False)) for p in _dotenv_candidates()}
    if requested_norm not in allowed:
        return None
    return requested


def _quote_dotenv_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_store_to_dotenv(
    target: Path,
    store,
    only_missing: bool = True,
) -> tuple[int, int, list[str]]:
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = (
        target.read_text(encoding="utf-8").splitlines()
        if target.exists()
        else []
    )
    key_line_map: dict[str, int] = {}
    pattern = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")

    for idx, line in enumerate(existing_lines):
        match = pattern.match(line)
        if match:
            key_line_map[match.group(1)] = idx

    provider_store = {
        key: val
        for key, val in store._secrets.items()
        if _is_provider_secret_key(key) and bool(val)
    }

    written_keys: list[str] = []
    updated = 0
    added = 0
    lines = list(existing_lines)

    for key in sorted(provider_store.keys()):
        if key in key_line_map:
            if only_missing:
                continue
            line_idx = key_line_map[key]
            lines[line_idx] = (
                f"{key}={_quote_dotenv_value(provider_store[key])}"
            )
            updated += 1
            written_keys.append(key)
            continue

        lines.append(f"{key}={_quote_dotenv_value(provider_store[key])}")
        added += 1
        written_keys.append(key)

    if written_keys:
        text = "\n".join(lines)
        if text and not text.endswith("\n"):
            text += "\n"
        target.write_text(text, encoding="utf-8")

    return added, updated, written_keys


def _parse_dotenv_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return values

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if ((val.startswith('"') and val.endswith('"'))
                    or (val.startswith("'") and val.endswith("'"))):
                val = val[1:-1]
            if key:
                values[key] = val
    except Exception as e:
        log.warning("Failed parsing .env %s: %s", path, e)

    return values


def _load_dotenv_values() -> tuple[dict[str, str], list[str]]:
    merged: dict[str, str] = {}
    sources: list[str] = []
    for path in _dotenv_candidates():
        parsed = _parse_dotenv_file(path)
        if parsed:
            merged.update(parsed)
            sources.append(str(path))
    return merged, sources


def _build_provider_matrix(store) -> tuple[list[dict], list[str]]:
    dotenv_map, dotenv_sources = _load_dotenv_values()

    known = set(PROVIDER_SECRET_KEYS)
    known.update(store._secrets.keys())
    known.update(k for k in os.environ.keys() if "_API_KEY" in k)
    known.update(k for k in os.environ.keys() if "_OAUTH_" in k)
    known.update(k for k in dotenv_map.keys() if "_API_KEY" in k)
    known.update(k for k in dotenv_map.keys() if "_OAUTH_" in k)

    rows: list[dict] = []
    for name in sorted(known):
        store_val = store.get(name)
        env_val = os.environ.get(name)
        dotenv_val = dotenv_map.get(name)

        if env_val:
            value = env_val
            source = "env"
        elif store_val:
            value = store_val
            source = "store"
        elif dotenv_val:
            value = dotenv_val
            source = "dotenv"
        else:
            value = ""
            source = "missing"

        rows.append({
            "name": name,
            "present": bool(value),
            "missing": not bool(value),
            "source": source,
            "in_store": bool(store_val),
            "in_env": bool(env_val),
            "in_dotenv": bool(dotenv_val),
            "masked": _mask(value) if value else "",
        })

    return rows, dotenv_sources


async def handle_list_secrets(request: web.Request) -> web.Response:
    """GET /api/secrets — list all stored secrets (masked)."""
    store = get_store()
    secrets = store.list()
    return web.json_response({"secrets": secrets, "count": len(secrets)})


async def handle_get_secret(request: web.Request) -> web.Response:
    """GET /api/secrets/{name} — get a secret value."""
    name = request.match_info.get("name", "")
    store = get_store()
    value = store.get(name, actor=_actor_from_request(request))
    if value is None:
        return web.json_response(
            {"error": f"Secret '{name}' not found"},
            status=404,
        )
    env_val = os.environ.get(name)
    return web.json_response({
        "name": name,
        "value": value,
        "from_env": bool(env_val),
        "masked": _mask(value),
    })


async def handle_set_secret(request: web.Request) -> web.Response:
    """POST /api/secrets/{name} — set a secret value.

    Body: {"value": "sk-or-v1-..."}
    """
    name = request.match_info.get("name", "")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    value = body.get("value", "").strip()
    if not value:
        return web.json_response({"error": "value is required"}, status=400)

    store = get_store()
    store.set(name, value, actor=_actor_from_request(request))
    store.save()

    return web.json_response({
        "name": name,
        "status": "saved",
        "masked": _mask(value),
    })


async def handle_delete_secret(request: web.Request) -> web.Response:
    """DELETE /api/secrets/{name} — delete a secret."""
    name = request.match_info.get("name", "")
    store = get_store()
    deleted = store.delete(name, actor=_actor_from_request(request))
    if not deleted:
        return web.json_response(
            {"error": f"Secret '{name}' not found"},
            status=404,
        )
    store.save()
    return web.json_response({"name": name, "status": "deleted"})


async def handle_list_env_vars(request: web.Request) -> web.Response:
    """GET /api/secrets/env — merged provider vars from store + env + .env."""
    store = get_store()
    env_vars, dotenv_sources = _build_provider_matrix(store)
    return web.json_response({
        "env_vars": env_vars,
        "count": len(env_vars),
        "dotenv_sources": dotenv_sources,
        "dotenv_candidates": [str(p) for p in _dotenv_candidates()],
    })


async def handle_import_from_env(request: web.Request) -> web.Response:
    """POST /api/secrets/import-env.

    Merge missing provider vars into the encrypted store.
    """
    store = get_store()
    env_vars, dotenv_sources = _build_provider_matrix(store)
    dotenv_map, _ = _load_dotenv_values()

    imported: list[str] = []
    for item in env_vars:
        name = item["name"]
        if item["in_store"]:
            continue

        value = os.environ.get(name) or dotenv_map.get(name)
        if value:
            store.set(name, value)
            imported.append(name)

    if imported:
        store.save()

    secrets = store.list()
    return web.json_response({
        "secrets": secrets,
        "count": len(secrets),
        "status": "imported",
        "imported_count": len(imported),
        "imported": imported,
        "dotenv_sources": dotenv_sources,
    })


async def handle_export_to_env(request: web.Request) -> web.Response:
    """POST /api/secrets/export-env.

    Write provider secrets from encrypted store to a chosen .env file.
    Body: {"target": "...", "only_missing": true}
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    target = _resolve_dotenv_target(str(body.get("target", "")))
    if target is None:
        return web.json_response(
            {
                "error": "target must be one of dotenv_candidates",
                "dotenv_candidates": [str(p) for p in _dotenv_candidates()],
            },
            status=400,
        )

    only_missing = bool(body.get("only_missing", True))
    store = get_store()
    added, updated, written_keys = _write_store_to_dotenv(
        target=target,
        store=store,
        only_missing=only_missing,
    )

    return web.json_response({
        "status": "exported",
        "target": str(target),
        "only_missing": only_missing,
        "added_count": added,
        "updated_count": updated,
        "written_count": len(written_keys),
        "written_keys": written_keys,
    })


async def handle_secret_audit(request: web.Request) -> web.Response:
    """GET /api/secrets/audit — list recent secret audit events."""
    raw_limit = request.query.get("limit", "100")
    try:
        limit = max(1, min(int(raw_limit), 1000))
    except ValueError:
        limit = 100

    store = get_store()
    events = store.list_audit(limit=limit)
    return web.json_response({"events": events, "count": len(events)})


async def handle_sync_github(request: web.Request) -> web.Response:
    """POST /api/secrets/sync-github.

    Sync GitHub secret *names* and populate values from payload/env/store where
    available. GitHub does not expose secret plaintext values via CLI/API.
    """
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    actor = _actor_from_request(request)
    repository = str(body.get("repository", "")).strip()
    supplied_values = body.get("secret_values")
    if not isinstance(supplied_values, dict):
        supplied_values = {}

    gh_path = shutil.which("gh")
    if not gh_path:
        return web.json_response(
            {"error": "gh CLI not found in PATH"},
            status=400,
        )

    cmd = [gh_path, "secret", "list", "--json", "name"]
    if repository:
        cmd.extend(["--repo", repository])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return web.json_response(
            {"error": f"gh execution failed: {exc}"},
            status=500,
        )

    if result.returncode != 0:
        return web.json_response(
            {
                "error": "gh secret list failed",
                "exit_code": result.returncode,
                "stderr": (result.stderr or "").strip(),
            },
            status=502,
        )

    try:
        rows = json.loads(result.stdout or "[]")
    except Exception as exc:
        return web.json_response(
            {"error": f"Invalid gh JSON output: {exc}"},
            status=502,
        )

    names: list[str] = []
    for row in rows:
        if isinstance(row, dict) and row.get("name"):
            names.append(str(row["name"]))

    store = get_store()
    imported: list[str] = []
    already_present: list[str] = []
    missing_values: list[str] = []

    for name in sorted(set(names)):
        if store.get(name, actor=actor):
            already_present.append(name)
            continue

        value = supplied_values.get(name) or os.environ.get(name)
        if value:
            store.set(name, str(value), actor=f"{actor}:github-sync")
            imported.append(name)
        else:
            missing_values.append(name)

    if imported:
        store.save()

    return web.json_response(
        {
            "status": "ok",
            "repository": repository or None,
            "listed_count": len(names),
            "imported_count": len(imported),
            "already_present_count": len(already_present),
            "missing_values_count": len(missing_values),
            "imported": imported,
            "already_present": already_present,
            "missing_values": missing_values,
            "note": (
                "GitHub secret plaintext values are not retrievable; "
                "import requires payload/env values."
            ),
        }
    )
