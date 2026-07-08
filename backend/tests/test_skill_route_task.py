"""Tests for the RouteTask skill."""
from __future__ import annotations

import pytest

from app.skills.builtin.route_task import RouteTask


@pytest.mark.asyncio
async def test_route_simple_task():
    skill = RouteTask()
    result = await skill.run(task="fix a typo in README", complexity="simple")
    assert result["success"] is True
    assert result["routing"]["provider"] == "ollama"


@pytest.mark.asyncio
async def test_route_medium_task():
    skill = RouteTask()
    result = await skill.run(task="implement a new REST API endpoint", complexity="medium")
    assert result["success"] is True
    assert result["routing"]["provider"] == "openrouter"


@pytest.mark.asyncio
async def test_route_complex_task():
    skill = RouteTask()
    result = await skill.run(task="fix a security vulnerability in the authentication system",
                              complexity="complex")
    assert result["success"] is True
    assert result["routing"]["model"].startswith("anthropic")


@pytest.mark.asyncio
async def test_route_auto_detect_simple():
    skill = RouteTask()
    result = await skill.run(task="fix typo in readme", complexity="auto")
    assert result["success"] is True
    assert result["analysis"]["detected_complexity"] == "simple"


@pytest.mark.asyncio
async def test_route_auto_detect_medium():
    skill = RouteTask()
    result = await skill.run(task="implement a new feature with database migration and API endpoint",
                              complexity="auto")
    assert result["success"] is True
    assert result["analysis"]["detected_complexity"] in ("medium", "complex")


@pytest.mark.asyncio
async def test_route_auto_detect_complex():
    skill = RouteTask()
    result = await skill.run(task="fix a race condition in the distributed authentication system",
                              complexity="auto")
    assert result["success"] is True
    assert result["analysis"]["detected_complexity"] == "complex"


@pytest.mark.asyncio
async def test_route_no_task():
    skill = RouteTask()
    result = await skill.run(task="")
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_route_large_context():
    skill = RouteTask()
    result = await skill.run(task="analyze this large dataset", complexity="simple",
                              context_size="large")
    assert result["success"] is True
    assert "gemini" in result["routing"]["model"].lower()


@pytest.mark.asyncio
async def test_route_invalid_complexity_defaults():
    skill = RouteTask()
    result = await skill.run(task="simple task", complexity="invalid")
    assert result["success"] is True
    assert result["analysis"]["detected_complexity"] == "simple"


@pytest.mark.asyncio
async def test_route_strategy_structure():
    skill = RouteTask()
    result = await skill.run(task="write unit tests", complexity="medium")
    assert "strategy" in result
    assert "tier_allocations" in result["strategy"]
    tiers = result["strategy"]["tier_allocations"]
    assert "simple" in tiers
    assert "medium" in tiers
    assert "complex" in tiers
