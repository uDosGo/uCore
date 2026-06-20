"""API routes for Container lifecycle management."""
from __future__ import annotations

from aiohttp import web
from app.models.container import ContainerRuntime, ContainerStatus
from app.services.container_manager import ContainerManager

# Shared service instance
_mgr = ContainerManager()


def register_container_routes(app: web.Application) -> None:
    app.router.add_get("/api/containers", list_containers)
    app.router.add_post("/api/containers", create_container)
    app.router.add_get("/api/containers/{container_id}", get_container)
    app.router.add_delete("/api/containers/{container_id}", delete_container)
    app.router.add_post("/api/containers/{container_id}/start", start_container)
    app.router.add_post("/api/containers/{container_id}/stop", stop_container)
    app.router.add_get("/api/containers/{container_id}/logs", get_logs)


async def list_containers(request: web.Request) -> web.Response:
    """GET /api/containers — list containers, optionally ?status=running"""
    status_filter = request.query.get("status")
    if status_filter:
        try:
            st = ContainerStatus(status_filter)
            containers = _mgr.list_containers(status=st)
        except ValueError:
            return web.json_response({"error": f"Invalid status: {status_filter}"}, status=400)
    else:
        containers = _mgr.list_containers()
    return web.json_response({
        "containers": [c.model_dump(mode="json") for c in containers],
        "count": len(containers),
    })


async def create_container(request: web.Request) -> web.Response:
    """POST /api/containers — create a new container"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    name = data.get("name")
    if not name:
        return web.json_response({"error": "name is required"}, status=400)

    runtime_str = data.get("runtime", "python")
    try:
        rt = ContainerRuntime(runtime_str)
    except ValueError:
        return web.json_response({"error": f"Invalid runtime: {runtime_str}"}, status=400)

    container = _mgr.create_container(
        name=name,
        runtime=rt,
        image=data.get("image"),
        dependencies=data.get("dependencies"),
        env_vars=data.get("env_vars"),
        command=data.get("command"),
    )
    return web.json_response(container.model_dump(mode="json"), status=201)


async def get_container(request: web.Request) -> web.Response:
    """GET /api/containers/{container_id}"""
    container_id = request.match_info.get("container_id")
    container = _mgr.get_container(container_id)
    if container is None:
        return web.json_response({"error": "Container not found"}, status=404)
    return web.json_response(container.model_dump(mode="json"))


async def delete_container(request: web.Request) -> web.Response:
    """DELETE /api/containers/{container_id}"""
    container_id = request.match_info.get("container_id")
    if _mgr.delete_container(container_id):
        return web.json_response({"status": "deleted"}, status=200)
    return web.json_response({"error": "Container not found"}, status=404)


async def start_container(request: web.Request) -> web.Response:
    """POST /api/containers/{container_id}/start"""
    container_id = request.match_info.get("container_id")
    container = _mgr.start_container(container_id)
    if container is None:
        return web.json_response({"error": "Container not found"}, status=404)
    return web.json_response(container.model_dump(mode="json"))


async def stop_container(request: web.Request) -> web.Response:
    """POST /api/containers/{container_id}/stop"""
    container_id = request.match_info.get("container_id")
    container = _mgr.stop_container(container_id)
    if container is None:
        return web.json_response({"error": "Container not found"}, status=404)
    return web.json_response(container.model_dump(mode="json"))


async def get_logs(request: web.Request) -> web.Response:
    """GET /api/containers/{container_id}/logs?tail=10"""
    container_id = request.match_info.get("container_id")
    tail_str = request.query.get("tail")
    try:
        tail = int(tail_str) if tail_str else None
    except ValueError:
        tail = None
    logs = _mgr.get_container_logs(container_id, tail=tail)
    if logs is None:
        return web.json_response({"error": "Container not found"}, status=404)
    return web.json_response({
        "container_id": container_id,
        "logs": logs,
        "count": len(logs),
    })
