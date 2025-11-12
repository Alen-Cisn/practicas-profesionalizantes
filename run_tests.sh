#!/bin/bash
# Quick start script for running Playwright E2E tests
# Usage: ./run_tests.sh [options]

set -e

echo "🧪 Historical Term Analyzer - E2E Test Runner"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv311" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3.11 -m venv venv311
fi

# Activate virtual environment
source venv311/bin/activate

# Check if playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install pytest pytest-playwright playwright
    
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium
fi

# Parse command line arguments
TEST_PATH="tests/e2e/"
PYTEST_ARGS="-v"
BROWSER="chromium"
HEADED=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            HEADED="--headed"
            shift
            ;;
        --slow)
            PYTEST_ARGS="$PYTEST_ARGS --slowmo 500"
            shift
            ;;
        --smoke)
            PYTEST_ARGS="$PYTEST_ARGS -m smoke"
            shift
            ;;
        --no-slow)
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            shift
            ;;
        --ui)
            TEST_PATH="tests/e2e/test_streamlit_ui.py"
            shift
            ;;
        --workflow)
            TEST_PATH="tests/e2e/test_analysis_workflow.py"
            shift
            ;;
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        --help)
            echo ""
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --headed      Run tests with visible browser"
            echo "  --slow        Slow down browser operations (500ms)"
            echo "  --smoke       Run only smoke tests"
            echo "  --no-slow     Skip slow tests"
            echo "  --ui          Run only UI tests"
            echo "  --workflow    Run only workflow tests"
            echo "  --browser     Specify browser (chromium|firefox|webkit)"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --headed           # Show browser"
            echo "  ./run_tests.sh --smoke            # Quick smoke tests"
            echo "  ./run_tests.sh --no-slow          # Skip slow tests"
            echo "  ./run_tests.sh --ui --headed      # UI tests with browser"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo "🎯 Running tests with:"
echo "   Path: $TEST_PATH"
echo "   Browser: $BROWSER"
echo "   Mode: $([ -z "$HEADED" ] && echo "headless" || echo "headed")"
echo ""

# Run tests
pytest $TEST_PATH $PYTEST_ARGS $HEADED --browser $BROWSER

echo ""
echo "✅ Tests completed!"
echo ""
echo "📸 Screenshots saved to: tests/screenshots/"
