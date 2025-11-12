# Historical Term Analyzer - E2E Testing Guide

## Overview

This directory contains end-to-end (E2E) tests for the Historical Term Analyzer Streamlit application using Playwright. The tests verify the complete user workflow from configuration to analysis results.

## Test Structure

```
tests/
├── conftest.py                      # Pytest and Playwright configuration
├── e2e/
│   ├── conftest.py                  # E2E-specific fixtures and utilities
│   ├── test_streamlit_ui.py         # UI component tests
│   ├── test_analysis_workflow.py    # Complete workflow tests
│   └── __init__.py
├── screenshots/                      # Test screenshots (auto-generated)
└── pytest.ini                        # Pytest configuration
```

## Prerequisites

### 1. Install Test Dependencies

```bash
pip install pytest pytest-playwright
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
# Optional: install other browsers
playwright install firefox webkit
```

### 3. Verify Streamlit Installation

```bash
pip install -r requirements.txt
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/e2e/

# With verbose output
pytest tests/e2e/ -v

# Show print statements
pytest tests/e2e/ -s
```

### Run Specific Test Files

```bash
# UI tests only
pytest tests/e2e/test_streamlit_ui.py

# Workflow tests only
pytest tests/e2e/test_analysis_workflow.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/e2e/test_streamlit_ui.py::TestStreamlitUI

# Run a specific test method
pytest tests/e2e/test_streamlit_ui.py::TestStreamlitUI::test_app_loads_successfully
```

### Run Tests by Markers

```bash
# Run only smoke tests (quick tests)
pytest tests/e2e/ -m smoke

# Skip slow tests
pytest tests/e2e/ -m "not slow"

# Run only integration tests
pytest tests/e2e/ -m integration
```

### Browser Options

```bash
# Run in headed mode (show browser)
pytest tests/e2e/ --headed

# Use specific browser
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# Slow down execution for debugging
pytest tests/e2e/ --headed --slowmo 1000
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/e2e/ -n 4
```

## Test Categories

### 1. UI Tests (`test_streamlit_ui.py`)

Tests the user interface components and layout:
- App loading and initialization
- Sidebar configuration options
- Button and input presence
- Responsive layout
- Accessibility features
- Error handling

**Example:**
```bash
pytest tests/e2e/test_streamlit_ui.py -v
```

### 2. Workflow Tests (`test_analysis_workflow.py`)

Tests the complete analysis workflow:
- Configuration changes
- Analysis execution
- Results display
- Export functionality
- History management
- Log functionality

**Example:**
```bash
# Run quick workflow test (might take 3-5 minutes)
pytest tests/e2e/test_analysis_workflow.py::TestAnalysisWorkflow::test_quick_analysis_workflow -v
```

## Test Fixtures and Utilities

### Key Fixtures (in `e2e/conftest.py`)

- **`streamlit_app`**: Starts/stops Streamlit app for testing
- **`browser_context`**: Creates isolated browser context
- **`page`**: Provides fresh page for each test
- **`screenshot_on_failure`**: Auto-captures screenshots on test failure

### Utility Functions

- **`wait_for_streamlit_ready(page)`**: Wait for app to load
- **`fill_streamlit_number_input(page, label, value)`**: Fill number inputs
- **`click_streamlit_button(page, text)`**: Click buttons
- **`move_streamlit_slider(page, label, value)`**: Set slider values
- **`wait_for_analysis_complete(page)`**: Wait for analysis to finish
- **`get_metric_value(page, label)`**: Extract metric values
- **`take_screenshot(page, name)`**: Manual screenshot capture

## Writing New Tests

### Basic Test Template

```python
import pytest
from playwright.sync_api import Page, expect
from .conftest import wait_for_streamlit_ready, take_screenshot

class TestMyFeature:
    """Test suite for my feature"""
    
    def test_my_feature(self, page: Page):
        """Test description"""
        # Arrange: Set up test conditions
        
        # Act: Perform actions
        
        # Assert: Verify results
        expect(page.locator("text=Expected Text")).to_be_visible()
        
        # Optional: Take screenshot
        take_screenshot(page, "my_feature_test")
```

### Slow Test Example

```python
@pytest.mark.slow
@pytest.mark.integration
def test_full_analysis(self, page: Page):
    """Test that requires long execution time"""
    # Test implementation
    pass
```

## Debugging Tests

### 1. Run in Headed Mode

See the browser while tests run:
```bash
pytest tests/e2e/ --headed --slowmo 500
```

### 2. Use Playwright Inspector

Debug interactively:
```bash
PWDEBUG=1 pytest tests/e2e/test_streamlit_ui.py::test_name
```

### 3. Check Screenshots

Failed tests automatically save screenshots to `tests/screenshots/`:
```bash
ls tests/screenshots/
```

### 4. Verbose Output

Get detailed test output:
```bash
pytest tests/e2e/ -vv -s
```

### 5. Use Playwright Trace

Record test execution:
```python
# Add to your test
context.tracing.start(screenshots=True, snapshots=True)
# ... test code ...
context.tracing.stop(path="trace.zip")
```

View trace:
```bash
playwright show-trace trace.zip
```

## Common Issues and Solutions

### Issue: Streamlit app doesn't start

**Solution:**
```bash
# Manually test Streamlit
streamlit run streamlit_app.py

# Check if port 8501 is in use
lsof -i :8501
```

### Issue: Tests timeout

**Solution:**
- Increase timeout in `conftest.py`
- Use `--slowmo` to slow down execution
- Check network connectivity for Internet Archive API

### Issue: Element not found

**Solution:**
- Use Playwright Inspector: `PWDEBUG=1 pytest ...`
- Take screenshots to see actual state
- Wait for Streamlit to finish rendering

### Issue: Flaky tests

**Solution:**
- Add explicit waits: `page.wait_for_timeout(500)`
- Use `wait_for_streamlit_ready()` after navigation
- Check for loading spinners before assertions

## Best Practices

1. **Always wait for Streamlit to be ready** after page loads or interactions
2. **Use descriptive test names** that explain what is being tested
3. **Take screenshots** at important test steps for debugging
4. **Keep tests independent** - each test should work in isolation
5. **Use markers** to categorize tests (slow, smoke, integration)
6. **Clean up resources** - fixtures handle cleanup automatically
7. **Avoid hardcoded waits** - use Playwright's built-in waiting mechanisms

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-playwright
          playwright install chromium
      - name: Run tests
        run: pytest tests/e2e/ -v
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: tests/screenshots/
```

## Performance Testing

For performance tests, use the `@pytest.mark.slow` marker:

```python
@pytest.mark.slow
def test_large_dataset_performance(self, page: Page):
    """Test with maximum documents"""
    # Configure for large dataset
    move_streamlit_slider(page, "Máximo de páginas web", 1000)
    # ... rest of test
```

## Test Coverage

To measure test coverage:

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest tests/e2e/ --cov=streamlit_app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Additional Resources

- [Playwright Python Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Streamlit Testing Guide](https://docs.streamlit.io/knowledge-base/using-streamlit/how-do-i-test-my-streamlit-app)

## Support

For issues or questions about the tests:
1. Check test output and screenshots
2. Review Playwright documentation
3. Check application logs
4. Create an issue with test failure details
