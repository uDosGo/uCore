"""API routes for Surface CRUD operations."""
from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from app.models.surface import SurfaceState, SurfaceType
from app.services.surface_manager import SurfaceManager
from app.services.surface_runtime import get_surface_runtime_manager

log = logging.getLogger("ucore")

# Shared service instance (will be injected properly later)
_surfaces = SurfaceManager()


def register_surface_routes(app: web.Application) -> None:
    app.router.add_get("/api/surfaces", list_surfaces)
    app.router.add_post("/api/surfaces", create_surface)
    app.router.add_get("/api/surfaces/{surface_id}", get_surface)
    app.router.add_patch("/api/surfaces/{surface_id}", update_surface)
    app.router.add_delete("/api/surfaces/{surface_id}", delete_surface)
    app.router.add_post("/api/surfaces/{surface_id}/start", start_surface)
    app.router.add_post("/api/surfaces/{surface_id}/stop", stop_surface)
    app.router.add_post("/api/surfaces/{surface_id}/restart", restart_surface)
    app.router.add_post("/api/surfaces/{surface_id}/repair", repair_surface)
    app.router.add_post("/api/surfaces/{surface_id}/debug", debug_surface)


async def list_surfaces(request: web.Request) -> web.Response:
    """GET /api/surfaces — list all surfaces, optionally ?type=prose"""
    type_filter = request.query.get("type")
    if type_filter:
        try:
            st = SurfaceType(type_filter)
            surfaces = _surfaces.list_by_type(st)
        except ValueError:
            return web.json_response({"error": f"Invalid type: {type_filter}"}, status=400)
    else:
        surfaces = _surfaces.list_surfaces()
    return web.json_response({
        "surfaces": [s.model_dump(mode="json") for s in surfaces],
        "count": len(surfaces),
    })


async def create_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces — create a new surface"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    name = data.get("name")
    if not name:
        return web.json_response({"error": "name is required"}, status=400)

    type_str = data.get("type", "prose")
    try:
        st = SurfaceType(type_str)
    except ValueError:
        return web.json_response({"error": f"Invalid type: {type_str}"}, status=400)

    surface = _surfaces.create_surface(
        name=name,
        type=st,
        metadata=data.get("metadata"),
        parent_id=data.get("parent_id"),
        position=data.get("position"),
    )
    return web.json_response(surface.model_dump(mode="json"), status=201)


async def get_surface(request: web.Request) -> web.Response:
    """GET /api/surfaces/{surface_id}"""
    surface_id = request.match_info.get("surface_id")
    surface = _surfaces.get_surface(surface_id)
    if surface is None:
        return web.json_response({"error": "Surface not found"}, status=404)
    return web.json_response(surface.model_dump(mode="json"))


async def update_surface(request: web.Request) -> web.Response:
    """PATCH /api/surfaces/{surface_id}"""
    surface_id = request.match_info.get("surface_id")
    surface = _surfaces.get_surface(surface_id)
    if surface is None:
        return web.json_response({"error": "Surface not found"}, status=404)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    updated = _surfaces.update_surface(
        surface_id=surface_id,
        name=data.get("name"),
        metadata=data.get("metadata"),
        position=data.get("position"),
    )
    return web.json_response(updated.model_dump(mode="json") if updated else {}, status=200)


async def delete_surface(request: web.Request) -> web.Response:
    """DELETE /api/surfaces/{surface_id}"""
    surface_id = request.match_info.get("surface_id")
    if _surfaces.delete_surface(surface_id):
        return web.json_response({"status": "deleted"}, status=200)
    return web.json_response({"error": "Surface not found"}, status=404)


async def start_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces/{surface_id}/start"""
    surface_id = request.match_info.get("surface_id")
    runtime = get_surface_runtime_manager()
    surface = _surfaces.get_surface(surface_id)

    if surface is None:
        runtime_result = runtime.start(surface_id)
        if runtime_result is None:
            return web.json_response({"error": "Surface not found"}, status=404)
        status = 200 if runtime_result.get("success") else 500
        return web.json_response(runtime_result, status=status)

    runtime_id = str(surface.metadata.get("runtime_id", "")).strip()
    if runtime_id:
        runtime_result = runtime.start(runtime_id)
        if runtime_result is not None:
            new_state = (
                SurfaceState.RUNNING
                if runtime_result.get("success")
                else SurfaceState.ERROR
            )
            updated = _surfaces.transition_state(surface_id, new_state)
            status = 200 if runtime_result.get("success") else 500
            payload = {
                **(
                    updated.model_dump(mode="json")
                    if updated is not None
                    else surface.model_dump(mode="json")
                ),
                "runtime": runtime_result,
            }
            return web.json_response(payload, status=status)

    transitioned = _surfaces.transition_state(surface_id, SurfaceState.RUNNING)
    if transitioned is None:
        return web.json_response({"error": "Surface not found"}, status=404)
    return web.json_response(transitioned.model_dump(mode="json"))


async def stop_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces/{surface_id}/stop"""
    surface_id = request.match_info.get("surface_id")
    runtime = get_surface_runtime_manager()
    surface = _surfaces.get_surface(surface_id)

    if surface is None:
        runtime_result = runtime.stop(surface_id)
        if runtime_result is None:
            return web.json_response({"error": "Surface not found"}, status=404)
        status = 200 if runtime_result.get("success") else 409
        return web.json_response(runtime_result, status=status)

    transitioned = _surfaces.transition_state(surface_id, SurfaceState.STOPPED)
    if transitioned is None:
        return web.json_response({"error": "Surface not found"}, status=404)

    runtime_id = str(surface.metadata.get("runtime_id", "")).strip()
    if runtime_id:
        runtime_result = runtime.stop(runtime_id)
        if runtime_result is not None:
            status = 200 if runtime_result.get("success") else 409
            payload = {
                **transitioned.model_dump(mode="json"),
                "runtime": runtime_result,
            }
            return web.json_response(payload, status=status)

    return web.json_response(transitioned.model_dump(mode="json"))


