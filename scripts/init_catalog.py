#!/usr/bin/env python3
"""Initialize catalog with sample entries."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.catalog import CatalogService, CatalogEntry, SpatialUID, EntryType


def main():
    """Initialize catalog with sample entries."""
    print("🚀 Initializing catalog with sample entries...")
    
    # Initialize catalog service
    catalog = CatalogService()
    
    # Create MCP servers
    lightpanda = CatalogEntry(
        uid=SpatialUID("mcp.browser.lightpanda"),
        type=EntryType.MCP,
        name="Lightpanda MCP",
        description="Browser automation MCP server using Lightpanda",
        metadata={
            "version": "1.0.0",
            "author": "uDos Go",
            "port": 8485,
            "tools": ["navigate", "click", "fill", "screenshot", "extract", "evaluate"],
        },
        relationships=[
            {"type": "related_to", "target": "mcp.browser.playwright", "weight": 0.7},
        ],
    )
    
    playwright = CatalogEntry(
        uid=SpatialUID("mcp.browser.playwright"),
        type=EntryType.MCP,
        name="Playwright MCP",
        description="Browser automation MCP server using Playwright",
        metadata={
            "version": "1.0.0",
            "author": "uDos Go",
            "port": 8486,
            "tools": ["navigate", "click", "fill", "screenshot", "extract", "evaluate", "wait", "close"],
        },
        relationships=[
            {"type": "related_to", "target": "mcp.browser.lightpanda", "weight": 0.7},
        ],
    )
    
    # Create LLM models
    gpt_oss = CatalogEntry(
        uid=SpatialUID("llm.openrouter.gpt-oss-20b"),
        type=EntryType.LLM,
        name="GPT-OSS-20B",
        description="OpenRouter GPT OSS 20B parameter model",
        metadata={
            "provider": "openrouter",
            "context_window": 128000,
            "max_tokens": 4096,
            "pricing": {"input": "0.0001", "output": "0.0003"},
        },
    )
    
    nemotron = CatalogEntry(
        uid=SpatialUID("llm.openrouter.nvidia-nemotron-3"),
        type=EntryType.LLM,
        name="Nemotron 3 Super",
        description="NVIDIA Nemotron 3 Super model via OpenRouter",
        metadata={
            "provider": "openrouter",
            "context_window": 128000,
            "max_tokens": 8192,
            "pricing": {"input": "0.0002", "output": "0.0006"},
        },
    )
    
    # Add entries
    try:
        catalog.add_entry(lightpanda)
        print(f"✅ Added: {lightpanda.name} ({lightpanda.uid})")
    except Exception as e:
        print(f"❌ Error adding entry: {e}")
    
    try:
        catalog.add_entry(playwright)
        print(f"✅ Added: {playwright.name} ({playwright.uid})")
    except Exception as e:
        print(f"❌ Error adding entry: {e}")
    
    try:
        catalog.add_entry(gpt_oss)
        print(f"✅ Added: {gpt_oss.name} ({gpt_oss.uid})")
    except Exception as e:
        print(f"❌ Error adding entry: {e}")
    
    try:
        catalog.add_entry(nemotron)
        print(f"✅ Added: {nemotron.name} ({nemotron.uid})")
    except Exception as e:
        print(f"❌ Error adding entry: {e}")
    
    # Show stats
    stats = catalog.get_stats()
    print(f"\n📊 Catalog Statistics:")
    print(f"   Total Entries: {stats['total_entries']}")
    print(f"   By Type: {stats['by_type']}")
    print(f"   Total Relationships: {stats['total_relationships']}")

    print("\n✨ Catalog initialization complete!")


if __name__ == "__main__":
    main()
