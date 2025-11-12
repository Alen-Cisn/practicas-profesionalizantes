# 🧪 Test Suite for Historical Term Analyzer

> Comprehensive Playwright-based E2E testing framework for the Streamlit application

## 🎯 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Run smoke tests (fastest, < 30 seconds)
./run_tests.sh --smoke --headed

# 3. Run all tests
pytest tests/e2e/ -v
```

## 📁 Directory Structure

```
tests/
├── README.md                    ← You are here
├── TESTING.md                   ← Comprehensive testing guide
├── SETUP_COMPLETE.md            ← What was created & quick start
├── conftest.py                  ← Global Playwright configuration
├── pytest.ini                   ← Pytest settings
│
├── e2e/                         ← End-to-end tests
│   ├── README.md                ← E2E testing guide
│   ├── conftest.py              ← E2E fixtures & utilities
│   ├── test_smoke.py            ← Quick smoke tests (5 tests)
│   ├── test_streamlit_ui.py     ← UI component tests (11 tests)
│   ├── test_analysis_workflow.py ← Workflow tests (15 tests)
│   └── test_example.py          ← Example patterns (15 tests)
│
└── screenshots/                 ← Auto-generated test screenshots
```

## 📊 Test Categories

| Type | Duration | Tests | Command |
|------|----------|-------|---------|
| **Smoke** | < 30s | 5 | `pytest -m smoke` |
| **UI** | 1-2 min | 11 | `pytest test_streamlit_ui.py` |
| **Workflow** | 3-5 min | 15 | `pytest -m "not slow"` |
| **Full** | 10+ min | 46+ | `pytest tests/e2e/` |

## 🚀 Common Commands

```bash
# Quick smoke tests with browser visible
./run_tests.sh --smoke --headed

# All UI tests (skip slow integration)
./run_tests.sh --ui --no-slow

# Specific test file
pytest tests/e2e/test_smoke.py -v

# Specific test
pytest tests/e2e/test_smoke.py::TestSmokeTests::test_app_is_accessible -v

# Debug mode (interactive)
PWDEBUG=1 pytest tests/e2e/test_smoke.py::test_name
```

## 📚 Documentation

- **[TESTING.md](TESTING.md)** - Comprehensive testing guide with examples
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Setup summary and quick start
- **[e2e/README.md](e2e/README.md)** - E2E-specific documentation
- **[../PLAYWRIGHT_IMPLEMENTATION.md](../PLAYWRIGHT_IMPLEMENTATION.md)** - Complete implementation summary

## 🔧 Configuration

### Browser Selection
```bash
pytest tests/e2e/ --browser chromium  # Default
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit    # Safari-like
```

### Display Mode
```bash
pytest tests/e2e/ --headed           # Show browser
pytest tests/e2e/ --headed --slowmo 500  # Slow motion
```

### Test Selection
```bash
pytest tests/e2e/ -m smoke           # Only smoke tests
pytest tests/e2e/ -m "not slow"      # Skip slow tests
pytest tests/e2e/ -k "test_app"      # Match test name
```

## 🛠️ Utilities

The test suite provides helper functions in `e2e/conftest.py`:

```python
# Wait for app to be ready
wait_for_streamlit_ready(page)

# Interact with Streamlit components
fill_streamlit_number_input(page, "Año inicio", 2000)
click_streamlit_button(page, "Iniciar Análisis")
move_streamlit_slider(page, "Máximo de páginas web", 100)

# Wait for analysis
wait_for_analysis_complete(page, timeout=120000)

# Extract data
value = get_metric_value(page, "Total de Páginas")

# Documentation
take_screenshot(page, "test_step")
```

## 🎨 Writing New Tests

### Basic Template

```python
import pytest
from playwright.sync_api import Page, expect
from .conftest import wait_for_streamlit_ready

class TestMyFeature:
    """Description of test suite"""
    
    def test_my_feature(self, page: Page):
        """Test description"""
        # Test implementation
        expect(page.locator("text=Expected")).to_be_visible()
```

### Example Tests

See `e2e/test_example.py` for comprehensive examples including:
- Basic UI checks
- User interactions
- Button clicks
- Input validation
- Parametrized tests
- Error handling
- Screenshot documentation

## 📸 Screenshots

Tests automatically capture screenshots on failure:
- Saved to `tests/screenshots/`
- Timestamped filenames
- Full-page captures

Manual screenshots:
```python
take_screenshot(page, "my_test_step")
```

## 🐛 Troubleshooting

### App won't start
```bash
# Test manually
streamlit run streamlit_app.py

# Check port
lsof -i :8501
```

### Tests timeout
```bash
# Increase timeout in tests/e2e/conftest.py
STREAMLIT_TIMEOUT = 60000  # 60 seconds

# Check network (needs Internet Archive)
curl -I https://web.archive.org/
```

### Element not found
```bash
# Use Playwright Inspector
PWDEBUG=1 pytest tests/e2e/test_smoke.py::test_name

# Check screenshots
ls tests/screenshots/
```

## ✅ Verification

Verify your test setup:

```bash
./verify_test_setup.sh
```

## 📞 Getting Help

1. **Check documentation** - See TESTING.md for comprehensive guide
2. **Review examples** - See test_example.py for patterns
3. **Check screenshots** - View tests/screenshots/ for visual debugging
4. **Use inspector** - Run with PWDEBUG=1 for interactive debugging

## 🎓 Best Practices

1. ✅ **Start with smoke tests** - Quick verification
2. ✅ **Use proper waits** - `wait_for_streamlit_ready()`
3. ✅ **Take screenshots** - Document test steps
4. ✅ **Mark tests appropriately** - Use `@pytest.mark.smoke/slow`
5. ✅ **Keep tests isolated** - Each test independent
6. ✅ **Use descriptive names** - Clear test purposes
7. ✅ **Test realistically** - Reasonable data sizes

## 🎯 Next Steps

### To run your first test:

```bash
# 1. Verify setup
./verify_test_setup.sh

# 2. Run smoke tests
./run_tests.sh --smoke --headed

# 3. Review screenshots
ls tests/screenshots/

# 4. Read the guide
cat tests/TESTING.md
```

### To add custom tests:

1. Create new file in `tests/e2e/`
2. Use examples from `test_example.py`
3. Import utilities from `conftest.py`
4. Run and verify: `pytest tests/e2e/your_test.py -v`

---

**🎉 Test suite ready to use!**

Start with: `./run_tests.sh --smoke --headed`

For full documentation, see [TESTING.md](TESTING.md)
