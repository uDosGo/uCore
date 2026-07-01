"""Developer API — local repo discovery and workspace file listing."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aiohttp import web

from app.core.settings import settings

ALLOWED_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".txt", ".csv", ".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".sh", ".toml"}
IGNORED_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
MAX_PREVIEW_BYTES = 200_000


def _git_output(repo_path: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _repo_file_count(repo_path: Path, limit: int = 500) -> int:
    count = 0
    for path in repo_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            count += 1
            if count >= limit:
                return count
    return count


def _repo_path(repo_name: str) -> Path:
    repo_path = (settings.udos_root.expanduser() / repo_name).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise FileNotFoundError(repo_name)
    return repo_path


def _safe_file_path(repo_name: str, relative_path: str) -> Path:
    repo_path = _repo_path(repo_name)
    file_path = (repo_path / relative_path).resolve()
    if repo_path not in file_path.parents and file_path != repo_path:
        raise ValueError("Path escapes repository root")
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(relative_path)
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")
    return file_path


def _list_repos() -> list[dict]:
    repos: list[dict] = []
    root = settings.udos_root.expanduser()
    if not root.exists():
        return repos

    for child in sorted(root.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir() or not (child / ".git").exists():
            continue

        branch = _git_output(child, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        status_lines = _git_output(child, "status", "--porcelain").splitlines()
        remote = _git_output(child, "remote", "get-url", "origin") or "No remote"
        changes = len([line for line in status_lines if line.strip()])
        repos.append({
            "id": child.name,
            "name": child.name,
            "path": str(child),
            "branch": branch,
            "status": "clean" if changes == 0 else "modified",
            "changes": changes,
            "remote": remote,
            "fileCount": _repo_file_count(child),
        })

    return repos


def _list_repo_files(repo_name: str, limit: int = 250) -> list[dict]:
    repo_path = _repo_path(repo_name)

    files: list[dict] = []
    for path in repo_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        rel_path = path.relative_to(repo_path)
        stat = path.stat()
        files.append({
            "id": len(files) + 1,
            "name": str(rel_path),
            "type": path.suffix.lstrip(".").lower() or "file",
            "size": stat.st_size,
            "updatedAt": path.stat().st_mtime,
            "tags": [path.suffix.lstrip(".").lower()] if path.suffix else [],
            "binder": repo_name,
        })
        if len(files) >= limit:
            break

    files.sort(key=lambda item: item["updatedAt"], reverse=True)
    for file in files:
        file["updatedAt"] = __import__("datetime").datetime.fromtimestamp(file["updatedAt"]).isoformat()
    return files


def _status_label(code: str) -> str:
    code = code.strip()
    if code in {"A", "??"}:
        return "added"
    if code == "D":
        return "deleted"
    return "modified"


def _review_summary(code: str, path: str) -> str:
    if code == "??":
        return f"Untracked file ready to stage: {path}"
    if "R" in code:
        return f"Renamed in working tree: {path}"
    if "D" in code:
        return f"Deleted from working tree: {path}"
    if "A" in code:
        return f"Added in working tree: {path}"
    return f"Modified in working tree: {path}"


def _list_repo_review(repo_name: str) -> list[dict[str, Any]]:
    repo_path = _repo_path(repo_name)
    status_output = _git_output(repo_path, "status", "--porcelain")
    numstat_output = _git_output(repo_path, "diff", "--numstat")

    line_counts: dict[str, int] = {}
    for line in numstat_output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_raw, deleted_raw, file_path = parts
        try:
            added = 0 if added_raw == "-" else int(added_raw)
            deleted = 0 if deleted_raw == "-" else int(deleted_raw)
        except ValueError:
            added = 0
            deleted = 0
        line_counts[file_path] = added + deleted

    reviews: list[dict[str, Any]] = []
    for raw in status_output.splitlines():
        if not raw.strip():
            continue
        code = raw[:2]
        path = raw[2:].lstrip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status = _status_label(code)
        reviews.append({
            "file": path,
            "status": status,
            "lines": line_counts.get(path, 0),
            "summary": _review_summary(code, path),
        })

    return reviews


def _get_repo_file_preview(repo_name: str, relative_path: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    truncated = False
    if len(raw.encode("utf-8")) > MAX_PREVIEW_BYTES:
        raw = raw[:MAX_PREVIEW_BYTES]
        truncated = True
    stat = file_path.stat()
    return {
        "repo": repo_name,
        "path": relative_path,
        "content": raw,
        "type": file_path.suffix.lstrip(".").lower() or "file",
        "size": stat.st_size,
        "truncated": truncated,
        "updatedAt": __import__("datetime").datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def _build_untracked_diff(repo_name: str, relative_path: str) -> str:
    preview = _get_repo_file_preview(repo_name, relative_path)
    header = [
        f"diff --git a/{relative_path} b/{relative_path}",
        "new file mode 100644",
        "index 0000000..0000000",
        "--- /dev/null",
        f"+++ b/{relative_path}",
        "@@ -0,0 +1 @@",
    ]
    body = [f"+{line}" for line in preview["content"].splitlines()]
    if not body:
        body = ["+"]
    return "\n".join(header + body)


def _get_repo_file_diff(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    status_output = _git_output(repo_path, "status", "--porcelain", "--", relative_path)
    status_code = status_output[:2].strip() if status_output else ""

    if status_code == "??":
        diff_text = _build_untracked_diff(repo_name, relative_path)
    else:
        diff_text = _git_output(repo_path, "diff", "--", relative_path)
        if not diff_text:
            diff_text = _git_output(repo_path, "diff", "--cached", "--", relative_path)

    return {
        "repo": repo_name,
        "path": relative_path,
        "status": _status_label(status_code) if status_code else "modified",
        "diff": diff_text,
        "hasDiff": bool(diff_text.strip()),
    }


def _save_repo_file(repo_name: str, relative_path: str, content: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    file_path.write_text(content, encoding="utf-8")
    return _get_repo_file_preview(repo_name, relative_path)


def _stage_repo_file(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "add", relative_path],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git add failed: {result.stderr}")
    return {"repo": repo_name, "path": relative_path, "action": "staged", "success": True}


def _unstage_repo_file(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "reset", "HEAD", relative_path],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git reset failed: {result.stderr}")
    return {"repo": repo_name, "path": relative_path, "action": "unstaged", "success": True}


def _commit_repo_files(repo_name: str, message: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", message],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"git commit failed: {result.stderr}")
    success = result.returncode == 0
    return {
        "repo": repo_name,
        "action": "commit",
        "success": success,
        "message": message,
        "output": result.stdout or result.stderr,
    }


async def handle_start_developer(request: web.Request) -> web.Response:
    """Start the developer server (DevMode).
    
    DevMode is internal dev ops - when active:
    - Dev server (Vite) runs on port 5174
    - Developer Surface is accessible at /developer
    - DevMode icon appears in global toolbar
    """
    import subprocess
    from pathlib import Path
    from app.core.logging import log
    
    try:
        # Check if already running
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:5174/developer", method="HEAD")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status < 500:
                    return web.json_response({
                        "success": True,
                        "message": "Developer server already running",
                        "dev_mode": {"active": True}
                    })
        except Exception:
            pass
        
        # Start Vite dev server
        frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
        if not frontend_dir.exists():
            return web.json_response({
                "success": False,
                "error": "Frontend directory not found"
            }, status=404)
        
        log.info("🚀 [DEVMODE] Starting developer server (internal dev ops)")
        
        # Start in background
        subprocess.Popen(
            ["pnpm", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return web.json_response({
            "success": True,
            "message": "Developer server starting",
            "dev_mode": {"active": True, "starting": True}
        })
    except Exception as e:
        log.error(f"❌ [DEVMODE] Failed to start developer server: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_stop_developer(request: web.Request) -> web.Response:
    """Stop the developer server (DevMode).
    
    Logs the stop operation for audit trail.
    """
    import subprocess
    from app.core.logging import log
    
    try:
        log.info("🛑 [DEVMODE] Stopping developer server (internal dev ops)")
        
        # Find and kill Vite process
        subprocess.run(
            ["pkill", "-f", "vite.*5174"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return web.json_response({
            "success": True,
            "message": "Developer server stopped",
            "dev_mode": {"active": False}
        })
    except Exception as e:
        log.error(f"❌ [DEVMODE] Failed to stop developer server: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_developer_status(request: web.Request) -> web.Response:
    """Get current DevMode status.
    
    Returns whether the developer server is running and accessible.
    """
    import urllib.request
    from app.core.logging import log
    
    try:
        req = urllib.request.Request("http://localhost:5174/developer", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as resp:
            active = resp.status < 500
            if active:
                log.debug("✅ [DEVMODE] Developer server is active")
            return web.json_response({
                "active": active,
                "description": "Internal dev ops - Developer Surface active",
                "icon_visible": active
            })
    except Exception:
        log.debug("⏸️  [DEVMODE] Developer server is inactive")
        return web.json_response({
            "active": False,
            "description": "Internal dev ops - Developer Surface inactive",
            "icon_visible": False
        })


async def handle_list_repos(request: web.Request) -> web.Response:
    return web.json_response({"repos": _list_repos(), "root": str(settings.udos_root)})


async def handle_list_repo_files(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        files = _list_repo_files(repo_name)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    return web.json_response({"repo": repo_name, "files": files})


async def handle_get_repo_file_preview(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _get_repo_file_preview(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_update_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    if not isinstance(data.get("content"), str):
        return web.json_response({"error": "Missing string field: content"}, status=400)

    try:
        payload = _save_repo_file(repo_name, relative_path, data["content"])
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_get_repo_file_diff(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _get_repo_file_diff(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_list_repo_review(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        review = _list_repo_review(repo_name)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    return web.json_response({"repo": repo_name, "review": review})


async def handle_stage_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _stage_repo_file(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except (ValueError, RuntimeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_unstage_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _unstage_repo_file(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except (ValueError, RuntimeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_commit_repo_files(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    message = data.get("message", "Update files").strip()
    if not message:
        message = "Update files"
    try:
        payload = _commit_repo_files(repo_name, message)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    except RuntimeError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)
