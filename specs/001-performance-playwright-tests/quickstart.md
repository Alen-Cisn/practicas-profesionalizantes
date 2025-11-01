# Quick Start: Performance Optimization & E2E Testing

**Feature**: 001-performance-playwright-tests  
**Date**: 2025-10-31  
**For**: Developers implementing and testing performance improvements

## Prerequisites

- Python 3.8 or higher
- 4+ CPU cores recommended for optimal parallel processing
- 8GB RAM minimum
- Chrome/Chromium browser (for Playwright tests)

## Installation

### 1. Install Dependencies

```bash
cd /home/alen/projects/practicas-profesionalizantes

# Install performance and testing dependencies
pip install playwright==1.40.0 pytest-playwright==0.4.3 pytest==7.4.3

# Install Playwright browsers (Chromium for tests)
playwright install chromium
```

### 2. Verify Installation

```bash
# Verify Playwright installation
playwright --version

# Run existing tests to ensure baseline
python -m unittest discover
```

## Running the Application

### Standard Mode (Current Baseline)

```bash
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501`

**Baseline Performance** (for comparison):

- 300-page analysis: 20-25 minutes
- 500-page analysis: 35-45 minutes
- Memory usage: 500-700MB+

### Optimized Mode (After Implementation)

```bash
# Run with performance optimizations enabled
ENABLE_PERFORMANCE_OPTS=1 streamlit run streamlit_app.py
```

**Expected Performance**:

- 300-page analysis: ≤15 minutes (30-40% faster)
- 500-page analysis: ≤25 minutes (30-44% faster)
- Memory usage: <500MB (stable)

### Performance Monitoring

Enable detailed performance metrics:

```bash
# Run with performance profiling
ENABLE_PERF_MONITORING=1 ENABLE_PERFORMANCE_OPTS=1 streamlit run streamlit_app.py
```

Access performance dashboard in the app sidebar to view:

- Real-time execution time by phase
- Memory usage graphs
- Cache hit/miss rates
- Worker pool utilization

## Running E2E Tests

### Local Development

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_analysis_workflow.py -v

# Run tests with specific tags
pytest tests/e2e/ -v -m critical

# Run with visible browser (non-headless)
pytest tests/e2e/ -v --headed

# Run with screenshots on all tests (not just failures)
pytest tests/e2e/ -v --screenshot=on
```

### Test Output

Test results are saved to:

- Screenshots: `tests/screenshots/`
- Videos: `tests/videos/` (on failure)
- Reports: `test-results/`

### Viewing Test Results

```bash
# Generate HTML report
pytest tests/e2e/ --html=report.html --self-contained-html

# Open report in browser
open report.html  # macOS
xdg-open report.html  # Linux
start report.html  # Windows
```

## Development Workflow

### 1. Implement Performance Optimization

Example: Adding caching to HTML parsing

```python
# performance/cache_manager.py
from functools import lru_cache
import hashlib

class CacheManager:
    def __init__(self, max_size_mb=450):
        self.max_size_mb = max_size_mb
        self._cache = {}
    
    @lru_cache(maxsize=1000)
    def get_parsed_html(self, content_hash: str, html_content: str):
        """Cache parsed BeautifulSoup objects"""
        from bs4 import BeautifulSoup
        return BeautifulSoup(html_content, 'lxml')

# historical_term_analyzer.py (modify existing)
from performance.cache_manager import CacheManager

class InternetArchiveClient:
    def __init__(self, enable_cache=True):
        self.cache = CacheManager() if enable_cache else None
    
    def parse_html(self, html_content: str):
        if self.cache:
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()
            return self.cache.get_parsed_html(content_hash, html_content)
        # Fallback to direct parsing
        return BeautifulSoup(html_content, 'lxml')
```

### 2. Measure Performance Impact

```python
# Run performance benchmarks
python tests/benchmarks/measure_performance.py --iterations=5 --pages=300

# Compare with baseline
python tests/benchmarks/compare_baseline.py
```

### 3. Write E2E Test

Create test for new feature:

```python
# tests/e2e/test_caching.py
import pytest
from playwright.sync_api import Page, expect

