# Playwright E2E Testing Setup - Historical Term Analyzer

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Run Tests

```bash
# Quick smoke tests (fast, verify basic functionality)
pytest tests/e2e/ -m smoke -v

# All UI tests (skip slow integration tests)
pytest tests/e2e/ -m "not slow" -v

# Run with visible browser (for debugging)
pytest tests/e2e/ --headed -v

# Use the convenience script
chmod +x run_tests.sh
./run_tests.sh --smoke --headed
```

## 📋 Test Overview

### Test Files Created

1. **`tests/conftest.py`** - Global pytest configuration with Playwright setup
2. **`tests/e2e/conftest.py`** - E2E-specific fixtures and utilities
3. **`tests/e2e/test_smoke.py`** - Quick smoke tests (< 30 seconds)
4. **`tests/e2e/test_streamlit_ui.py`** - UI component tests
5. **`tests/e2e/test_analysis_workflow.py`** - Full workflow tests
6. **`pytest.ini`** - Pytest configuration
7. **`run_tests.sh`** - Convenience script for running tests

### Test Categories

| Category | Description | Duration | Command |
|----------|-------------|----------|---------|
| **Smoke** | Basic functionality checks | < 30s | `pytest -m smoke` |
| **UI** | Interface component tests | 1-2 min | `pytest test_streamlit_ui.py` |
| **Workflow** | Full analysis workflows | 5-10 min | `pytest test_analysis_workflow.py` |
| **Integration** | Complete end-to-end tests | 10+ min | `pytest -m integration` |

## 🛠️ Key Features

### Automatic Streamlit Management

Tests automatically start and stop the Streamlit app:
- No manual app startup needed
- Automatic cleanup after tests
- Proper port management

### Smart Waiting

Built-in utilities for Streamlit's async nature:
- Wait for app to be fully loaded
- Wait for spinners to disappear
- Wait for analysis completion

### Screenshot on Failure

Failed tests automatically capture screenshots:
- Saved to `tests/screenshots/`
- Timestamped filenames
- Full-page captures

### Flexible Configuration

Run tests your way:
- Different browsers (Chromium, Firefox, WebKit)
- Headed or headless mode
- Slow motion for debugging
- Parallel execution support

## 📝 Usage Examples

### Run Specific Tests

```bash
# Single test class
pytest tests/e2e/test_streamlit_ui.py::TestStreamlitUI -v

# Single test method
pytest tests/e2e/test_streamlit_ui.py::TestStreamlitUI::test_app_loads_successfully -v

# All smoke tests with visible browser
pytest tests/e2e/ -m smoke --headed -v
```

### Debugging Tests

```bash
# Run with Playwright inspector (interactive debugging)
PWDEBUG=1 pytest tests/e2e/test_smoke.py::TestSmokeTests::test_app_is_accessible

# Run slowly to watch what's happening
pytest tests/e2e/ --headed --slowmo 1000 -v

# Run specific test with detailed output
pytest tests/e2e/test_streamlit_ui.py::TestStreamlitUI::test_app_loads_successfully -vv -s
```

### Different Browsers

```bash
# Firefox
pytest tests/e2e/ --browser firefox --headed

# WebKit (Safari-like)
pytest tests/e2e/ --browser webkit --headed
```

### Using the Shell Script

```bash
# Make executable (first time only)
chmod +x run_tests.sh

# Quick smoke tests with visible browser
./run_tests.sh --smoke --headed

# UI tests only, headless
./run_tests.sh --ui

# Skip slow tests, show browser
./run_tests.sh --no-slow --headed

# All options
./run_tests.sh --help
```

## 🔧 Utility Functions

The test suite provides several helper functions in `tests/e2e/conftest.py`:

```python
# Wait for Streamlit to be ready
wait_for_streamlit_ready(page)

# Fill number inputs
fill_streamlit_number_input(page, "Año inicio", 2000)

# Click buttons
click_streamlit_button(page, "Iniciar Análisis")

# Move sliders
move_streamlit_slider(page, "Máximo de páginas web", 100)

# Wait for analysis to complete
wait_for_analysis_complete(page, timeout=120000)

# Get metric values
value = get_metric_value(page, "Total de Páginas")

# Take screenshots
take_screenshot(page, "my_test_step")
```

