"""
Playwright Configuration for pytest
Configures Playwright browser settings and test execution

Author: Test Suite
Date: 2025-11-11
"""

import pytest
from playwright.sync_api import sync_playwright


def pytest_addoption(parser):
    """Add custom command line options"""
    # Note: pytest-playwright already provides --headed, --browser, and --slowmo
    # We don't need to add them again
    pass


# pytest-playwright provides these fixtures automatically:
# - playwright
# - browser_type
# - browser
# - context
# - page
# 
# We don't need to define them here


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests"
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make test result information available in fixtures.
    Used for screenshot on failure.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
