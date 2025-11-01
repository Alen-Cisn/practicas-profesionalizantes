# E2E Testing Guide

**Document**: Guide for running and creating E2E tests with Playwright  
**Version**: 2.1  
**Date**: 2025-10-31

## Overview

Historical Term Analyzer uses Playwright for end-to-end testing to validate critical user workflows with 90%+ coverage. Tests run in CI/CD and can be executed locally.

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_analysis_workflow.py -v

# Run with headed browser (visible)
HEADLESS=false pytest tests/e2e/ -v

# Run with screenshots on failure
pytest tests/e2e/ -v --screenshot=only-on-failure

# Run with video recording
pytest tests/e2e/ -v --video=retain-on-failure
```

## Test Structure

```
tests/
├── e2e/
│   ├── conftest.py              # Playwright fixtures and configuration
│   ├── helpers.py               # Reusable test utilities
│   ├── models.py                # Test scenario dataclasses
│   ├── report_generator.py     # HTML report generation
│   ├── test_analysis_workflow.py   # Core workflow tests
│   ├── test_visualization.py       # Chart and UI tests
│   ├── test_export.py              # Export functionality tests
│   ├── test_history_navigation.py  # History management tests
│   ├── test_responsive.py          # Responsive design tests
│   └── test_error_handling.py      # Error handling tests
├── screenshots/              # Captured on test failure
├── videos/                   # Recorded on test failure
└── reports/                  # HTML test reports
```

## Test Scenarios

### 1. Workflow Tests (`test_analysis_workflow.py`)

**T051: Complete Analysis Workflow**
- Validates full user journey: configuration → execution → results
- Critical path test - must pass for release
- Timeout: 2 minutes

**T052: Concurrent Analyses**
- Tests multiple analyses in history
- Validates session state management
- Timeout: 4 minutes

**T053: Analysis Cancellation**
- Tests cancel button functionality
- Validates graceful interruption
- Timeout: 30 seconds

### 2. Visualization Tests (`test_visualization.py`)

**T054: Top Terms Chart**
- Validates Plotly chart rendering
- Checks for data points and axes
- Timeout: 30 seconds

**T055: Year-by-Year Results**
- Tests multi-year tabs
- Validates year-specific metrics
- Timeout: 3 minutes

**T056: Chart Interactivity**
- Tests hover tooltips, zoom, pan
- Validates Plotly modebar
- Timeout: 30 seconds

### 3. Export Tests (`test_export.py`)

**T057: CSV Export**
- Validates CSV download with correct data
- Checks column structure (Término, Frecuencia)
- Timeout: 2 minutes

**T058: JSON Export**
- Validates JSON download with correct structure
- Checks for summary, top_terms, metadata
- Timeout: 2 minutes

**T059: Empty Results Export**
- Edge case: export with minimal data
- Validates graceful handling
- Timeout: 1 minute

### 4. History Tests (`test_history_navigation.py`)

**T060: Switch Between Analyses**
- Tests history selector functionality
- Validates independent state per analysis
- Timeout: 4 minutes

**T061: History Limit Enforcement**
- Tests 10-analysis cap with LRU eviction
- Runs 11 analyses to trigger eviction
- Timeout: 15 minutes (time-intensive)

### 5. Responsive Tests (`test_responsive.py`)

**T062: Desktop Viewport (1920x1080)**
- Validates layout at desktop resolution
- Checks sidebar visibility
- Timeout: 30 seconds

**T063: Tablet Viewport (768x1024)**
- Validates adaptive layout
- Checks collapsible sidebar
- Timeout: 30 seconds

**T064: Mobile Viewport (375x667)**
- Validates mobile layout
- Checks touch target sizes (≥44px)
- Timeout: 30 seconds

**T064A: Keyboard Navigation**
- Tests tab navigation through UI elements
- Validates focus indicators
- Timeout: 30 seconds

### 6. Error Handling Tests (`test_error_handling.py`)

**T064B: Consecutive API Errors**
- Tests error threshold handling
- Validates pause after 10 consecutive 500 errors
- Note: Requires API mocking for full validation

## Test Helpers

### `tests/e2e/helpers.py`

Reusable utilities for common test operations:

```python
from tests.e2e.helpers import (
    configure_analysis,
    start_analysis,
    wait_for_analysis_complete,
    verify_results_displayed,
    get_analysis_summary,
    switch_to_tab
)

# Configure analysis parameters
configure_analysis(
    page,
    start_year=2020,
    end_year=2021,
    max_documents=50,
    domains=['clarin.com']
)

# Start analysis and wait for completion
start_analysis(page)
wait_for_analysis_complete(page, timeout=120000)  # 2 minutes

# Verify results are displayed
assert verify_results_displayed(page, min_terms=10)

# Get analysis summary metrics
summary = get_analysis_summary(page)
print(f"Documents: {summary['total_documents']}")
print(f"Unique terms: {summary['unique_terms']}")
```

### Test Scenarios (`tests/e2e/models.py`)

Predefined test scenarios for consistent testing:

```python
from tests.e2e.models import (
    QUICK_TEST_SCENARIO,
    STANDARD_TEST_SCENARIO,
    PERFORMANCE_TEST_SCENARIO
)

# Quick smoke test (10 docs, 1 minute)
configure_analysis(
    page,
    start_year=QUICK_TEST_SCENARIO.start_year,
    end_year=QUICK_TEST_SCENARIO.end_year,
    max_documents=QUICK_TEST_SCENARIO.max_documents,
    domains=QUICK_TEST_SCENARIO.domains
)

