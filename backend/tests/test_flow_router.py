from __future__ import annotations

import pytest

from app.services.flow_router import FlowLLMRouter


@pytest.mark.asyncio
async def test_flow_router_basic():
    """Test basic Flow-LLM Router functionality."""
    # Create router
    router = FlowLLMRouter()

    # Test routing a simple task
    result = await router.route_task(
        task_description="Fix a typo in README",
        complexity="simple",
        context_size="small",
        risk_level="low",
    )

    # Verify result structure
    assert "success" in result
    assert result["success"] is True
    assert "routing" in result
    assert "provider" in result["routing"]
    assert "model" in result["routing"]
    assert "estimated_cost" in result["routing"]

    # Test routing a complex task
    result = await router.route_task(
        task_description="Refactor the authentication system to use OAuth2",
        complexity="complex",
        context_size="large",
        risk_level="high",
    )

    assert "success" in result
    assert result["success"] is True
    assert "routing" in result
    assert "provider" in result["routing"]
    assert "model" in result["routing"]


@pytest.mark.asyncio
async def test_flow_router_analytics():
    """Test Flow-LLM Router analytics."""
    router = FlowLLMRouter()

    # Get initial analytics
    analytics = router.get_analytics()
    assert "total_requests" in analytics
    assert analytics["total_requests"] == 0

    # Make some routing decisions
    for i in range(5):
        await router.route_task(f"Test task {i}")

    # Get updated analytics
    analytics = router.get_analytics()
    assert analytics["total_requests"] == 5

    # Test history
    history = router.get_routing_history(limit=10)
    assert len(history) == 5


@pytest.mark.asyncio
async def test_flow_router_clear():
    """Test Flow-LLM Router history clearing."""
    router = FlowLLMRouter()

    # Add some history
    for i in range(3):
        await router.route_task(f"Test task {i}")

    assert len(router.get_routing_history()) == 3

    # Clear history
    router.clear_history()

    assert len(router.get_routing_history()) == 0
