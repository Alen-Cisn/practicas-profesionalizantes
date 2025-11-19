"""
Playwright E2E Test Configuration
Provides fixtures and utilities for testing the Historical Term Analyzer Streamlit app

Author: Test Suite
Date: 2025-11-11
"""

import pytest
import subprocess
import time
import requests
from playwright.sync_api import Page, Browser, BrowserContext, expect
from typing import Generator
import os
import signal
import sys
import platform


# Test configuration
STREAMLIT_URL = "http://localhost:8501"
STREAMLIT_TIMEOUT = 30000  # 30 seconds
APP_STARTUP_TIMEOUT = 10  # 10 seconds to start the app
IS_WINDOWS = platform.system() == "Windows"


@pytest.fixture(scope="session")
def streamlit_app():
    """
    Start the Streamlit app before tests and stop it after.
    This fixture runs once per test session.
    """
    # Get the path to streamlit executable in the virtual environment
    streamlit_path = os.path.join(os.path.dirname(sys.executable), "streamlit")
    
    # Start Streamlit app with platform-specific process group handling
    if IS_WINDOWS:
        # On Windows, create new process group
        process = subprocess.Popen(
            [streamlit_path, "run", "streamlit_app.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # On Unix, create new process group for proper cleanup
        process = subprocess.Popen(
            [streamlit_path, "run", "streamlit_app.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # type: ignore
        )
    
    # Wait for the app to be ready
    max_attempts = 20
    for i in range(max_attempts):
        try:
            response = requests.get(STREAMLIT_URL, timeout=2)
            if response.status_code == 200:
                print(f"\n✅ Streamlit app started successfully at {STREAMLIT_URL}")
                break
        except requests.exceptions.RequestException:
            if i < max_attempts - 1:
                time.sleep(1)
            else:
                # Kill the process if it didn't start
                _terminate_process(process)
                raise RuntimeError("Failed to start Streamlit app")
    
    yield STREAMLIT_URL
    
    # Cleanup: Stop the Streamlit app
    print("\n🛑 Stopping Streamlit app...")
    _terminate_process(process)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _terminate_process(process):
    """Terminate a process in a cross-platform way."""
    if IS_WINDOWS:
        # On Windows, use terminate() which sends CTRL_BREAK_EVENT to process group
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
    else:
        # On Unix, kill the process group
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # type: ignore
        except ProcessLookupError:
            pass  # Process already terminated


@pytest.fixture
def browser_context(browser) -> Generator[BrowserContext, None, None]:
    """
    Create a new browser context with custom configuration.
    Each test gets a fresh context with isolated state.
    Note: browser fixture is provided by pytest-playwright
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
    )
    
    # Set longer default timeout for Streamlit
    context.set_default_timeout(STREAMLIT_TIMEOUT)
    
    yield context
    
    context.close()


@pytest.fixture
def page(browser_context: BrowserContext, streamlit_app: str) -> Generator[Page, None, None]:
    """
    Create a new page and navigate to the Streamlit app.
    Each test gets a fresh page.
    """
    page = browser_context.new_page()
    
    # Navigate to the app
    page.goto(streamlit_app)
    
    # Wait for Streamlit to be fully loaded
    wait_for_streamlit_ready(page)
    
    yield page
    
    page.close()


def wait_for_streamlit_ready(page: Page, timeout: int = STREAMLIT_TIMEOUT):
    """
    Wait for Streamlit app to be fully loaded and interactive.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds
    """
    # Wait for the main app container to be visible
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout)
    
    # Wait for any initial loading spinners to disappear
    page.wait_for_function(
        """() => {
            const spinners = document.querySelectorAll('[data-testid="stSpinner"]');
            return spinners.length === 0;
        }""",
        timeout=timeout
    )
    
    # Give Streamlit a moment to settle
    page.wait_for_timeout(500)


def fill_streamlit_number_input(page: Page, label: str, value: int):
    """
    Fill a Streamlit number input field by label.
    
    Args:
        page: Playwright page object
        label: The label text of the number input
        value: The numeric value to set
    """
    # Find the input by associated label
    input_locator = page.locator(f'label:has-text("{label}") + div input')
    input_locator.click()
    input_locator.fill(str(value))
    input_locator.press("Enter")
    page.wait_for_timeout(300)  # Wait for Streamlit to process


def click_streamlit_button(page: Page, button_text: str):
    """
    Click a Streamlit button by its text.
    
    Args:
        page: Playwright page object
        button_text: The text displayed on the button
    """
    button = page.get_by_role("button", name=button_text)
    button.click()
    page.wait_for_timeout(500)  # Wait for Streamlit to process


def select_streamlit_multiselect_option(page: Page, label: str, option: str):
    """
    Select an option in a Streamlit multiselect widget.
    
    Args:
        page: Playwright page object
        label: The label of the multiselect widget
        option: The option to select
    """
    # Click the multiselect to open dropdown
    multiselect = page.locator(f'label:has-text("{label}") + div')
    multiselect.click()
    page.wait_for_timeout(300)
    
    # Click the option
    page.get_by_text(option, exact=True).click()
    page.wait_for_timeout(300)
    
    # Click outside to close dropdown
    page.locator('[data-testid="stAppViewContainer"]').click(position={"x": 0, "y": 0})


def move_streamlit_slider(page: Page, label: str, value: int):
    """
    Set a Streamlit slider to a specific value.
    
    Args:
        page: Playwright page object
        label: The label of the slider
        value: The value to set
    
    Note:
        Streamlit 1.50.0+ uses div[role="slider"] instead of input[type="range"]
    """
    # Streamlit sliders in sidebar use div with role="slider" and aria-label
    # Scope to sidebar first
    sidebar = page.locator('[data-testid="stSidebar"]')
    
    # Find the slider element by role and aria-label
    slider_element = sidebar.locator(f'div[role="slider"][aria-label="{label}"]').first
    
    try:
        slider_element.wait_for(state="visible", timeout=5000)
        
        # Get the slider's value range (can be int or float)
        min_value = float(slider_element.get_attribute('aria-valuemin'))
        max_value = float(slider_element.get_attribute('aria-valuemax'))
        
        # Calculate the percentage position for the value
        # The slider uses transform: translate() to position the thumb
        value_range = max_value - min_value
        value_percent = (value - min_value) / value_range
        
        # Get the slider track to calculate pixel position
        # The track is the parent's parent element
        slider_track = slider_element.locator('xpath=../..').first
        track_width = slider_track.evaluate("el => el.getBoundingClientRect().width")
        
        # Calculate target position in pixels
        target_x = track_width * value_percent
        
        # Drag the slider to the target position
        # Get current slider thumb position
        slider_box = slider_element.bounding_box()
        if slider_box:
            # Start from center of thumb
            start_x = slider_box['x'] + slider_box['width'] / 2
            start_y = slider_box['y'] + slider_box['height'] / 2
            
            # Calculate the track's left position
            track_box = slider_track.bounding_box()
            if track_box:
                # Target position relative to track
                target_absolute_x = track_box['x'] + target_x
                
                # Perform the drag
                page.mouse.move(start_x, start_y)
                page.mouse.down()
                page.mouse.move(target_absolute_x, start_y, steps=10)
                page.mouse.up()
        
    except Exception as e:
        raise Exception(f"Could not locate or interact with slider '{label}' in sidebar. Error: {e}")
    
    page.wait_for_timeout(500)


def wait_for_analysis_complete(page: Page, timeout: int = 120000):
    """
    Wait for the analysis to complete by checking for result indicators.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait in milliseconds (default 2 minutes)
    """
    # Wait for the results header to appear
    page.wait_for_selector('text="📊 Resultados del Análisis"', timeout=timeout)
    
    # Wait for any spinners to disappear
    page.wait_for_function(
        """() => {
            const spinners = document.querySelectorAll('[data-testid="stSpinner"]');
            return spinners.length === 0;
        }""",
        timeout=timeout
    )
    
    page.wait_for_timeout(1000)


def get_metric_value(page: Page, metric_label: str) -> str:
    """
    Get the value of a Streamlit metric by its label.
    
    Args:
        page: Playwright page object
        metric_label: The label of the metric
        
    Returns:
        The metric value as a string
    """
    metric = page.locator(f'[data-testid="stMetric"]:has-text("{metric_label}")')
    value = metric.locator('[data-testid="stMetricValue"]').text_content()
    return value.strip() if value else ""


def take_screenshot(page: Page, name: str):
    """
    Take a screenshot and save it to the screenshots directory.
    
    Args:
        page: Playwright page object
        name: Name for the screenshot file
    """
    screenshots_dir = "tests/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(screenshots_dir, f"{name}_{timestamp}.png")
    
    page.screenshot(path=filepath, full_page=True)
    print(f"📸 Screenshot saved: {filepath}")


@pytest.fixture
def screenshot_on_failure(page: Page, request):
    """
    Automatically take a screenshot if a test fails.
    """
    yield
    
    if request.node.rep_call.failed:
        test_name = request.node.name
        take_screenshot(page, f"failure_{test_name}")