async def restart_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces/{surface_id}/restart — stop then start."""
    surface_id = request.match_info.get("surface_id")
    runtime = get_surface_runtime_manager()
    surface = _surfaces.get_surface(surface_id)

    if surface is None:
        runtime_result = runtime.restart(surface_id)
        if runtime_result is None:
            return web.json_response({"error": "Surface not found"}, status=404)
        status = 200 if runtime_result.get("success") else 500
        return web.json_response(runtime_result, status=status)

    runtime_id = str(surface.metadata.get("runtime_id", "")).strip()
    if runtime_id:
        runtime_result = runtime.restart(runtime_id)
        if runtime_result is not None:
            new_state = (
                SurfaceState.RUNNING
                if runtime_result.get("success")
                else SurfaceState.ERROR
            )
            updated = _surfaces.transition_state(surface_id, new_state)
            status = 200 if runtime_result.get("success") else 500
            payload = {
                **(
                    updated.model_dump(mode="json")
                    if updated is not None
                    else surface.model_dump(mode="json")
                ),
                "runtime": runtime_result,
                "action": "restart",
            }
            return web.json_response(payload, status=status)

    stopped = _surfaces.transition_state(surface_id, SurfaceState.STOPPED)
    if stopped is None:
        return web.json_response({"error": "Surface not found during restart"}, status=404)

    await asyncio.sleep(0.5)

    started = _surfaces.transition_state(surface_id, SurfaceState.RUNNING)
    if started is None:
        return web.json_response({"error": "Surface not found during restart"}, status=404)

    log.info("Surface %s restarted", surface_id)
    return web.json_response({
        **started.model_dump(mode="json"),
        "action": "restart",
        "message": f"Surface {surface_id} restarted successfully",
    })


async def repair_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces/{surface_id}/repair — diagnostics and fix."""
    surface_id = request.match_info.get("surface_id")
    surface = _surfaces.get_surface(surface_id)
    if surface is None:
        return web.json_response({"error": "Surface not found"}, status=404)

    issues = []
    fixes = []

    if not surface.name:
        issues.append("Surface has no name")
        fixed = _surfaces.update_surface(surface_id, name=f"Surface-{surface_id[:8]}")
        if fixed:
            fixes.append("Assigned default name")

    if surface.state == SurfaceState.ERROR:
        issues.append("Surface is in ERROR state")
        fixed = _surfaces.transition_state(surface_id, SurfaceState.STOPPED)
        if fixed:
            fixes.append("Reset to STOPPED state")

    if not isinstance(surface.metadata, dict):
        issues.append("Metadata is not a valid dict")
        fixed = _surfaces.update_surface(surface_id, metadata={})
        if fixed:
            fixes.append("Reset metadata to empty dict")

    if surface.position is not None and surface.position < 0:
        issues.append("Position is negative")
        fixed = _surfaces.update_surface(surface_id, position=0)
        if fixed:
            fixes.append("Reset position to 0")

    return web.json_response({
        **surface.model_dump(mode="json"),
        "action": "repair",
        "diagnostics": {"issues": issues, "fixes": fixes, "healthy": len(issues) == 0},
    })


async def debug_surface(request: web.Request) -> web.Response:
    """POST /api/surfaces/{surface_id}/debug — health diagnostics."""
    surface_id = request.match_info.get("surface_id")
    surface = _surfaces.get_surface(surface_id)
    if surface is None:
        return web.json_response({"error": "Surface not found"}, status=404)

    checks = {
        "exists": True,
        "has_name": bool(surface.name),
        "valid_state": surface.state.value,
        "valid_type": surface.type.value,
        "has_metadata": isinstance(surface.metadata, dict),
        "metadata_keys": list(surface.metadata.keys()) if isinstance(surface.metadata, dict) else [],
        "has_parent": surface.parent_id is not None,
        "position": surface.position,
    }

    healthy = all([checks["has_name"], checks["has_metadata"]])
    return web.json_response({
        "surface_id": surface_id,
        "action": "debug",
        "healthy": healthy,
        "checks": checks,
        "surface": surface.model_dump(mode="json"),
    })
