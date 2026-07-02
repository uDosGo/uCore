#!/usr/bin/env python3
"""Demonstration script for the optimized workflow features.

This script shows how to use the TOON Context Optimization and Flow-LLM Router
features to reduce token waste and improve cost efficiency.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


async def demo_toon_optimization():
    """Demonstrate TOON context optimization."""
    print("\n=== TOON Context Optimization Demo ===\n")
    
    # Import TOON server
    from app.mcp.toon.server import TOONContextServer
    
    # Create server
    toon_server = TOONContextServer()
    
    # Test content
    markdown_content = """# Project Requirements

- Implement user authentication
- Add role-based access control
- Create API endpoints for CRUD operations
- Add unit tests for all endpoints
- Deploy to production environment

## Technical Details

- Use Python 3.12 with FastAPI
- PostgreSQL database with async support
- Redis for caching
- Docker for containerization
- GitHub Actions for CI/CD
"""
    
    print("Original markdown content size:", len(markdown_content), "bytes")
    
    # Convert to TOON format
    toon_content = toon_server.toon_encode(markdown_content, "markdown")
    print("TOON content size:", len(toon_content), "bytes")
    
    # Calculate compression ratio
    compression_ratio = len(toon_content) / len(markdown_content) if len(markdown_content) > 0 else 1.0
    print(f"Compression ratio: {compression_ratio:.2%}")
    
    # Show sample TOON content
    print("\nSample TOON content:")
    print(toon_content[:200] + "..." if len(toon_content) > 200 else toon_content)
    
    # Test caching
    print("\nTesting TOON caching...")
    toon_server.set(markdown_content, toon_content, "markdown")
    cached = toon_server.get(markdown_content, "markdown")
    print(f"Cache hit: {cached is not None}")
    
    # Get stats
    stats = toon_server.stats()
    print(f"TOON cache stats: {stats['entries']} entries, {stats['hit_ratio']:.2%} hit ratio")


async def demo_flow_router():
    """Demonstrate Flow-LLM Router."""
    print("\n=== Flow-LLM Router Demo ===\n")
    
    # Import Flow-LLM Router
    from app.services.flow_router import FlowLLMRouter
    
    # Create router
    router = FlowLLMRouter()
    
    # Test routing decisions
    tasks = [
        "Fix a typo in README",
        "Implement user authentication",
        "Refactor the authentication system to use OAuth2",
        "Analyze security vulnerabilities in the codebase",
    ]
    
    for i, task in enumerate(tasks):
        print(f"Task {i+1}: {task}")
        
        # Route the task
        result = await router.route_task(task)
        
        if result.get("success"):
            routing = result["routing"]
            print(f"  → Provider: {routing['provider']}")
            print(f"  → Model: {routing['model']}")
            print(f"  → Estimated cost: ${routing['estimated_cost']:.4f}")
            print(f"  → Reason: {routing['reason']}")
        else:
            print(f"  → Error: {result.get('error', 'Unknown error')}")
        print()
    
    # Get analytics
    analytics = router.get_analytics()
    print(f"Flow Router Analytics:")
    print(f"  Total requests: {analytics['total_requests']}")
    print(f"  Cost savings: ${analytics['cost_savings']:.4f}")
    print(f"  Token savings: {analytics['token_savings']} tokens")
    print(f"  Provider distribution: {analytics['provider_distribution']}")
    
    # Get history
    history = router.get_routing_history(limit=3)
    print(f"\nRecent routing history:")
    for i, entry in enumerate(history):
        print(f"  {i+1}. {entry['task_description'][:50]}... → {entry['selected_provider']}/{entry['selected_model']}")


async def main():
    """Main demo function."""
    print("uCore Optimized Workflow Demo")
    print("=" * 50)
    
    await demo_toon_optimization()
    await demo_flow_router()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
