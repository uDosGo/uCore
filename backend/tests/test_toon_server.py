from __future__ import annotations

from app.mcp.toon.server import TOONContextServer


def test_toon_server_basic():
    """Test basic TOON server functionality."""
    # Create server with in-memory database
    server = TOONContextServer()

    # Test TOON encoding
    content = "# Hello World\n\nThis is a test markdown document.\n\n- Item 1\n- Item 2\n- Item 3"

    toon_content = server.toon_encode(content, "markdown")

    # Verify TOON content is generated
    assert toon_content is not None
    assert len(toon_content) > 0
    assert "SECTION:" in toon_content or "TEXT:" in toon_content

    # Test JSON encoding
    json_content = '{"name": "test", "value": 42, "items": ["a", "b", "c"]}'
    toon_json = server.toon_encode(json_content, "json")

    assert toon_json is not None
    assert len(toon_json) > 0
    assert "name=" in toon_json or "value=" in toon_json

    # Test caching
    cached = server.get(content, "markdown")
    assert cached is None  # Should be None before setting

    server.set(content, toon_content, "markdown")

    cached = server.get(content, "markdown")
    assert cached is not None
    assert cached.toon_content == toon_content


def test_toon_compression_ratio():
    """Test TOON compression ratio calculation."""
    server = TOONContextServer()

    original = "This is a test string that should be compressed"
    toon = "TEXT: This is a test string..."

    ratio = server._calculate_compression_ratio(original, toon)
    assert ratio > 0.0
    assert ratio < 1.0


def test_toon_stats():
    """Test TOON server statistics."""
    server = TOONContextServer()

    stats = server.stats()
    assert "entries" in stats
    assert "requests" in stats
    assert "hits" in stats
    assert "misses" in stats
    assert "writes" in stats
    assert "hit_ratio" in stats


def test_toon_clear():
    """Test TOON server cache clearing."""
    server = TOONContextServer()

    # Add some content
    content = "test content"
    toon_content = server.toon_encode(content)
    server.set(content, toon_content)

    # Verify cache has entries
    stats = server.stats()
    assert stats["entries"] > 0

    # Clear cache
    server.clear()

    # Verify cache is empty
    stats = server.stats()
    assert stats["entries"] == 0