def test_cache_improves_performance(page: Page, mock_cdx_api):
    """Verify caching reduces execution time for repeated analyses"""
    
    # Run first analysis (cold cache)
    page.goto("http://localhost:8501")
    page.click("text=Execute Analysis")
    
    # Measure first run time
    start_time = time.time()
    page.wait_for_selector("text=Analysis Complete", timeout=600000)
    first_run_time = time.time() - start_time
    
    # Run second analysis with same parameters (warm cache)
    page.click("text=Execute Analysis")
    start_time = time.time()
    page.wait_for_selector("text=Analysis Complete", timeout=600000)
    second_run_time = time.time() - start_time
    
    # Second run should be faster due to caching
    assert second_run_time < first_run_time * 0.8  # At least 20% faster
```

### 4. Verify Test Passes

```bash
# Run new test
pytest tests/e2e/test_caching.py -v --headed

# Run full suite to check for regressions
pytest tests/e2e/ -v
```

## Common Tasks

### Creating Test Fixtures

```bash
# Create new mock data for testing
cat > tests/fixtures/mock_cdx_small.json << EOF
{
  "cnn.com": {
    "2000": [
      ["20000115120000", "http://cnn.com/article1", "text/html", "200"],
      ["20000215140000", "http://cnn.com/article2", "text/html", "200"]
    ]
  }
}
EOF
```

### Debugging Test Failures

```bash
# Run with maximum verbosity
pytest tests/e2e/ -vv --tb=long

# Pause on failure for inspection
pytest tests/e2e/ --pdb

# Keep browser open on failure
pytest tests/e2e/ --headed --slowmo=1000

# Generate trace for debugging
pytest tests/e2e/ --tracing=on
```

### Profiling Performance

```python
# Profile specific function
python -m cProfile -o profile.stats historical_term_analyzer.py

# View profile
python -m pstats profile.stats
>>> sort cumtime
>>> stats 20

# Memory profiling
from memory_profiler import profile

@profile
def analyze_terms(documents):
    # Implementation
    pass
```

### Cache Management

```python
# Clear cache manually
from performance.cache_manager import CacheManager
cache = CacheManager()
cache.clear()

# View cache statistics
stats = cache.get_statistics()
print(f"Hit rate: {stats['hit_rate_percent']:.1f}%")
print(f"Total size: {stats['total_size_bytes'] / 1024 / 1024:.1f} MB")
```

## Continuous Integration

### GitHub Actions Workflow

Tests run automatically on every push and PR.

View results: `https://github.com/Alen-Cisn/practicas-profesionalizantes/actions`

### Local CI Simulation

```bash
# Run tests as CI would
pytest tests/e2e/ --headless --screenshot=only-on-failure --video=retain-on-failure

# Check exit code
echo $?  # Should be 0 for passing tests
```

## Troubleshooting

### Tests Timing Out

If tests timeout:

1. Increase timeout in test:

```python
page.wait_for_selector("text=Complete", timeout=900000)  # 15 minutes
```

2. Use mock data to avoid real API calls
3. Reduce test workload (fewer pages)

### Browser Not Found

```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

### Memory Issues During Tests

```bash
# Run tests one at a time to reduce memory pressure
pytest tests/e2e/ -v --maxfail=1

# Reduce parallel test execution
pytest tests/e2e/ -v -n 1
```

### Cache Not Working

Check environment variable:

```bash
# Verify performance opts are enabled
echo $ENABLE_PERFORMANCE_OPTS

# Enable explicitly
export ENABLE_PERFORMANCE_OPTS=1
streamlit run streamlit_app.py
```

## Performance Benchmarks

### Running Benchmarks

```bash
# Quick benchmark (100 pages)
python tests/benchmarks/quick_bench.py

# Full benchmark (300 pages, 5 iterations)
python tests/benchmarks/full_bench.py

# Memory benchmark
python tests/benchmarks/memory_bench.py
```

### Expected Results

| Configuration | 300 Pages | 500 Pages | Memory Peak |
|--------------|-----------|-----------|-------------|
| Baseline (no opts) | 20-25 min | 35-45 min | 600-700 MB |
| With caching | 16-20 min | 28-36 min | 450-550 MB |
| Full optimizations | ≤15 min | ≤25 min | <500 MB |

## Next Steps

1. **Implement Performance Module**: Start with `performance/cache_manager.py`
2. **Update Analyzer**: Integrate caching into `historical_term_analyzer.py`
3. **Create E2E Tests**: Write tests in `tests/e2e/`
4. **Run Benchmarks**: Measure improvements
5. **Update Documentation**: Document new features in `GUIA_USO.md`

## Resources

- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [pytest-playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)

## Support

For issues or questions:

1. Check existing tests for examples
2. Review performance benchmarks for expected behavior
3. Consult research.md for implementation details
4. Check contracts/performance-monitoring.md for interface definitions
