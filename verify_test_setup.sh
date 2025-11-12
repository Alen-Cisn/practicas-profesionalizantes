#!/bin/bash
# Verification script for Playwright test setup
# Checks that all required components are in place

echo "🔍 Playwright Test Suite - Setup Verification"
echo "=============================================="
echo ""

ERRORS=0

# Check Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python found: $PYTHON_VERSION"
else
    echo "   ❌ Python not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check if venv exists
echo "2️⃣  Checking virtual environment..."
if [ -d "venv311" ]; then
    echo "   ✅ Virtual environment exists: venv311/"
else
    echo "   ⚠️  Virtual environment not found: venv311/"
    echo "      Run: python3.11 -m venv venv311"
fi
echo ""

# Check test files
echo "3️⃣  Checking test files..."
TEST_FILES=(
    "tests/conftest.py"
    "tests/e2e/conftest.py"
    "tests/e2e/test_smoke.py"
    "tests/e2e/test_streamlit_ui.py"
    "tests/e2e/test_analysis_workflow.py"
    "tests/e2e/test_example.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check configuration files
echo "4️⃣  Checking configuration files..."
CONFIG_FILES=(
    "pytest.ini"
    "run_tests.sh"
    "requirements.txt"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check documentation
echo "5️⃣  Checking documentation..."
DOC_FILES=(
    "tests/TESTING.md"
    "tests/e2e/README.md"
    "tests/SETUP_COMPLETE.md"
    "PLAYWRIGHT_IMPLEMENTATION.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check if pytest is installed
echo "6️⃣  Checking pytest installation..."
if python3 -c "import pytest" 2>/dev/null; then
    PYTEST_VERSION=$(python3 -c "import pytest; print(pytest.__version__)")
    echo "   ✅ pytest installed: $PYTEST_VERSION"
else
    echo "   ⚠️  pytest not installed"
    echo "      Run: pip install -r requirements.txt"
fi
echo ""

# Check if playwright is installed
echo "7️⃣  Checking playwright installation..."
if python3 -c "import playwright" 2>/dev/null; then
    echo "   ✅ playwright package installed"
    
    # Check if browsers are installed
    if command -v playwright &> /dev/null; then
        echo "   ℹ️  To install browsers, run: playwright install chromium"
    fi
else
    echo "   ⚠️  playwright not installed"
    echo "      Run: pip install -r requirements.txt"
    echo "      Then: playwright install chromium"
fi
echo ""

# Check streamlit
echo "8️⃣  Checking streamlit installation..."
if python3 -c "import streamlit" 2>/dev/null; then
    STREAMLIT_VERSION=$(python3 -c "import streamlit; print(streamlit.__version__)")
    echo "   ✅ streamlit installed: $STREAMLIT_VERSION"
else
    echo "   ⚠️  streamlit not installed"
    echo "      Run: pip install -r requirements.txt"
fi
echo ""

# Check main app file
echo "9️⃣  Checking application files..."
APP_FILES=(
    "streamlit_app.py"
    "historical_term_analyzer.py"
)

for file in "${APP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Summary
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Setup verification PASSED!"
    echo ""
    echo "🚀 Ready to run tests:"
    echo "   ./run_tests.sh --smoke --headed"
    echo ""
    echo "📚 Read the docs:"
    echo "   - tests/SETUP_COMPLETE.md (quick start)"
    echo "   - tests/TESTING.md (comprehensive guide)"
    echo "   - PLAYWRIGHT_IMPLEMENTATION.md (summary)"
    echo ""
else
    echo "⚠️  Setup verification found $ERRORS error(s)"
    echo ""
    echo "Please fix the issues above before running tests."
fi
echo "=============================================="
