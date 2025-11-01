"""
Pytest configuration and fixtures for E2E tests.

Provides reusable test components including:
- Playwright browser fixtures
- Mock data fixtures
- Streamlit app fixtures
- T049: Browser launch options, viewport sizes, timeout configurations
- T065-T066: Screenshot capture and video recording
"""

import pytest
import json
import os
from pathlib import Path
from playwright.sync_api import Browser, Page, BrowserContext
from typing import Dict, Any, Generator


# T049: Browser launch configuration
@pytest.fixture(scope="session")
def browser_launch_args() -> dict:
    """Browser launch configuration"""
    return {
        'headless': os.getenv('HEADLESS', 'true').lower() == 'true',
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ],
        'slow_mo': int(os.getenv('SLOW_MO', '0'))  # Slow down operations for debugging
    }


@pytest.fixture(scope="session")
def default_timeout() -> int:
    """Default timeout for operations (milliseconds)"""
    return int(os.getenv('TEST_TIMEOUT', '30000'))


@pytest.fixture
def page_with_timeout(page: Page, default_timeout: int) -> Page:
    """Page fixture with configured timeout"""
    page.set_default_timeout(default_timeout)
    return page


# T049: Viewport size fixtures for responsive testing
@pytest.fixture
def desktop_viewport() -> dict:
    """Desktop viewport (1920x1080)"""
    return {'width': 1920, 'height': 1080}


@pytest.fixture
def tablet_viewport() -> dict:
    """Tablet viewport (768x1024)"""
    return {'width': 768, 'height': 1024}


@pytest.fixture
def mobile_viewport() -> dict:
    """Mobile viewport (375x667)"""
    return {'width': 375, 'height': 667}


@pytest.fixture
def app_url() -> str:
    """Application URL for testing"""
    return os.getenv('APP_URL', 'http://localhost:8501')


# T065: Screenshot capture on failure
@pytest.fixture
def screenshot_on_failure(request, page: Page):
    """Capture screenshot on test failure"""
    yield
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        screenshot_dir = 'tests/screenshots'
        os.makedirs(screenshot_dir, exist_ok=True)
        
        screenshot_path = f"{screenshot_dir}/{request.node.name}.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")


# T066: Video recording (retain on failure)
@pytest.fixture
def video_recording(browser: Browser, browser_context_args: Dict, request) -> Generator[BrowserContext, None, None]:
    """Enable video recording for test (retain on failure)"""
    video_dir = 'tests/videos'
    os.makedirs(video_dir, exist_ok=True)
    
    context = browser.new_context(
        **browser_context_args,
        record_video_dir=video_dir,
        record_video_size={'width': 1920, 'height': 1080}
    )
    
    yield context
    
    # Close context and save video only on failure
    context.close()
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        print(f"Video saved to {video_dir}")
    else:
        # Clean up video if test passed
        try:
            for page in context.pages:
                if page.video:
                    video_path = page.video.path()
                    if os.path.exists(video_path):
                        os.remove(video_path)
        except:
            pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to store test result for screenshot/video fixtures"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# Existing fixtures below
@pytest.fixture(scope="session")
def mock_cdx_api() -> Dict[str, Any]:
    """
    Load mock CDX API responses from fixture file.
    
    Returns:
        Dictionary containing mock CDX API responses for various scenarios
    """
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "mock_cdx_responses.json"
    with open(fixtures_path, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_html_content() -> str:
    """
    Load mock HTML content for testing term extraction.
    
    Returns:
        String containing sample HTML page content
    """
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "mock_html_content.html"
    with open(fixtures_path, "r") as f:
        return f.read()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: Dict) -> Dict:
    """
    Configure browser context for tests.
    
    Args:
        browser_context_args: Default context arguments from pytest-playwright
    
    Returns:
        Updated context arguments with custom settings
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "record_video_dir": "tests/screenshots/videos"
    }


@pytest.fixture
def streamlit_app(page: Page, monkeypatch) -> Page:
    """
    Navigate to Streamlit app and wait for ready state.
    
    Args:
        page: Playwright Page fixture from pytest-playwright
        monkeypatch: Pytest fixture for environment variable mocking
    
    Returns:
        Page object ready for interaction with Streamlit app
    
    Side Effects:
        - Sets ENABLE_PERFORMANCE_OPTS=true environment variable
        - Navigates to http://localhost:8501
        - Waits for Streamlit initialization
    """
    # Enable performance optimizations for testing
    monkeypatch.setenv("ENABLE_PERFORMANCE_OPTS", "true")
    monkeypatch.setenv("ENABLE_PERF_MONITORING", "true")
    
    # Navigate to Streamlit app
    page.goto("http://localhost:8501", wait_until="networkidle")
    
    # Wait for Streamlit to finish initializing (stale elements become stable)
    page.wait_for_selector("div[data-testid='stApp']", state="visible", timeout=10000)
    
    return page


@pytest.fixture
def mock_cdx_route(page: Page, mock_cdx_api: Dict) -> Page:
    """
    Mock Internet Archive CDX API responses.
    
    Args:
        page: Playwright Page object
        mock_cdx_api: Mock CDX response data
    
    Returns:
        Page with API routes mocked
    
    Side Effects:
        Intercepts requests to web.archive.org/cdx and returns mock data
    """
    def handle_cdx_request(route, request):
        url = request.url
        
        # Check which scenario to return based on URL parameters
        if "example.com" in url:
            route.fulfill(json=mock_cdx_api["test_scenarios"]["successful_query"]["response"])
        elif "notfound" in url:
            route.fulfill(json=mock_cdx_api["test_scenarios"]["empty_results"]["response"])
        elif "popular" in url:
            route.fulfill(json=mock_cdx_api["test_scenarios"]["paginated_results"]["response"])
        elif "error" in url:
            route.fulfill(status=500, body=json.dumps({"error": "Internal Server Error"}))
        elif "throttled" in url:
            route.fulfill(status=429, body=json.dumps({"error": "Rate limit exceeded"}))
        else:
            route.continue_()
    
    page.route("**/web.archive.org/cdx/**", handle_cdx_request)
    return page


@pytest.fixture
def performance_test_config() -> Dict[str, Any]:
    """
    Configuration for performance benchmarking tests.
    
    Returns:
        Dictionary with performance test parameters
    """
    return {
        "max_execution_time": 900,  # 15 minutes
        "max_memory_mb": 500,
        "min_cache_hit_rate": 40.0,
        "test_page_counts": [10, 50, 100, 300],
        "timeout_per_page": 3000  # 3 seconds
    }

import pytest
from playwright.sync_api import Page
import json
from pathlib import Path

# Fixtures will be implemented in Phase 2 (T011)