## 🎯 Writing Your Own Tests

### Basic Test Template

```python
import pytest
from playwright.sync_api import Page, expect
from .conftest import wait_for_streamlit_ready, take_screenshot

class TestMyFeature:
    """Description of what this test suite covers"""
    
    def test_my_feature_works(self, page: Page):
        """Test that my feature works correctly"""
        # Arrange - set up test conditions
        
        # Act - perform actions
        page.locator('button:has-text("My Button")').click()
        page.wait_for_timeout(500)
        
        # Assert - verify results
        expect(page.locator("text=Expected Result")).to_be_visible()
        
        # Optional screenshot
        take_screenshot(page, "my_feature_test")
```

### Mark Tests Appropriately

```python
@pytest.mark.smoke  # Quick tests
def test_quick_check(self, page: Page):
    pass

@pytest.mark.slow  # Longer tests
@pytest.mark.integration  # Full workflow tests
def test_complete_workflow(self, page: Page):
    pass
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8501
lsof -i :8501

# Kill the process
kill -9 <PID>
```

### Tests Timing Out

1. Check if Streamlit app starts manually:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Increase timeout in `conftest.py`:
   ```python
   STREAMLIT_TIMEOUT = 60000  # 60 seconds
   ```

3. Check network connectivity (app needs Internet Archive access)

### Element Not Found

1. Use Playwright Inspector:
   ```bash
   PWDEBUG=1 pytest tests/e2e/test_smoke.py::test_name
   ```

2. Take screenshot to see current state:
   ```python
   take_screenshot(page, "debug_state")
   ```

3. Check if element selector is correct:
   ```python
   # List all matching elements
   print(page.locator("text=My Text").count())
   ```

### Flaky Tests

1. Add explicit waits after interactions:
   ```python
   button.click()
   page.wait_for_timeout(500)  # Wait for Streamlit to process
   ```

2. Use Playwright's auto-waiting:
   ```python
   expect(element).to_be_visible()  # Waits up to 30s by default
   ```

3. Wait for Streamlit to finish rendering:
   ```python
   wait_for_streamlit_ready(page)
   ```

## 📊 Test Reports

### Generate HTML Report

```bash
# Install pytest-html
pip install pytest-html

# Generate report
pytest tests/e2e/ --html=report.html --self-contained-html
```

### Coverage Report

```bash
# Install pytest-cov
pip install pytest-cov

# Run with coverage
pytest tests/e2e/ --cov=streamlit_app --cov-report=html

# View report
open htmlcov/index.html
```

## 🔄 Continuous Integration

### Example GitHub Actions Workflow

Create `.github/workflows/e2e-tests.yml`:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run smoke tests
        run: pytest tests/e2e/ -m smoke -v
      
      - name: Run UI tests
        run: pytest tests/e2e/test_streamlit_ui.py -v
      
      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-screenshots
          path: tests/screenshots/
```

## 📚 Additional Resources

- [Playwright Python Docs](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Streamlit Testing](https://docs.streamlit.io/knowledge-base/using-streamlit/how-do-i-test-my-streamlit-app)
- [Playwright Inspector](https://playwright.dev/python/docs/inspector)

## ✅ Test Checklist

Before committing changes, run:

- [ ] Smoke tests: `pytest tests/e2e/ -m smoke`
- [ ] UI tests: `pytest tests/e2e/test_streamlit_ui.py`
- [ ] Check screenshots for any failures in `tests/screenshots/`
- [ ] Verify no console errors: Check test output

## 🎓 Best Practices

1. **Always use fixtures** - Don't manually start/stop the app
2. **Wait for Streamlit** - Use `wait_for_streamlit_ready()` liberally
3. **Take screenshots** - Especially at critical points for debugging
4. **Use descriptive names** - Test names should explain what they test
5. **Keep tests independent** - Each test should work in isolation
6. **Mark appropriately** - Use `@pytest.mark.smoke/slow/integration`
7. **Clean up resources** - Fixtures handle this automatically
8. **Test realistically** - Use reasonable data volumes in tests

## 📞 Support

For issues with the test suite:
1. Check this README
2. Review test output and screenshots
3. Use Playwright Inspector for debugging
4. Check application logs
5. Create an issue with full error details
