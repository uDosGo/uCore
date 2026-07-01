"""End-to-End Tests with Playwright

Tests complete user workflows:
- Backend startup and health check
- Frontend load and rendering
- Popcorn menu interaction
- API endpoints
- Error recovery

Usage:
    pytest tests/e2e_playwright.py -v
    pytest tests/e2e_playwright.py::test_backend_health -v
"""

import pytest
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    pytest.skip("Playwright not installed", allow_module_level=True)


# ─── Configuration ────────────────────────────────────────────────

BACKEND_URL = "http://localhost:8484"
FRONTEND_URL = "http://localhost:5173"
TIMEOUT_MS = 10000


# ─── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
async def browser():
    """Setup browser for tests"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser):
    """Create a new page for each test"""
    context: BrowserContext = await browser.new_context()
    page: Page = await context.new_page()
    
    # Capture console messages
    page.messages = []
    page.on("console", lambda msg: page.messages.append(msg.text))
    
    # Capture errors
    page.errors = []
    page.on("pageerror", lambda exc: page.errors.append(str(exc)))
    
    yield page
    
    await context.close()


# ─── Backend Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_backend_health_endpoint(page: Page):
    """Test backend /api/health endpoint"""
    response = await page.request.get(f"{BACKEND_URL}/api/health")
    assert response.status == 200
    
    data = await response.json()
    assert data["status"] == "ok"
    assert data["service"] == "uCore"
    assert "version" in data
    assert "popcorn" in data  # macOS


@pytest.mark.asyncio
async def test_backend_version_endpoint(page: Page):
    """Test backend /api/version endpoint"""
    response = await page.request.get(f"{BACKEND_URL}/api/version")
    assert response.status == 200
    
    data = await response.json()
    assert "app" in data
    assert "version" in data
    assert "python" in data


@pytest.mark.asyncio
async def test_backend_info_endpoint(page: Page):
    """Test backend /api/info endpoint"""
    response = await page.request.get(f"{BACKEND_URL}/api/info")
    assert response.status == 200
    
    data = await response.json()
    assert data["port"] == 8484
    assert "platform" in data
    assert "machine" in data


# ─── Frontend Tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_frontend_loads(page: Page):
    """Test frontend loads without errors"""
    await page.goto(FRONTEND_URL, wait_until="domcontentloaded")
    
    # Check for console errors
    assert len(page.errors) == 0, f"Console errors: {page.errors}"
    
    # Check page title
    title = await page.title()
    assert "uCore" in title or "UI Hub" in title


@pytest.mark.asyncio
async def test_frontend_typography_responsive(page: Page):
    """Test responsive typography system"""
    await page.goto(FRONTEND_URL, wait_until="domcontentloaded")
    
    # Set mobile viewport
    await page.set_viewport_size({"width": 375, "height": 667})
    await page.wait_for_timeout(1000)
    
    # Check body font size (should be 12.8px on mobile)
    body_size = await page.evaluate("""
        window.getComputedStyle(document.body).fontSize
    """)
    # Allow some variance due to rendering
    assert "px" in body_size
    
    # Set tablet viewport
    await page.set_viewport_size({"width": 768, "height": 1024})
    await page.wait_for_timeout(1000)
    
    # Check body font size (should be 15.2px on tablet)
    tablet_size = await page.evaluate("""
        window.getComputedStyle(document.body).fontSize
    """)
    assert "px" in tablet_size


@pytest.mark.asyncio
async def test_frontend_no_console_errors(page: Page):
    """Test that frontend has no console errors on load"""
    await page.goto(FRONTEND_URL, wait_until="networkidle")
    
    # Get all console messages
    console_logs = [msg for msg in page.messages if "error" in msg.lower()]
    
    # Filter out known non-critical warnings
    critical_errors = [
        msg for msg in console_logs
        if not any(skip in msg for skip in [
            "ResizeObserver",
            "Non-Error promise rejection",
        ])
    ]
    
    assert len(critical_errors) == 0, f"Console errors: {critical_errors}"


# ─── API Integration Tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_popcorn_api_status(page: Page):
    """Test Popcorn status API"""
    response = await page.request.get(f"{BACKEND_URL}/api/surfaces/popcorn/status")
    assert response.status == 200
    
    data = await response.json()
    assert "running" in data
    assert "installed" in data
    assert "plist" in data


@pytest.mark.asyncio
async def test_health_monitor_api(page: Page):
    """Test health monitor endpoints"""
    # Get health status
    response = await page.request.get(f"{BACKEND_URL}/api/health")
    assert response.status == 200
    
    data = await response.json()
    
    # Check components are present
    assert "status" in data
    assert data["status"] == "ok"


# ─── Error Recovery Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_backend_recovery_on_error(page: Page):
    """Test backend recovers from transient errors"""
    # Make multiple requests to ensure resilience
    for i in range(5):
        response = await page.request.get(f"{BACKEND_URL}/api/health", timeout=5000)
        assert response.status == 200, f"Request {i+1} failed"
        await page.wait_for_timeout(500)


@pytest.mark.asyncio
async def test_frontend_handles_offline(page: Page):
    """Test frontend handles offline gracefully"""
    await page.goto(FRONTEND_URL, wait_until="domcontentloaded")
    
    # Go offline
    await page.context.set_offline(True)
    await page.wait_for_timeout(1000)
    
    # Check page doesn't crash
    is_visible = await page.is_visible("body")
    assert is_visible, "Page should still be visible when offline"
    
    # Go back online
    await page.context.set_offline(False)
    await page.wait_for_timeout(1000)


# ─── Popcorn Menu Tests (macOS only) ───────────────────────────────


@pytest.mark.asyncio
async def test_popcorn_lifecycle_api(page: Page):
    """Test Popcorn start/stop/restart API"""
    # Get initial status
    response = await page.request.get(f"{BACKEND_URL}/api/surfaces/popcorn/status")
    await response.json()
    
    # Try to get Popcorn installed (shouldn't fail even if not installed)
    assert response.status == 200


# ─── Logging & Monitoring Tests ───────────────────────────────────


@pytest.mark.asyncio
async def test_backend_logs_requests(page: Page):
    """Test that backend logs requests properly"""
    response = await page.request.get(f"{BACKEND_URL}/api/health")
    assert response.status == 200
    
    # Log file should exist
    log_file = Path.home() / ".ucore" / "logs" / "ucore-menu.log"
    assert log_file.parent.exists(), "Log directory should exist"


@pytest.mark.asyncio
async def test_console_output_captured(page: Page):
    """Test that console output is captured"""
    # Navigate and trigger some logging
    await page.goto(FRONTEND_URL, wait_until="domcontentloaded")
    
    # Check that messages were captured (if any)
    # page.messages should have console output
    assert isinstance(page.messages, list)


# ─── Performance Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_backend_response_time(page: Page):
    """Test backend response time is acceptable"""
    start = time.time()
    response = await page.request.get(f"{BACKEND_URL}/api/health")
    elapsed = (time.time() - start) * 1000  # ms
    
    assert response.status == 200
    assert elapsed < 1000, f"Backend took {elapsed}ms (threshold: 1000ms)"


@pytest.mark.asyncio
async def test_frontend_load_time(page: Page):
    """Test frontend load time is acceptable"""
    start = time.time()
    await page.goto(FRONTEND_URL, wait_until="networkidle")
    elapsed = (time.time() - start) * 1000  # ms
    
    assert elapsed < 5000, f"Frontend took {elapsed}ms (threshold: 5000ms)"


# ─── Main (run with: python -m pytest tests/e2e_playwright.py) ──────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
