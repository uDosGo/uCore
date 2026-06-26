#!/usr/bin/env python3
"""Verification script for the optimized workflow features.

This script verifies that the TOON Context Optimization and Flow-LLM Router
features are working correctly by making API calls to the uCore backend.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


async def verify_toon_features():
    """Verify TOON Context Optimization features."""
    print("\n=== Verifying TOON Context Optimization Features ===\n")
    
    # Test TOON encode endpoint
    try:
        import urllib.request
        import urllib.parse
        
        # Test data
        test_data = {
            "content": "# Test Document\n\nThis is a test markdown document.",
            "content_type": "markdown"
        }
        
        # Make POST request
        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:8484/api/toon/encode',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get('status') == 'encoded' and 'toon_content' in result:
            print("✅ TOON encode endpoint: OK")
            print(f"   TOON content: {result['toon_content'][:50]}...")
            print(f"   Compression ratio: {result.get('compression_ratio', 'N/A'):.2%}")
        else:
            print("❌ TOON encode endpoint: Failed")
            print(f"   Response: {result}")
            
    except Exception as e:
        print("❌ TOON encode endpoint: Error")
        print(f"   Error: {e}")
    
    # Test TOON stats endpoint
    try:
        req = urllib.request.Request('http://localhost:8484/api/toon/stats')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get('status') == 'ok' and 'stats' in result:
            print("✅ TOON stats endpoint: OK")
            print(f"   Cache entries: {result['stats'].get('entries', 'N/A')}")
            print(f"   Hit ratio: {result['stats'].get('hit_ratio', 'N/A'):.2%}")
        else:
            print("❌ TOON stats endpoint: Failed")
            print(f"   Response: {result}")
            
    except Exception as e:
        print("❌ TOON stats endpoint: Error")
        print(f"   Error: {e}")


async def verify_flow_router_features():
    """Verify Flow-LLM Router features."""
    print("\n=== Verifying Flow-LLM Router Features ===\n")
    
    # Test Flow-LLM Router route endpoint
    try:
        import urllib.request
        import urllib.parse
        
        # Test data
        test_data = {
            "task": "Fix a typo in README"
        }
        
        # Make POST request
        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:8484/api/flow-router/route',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get('status') == 'routed' and 'result' in result:
            routing = result['result'].get('routing', {})
            if 'provider' in routing and 'model' in routing:
                print("✅ Flow-LLM Router route endpoint: OK")
                print(f"   Provider: {routing['provider']}")
                print(f"   Model: {routing['model']}")
                print(f"   Estimated cost: ${routing.get('estimated_cost', 0):.4f}")
            else:
                print("❌ Flow-LLM Router route endpoint: Missing routing info")
                print(f"   Response: {result}")
        else:
            print("❌ Flow-LLM Router route endpoint: Failed")
            print(f"   Response: {result}")
            
    except Exception as e:
        print("❌ Flow-LLM Router route endpoint: Error")
        print(f"   Error: {e}")
    
    # Test Flow-LLM Router analytics endpoint
    try:
        req = urllib.request.Request('http://localhost:8484/api/flow-router/analytics')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get('status') == 'ok' and 'analytics' in result:
            analytics = result['analytics']
            print("✅ Flow-LLM Router analytics endpoint: OK")
            print(f"   Total requests: {analytics.get('total_requests', 'N/A')}")
            print(f"   Cost savings: ${analytics.get('cost_savings', 0):.4f}")
        else:
            print("❌ Flow-LLM Router analytics endpoint: Failed")
            print(f"   Response: {result}")
            
    except Exception as e:
        print("❌ Flow-LLM Router analytics endpoint: Error")
        print(f"   Error: {e}")


async def main():
    """Main verification function."""
    print("uCore Optimized Workflow Features Verification")
    print("=" * 50)
    
    await verify_toon_features()
    await verify_flow_router_features()
    
    print("\n" + "=" * 50)
    print("Verification completed!")


if __name__ == "__main__":
    asyncio.run(main())