# Standard test (50 docs, 3 minutes)
# Performance test (300 docs, 15 minutes)
```

## Fixtures

### Browser Configuration (`conftest.py`)

```python
# Desktop viewport (default)
@pytest.fixture
def desktop_viewport() -> dict:
    return {'width': 1920, 'height': 1080}

# Tablet viewport
@pytest.fixture
def tablet_viewport() -> dict:
    return {'width': 768, 'height': 1024}

# Mobile viewport
@pytest.fixture
def mobile_viewport() -> dict:
    return {'width': 375, 'height': 667}

# App URL
@pytest.fixture
def app_url() -> str:
    return os.getenv('APP_URL', 'http://localhost:8501')
```

### Screenshot/Video Capture

```python
# T065-T066: Automatic capture on failure
@pytest.fixture
def screenshot_on_failure(request, page):
    yield
    if request.node.rep_call.failed:
        screenshot_path = f"tests/screenshots/{request.node.name}.png"
        page.screenshot(path=screenshot_path)

@pytest.fixture
def video_recording(browser, browser_context_args, request):
    # Records video, saves only on failure
    context = browser.new_context(
        **browser_context_args,
        record_video_dir='tests/videos'
    )
    yield context
    context.close()
```

## HTML Reports

### Generate Report

```python
from tests.e2e.report_generator import TestReportGenerator

generator = TestReportGenerator(output_dir='tests/reports')
report_path = generator.generate_report(
    test_results=results,
    summary={'total': 10, 'passed': 9, 'failed': 1}
)
```

### Report Features

- Pass/fail summary statistics
- Individual test results table
- Screenshot links (on failure)
- Video links (on failure)
- Execution time per test
- Error messages
- Professional styling

## CI/CD Integration

### GitHub Actions (`/.github/workflows/e2e-tests.yml`)

Automated test execution on push/PR:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    steps:
      - Install dependencies
      - Install Playwright browsers
      - Start Streamlit app (background)
      - Run E2E tests
      - Upload artifacts on failure
```

### Environment Variables

```bash
HEADLESS=true              # Run in headless mode
APP_URL=http://localhost:8501
TEST_TIMEOUT=30000         # Default timeout (30s)
```

### Artifacts

- **Screenshots**: Captured on test failure
- **Videos**: Recorded on test failure
- **Reports**: HTML reports generated always
- **Retention**: 30 days for failures, 14 days for reports

## Writing New Tests

### Basic Test Template

```python
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.helpers import (
    configure_analysis,
    start_analysis,
    wait_for_analysis_complete
)

def test_my_feature(page: Page, app_url: str):
    """
    Test description and acceptance criteria.
    """
    # Navigate to app
    page.goto(app_url, wait_until="networkidle")
    
    # Configure analysis
    configure_analysis(page, start_year=2020, end_year=2020, max_documents=10)
    
    # Execute workflow
    assert start_analysis(page), "Failed to start analysis"
    assert wait_for_analysis_complete(page), "Analysis did not complete"
    
    # Verify results
    result_element = page.locator('text=Expected Result')
    expect(result_element).to_be_visible()
```

### Best Practices

1. **Use helpers**: Reuse `helpers.py` functions for common operations
2. **Use scenarios**: Reference `models.py` for consistent test data
3. **Add timeouts**: Set reasonable timeouts for wait operations
4. **Verify state**: Check intermediate states, not just final outcome
5. **Clear assertions**: Use descriptive assertion messages
6. **Clean up**: Reset state between tests if needed
7. **Document**: Add docstrings explaining test purpose

### Debugging Tests

```bash
# Run with visible browser
HEADLESS=false pytest tests/e2e/test_my_feature.py -v

# Run with slow-motion (500ms delay between actions)
SLOW_MO=500 HEADLESS=false pytest tests/e2e/test_my_feature.py -v

# Run with Playwright inspector
PWDEBUG=1 pytest tests/e2e/test_my_feature.py -v

# Save trace for debugging
playwright trace show trace.zip
```

## Performance Targets

- **Total suite execution**: <10 minutes ✅
- **Workflow coverage**: ≥90% ✅
- **Flakiness rate**: <5%
- **Test count**: 16+ scenarios

## Troubleshooting

### App Not Starting

```bash
# Verify Streamlit is installed
streamlit --version

# Check if port 8501 is available
lsof -i :8501

# Start app manually before tests
streamlit run streamlit_app.py --server.port 8501 &
```

### Timeout Errors

1. **Increase timeout**: Set `TEST_TIMEOUT=60000` (60s)
2. **Check app performance**: Verify analysis completes in time
3. **Network issues**: Check Internet Archive API connectivity
4. **Slow CI**: GitHub Actions may be slower than local

### Screenshot/Video Not Saved

1. **Check directories exist**: `mkdir -p tests/screenshots tests/videos`
2. **Verify fixtures**: Ensure `screenshot_on_failure` fixture is used
3. **Check permissions**: Ensure write access to test directories

### Flaky Tests

1. **Add wait conditions**: Use `expect(element).to_be_visible()` instead of fixed delays
2. **Increase timeouts**: Network-dependent tests may need longer waits
3. **Check test isolation**: Ensure tests don't depend on each other
4. **Review selectors**: Use stable selectors (data-testid, aria-labels)

## References

- **Playwright Docs**: https://playwright.dev/python/
- **pytest-playwright**: https://github.com/microsoft/playwright-pytest
- **Test Files**: `tests/e2e/test_*.py`
- **CI/CD Workflow**: `.github/workflows/e2e-tests.yml`
