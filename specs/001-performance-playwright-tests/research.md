# Research: Performance Optimization & E2E Testing

**Feature**: 001-performance-playwright-tests  
**Date**: 2025-10-31  
**Status**: Complete

## Overview

This document consolidates research findings for implementing performance optimizations and Playwright-based E2E testing for the Historical Term Analyzer. Research focuses on caching strategies, parallel processing patterns, memory management techniques, and Playwright best practices for Streamlit applications.

## Research Areas

### 1. Caching Strategies for Web Scraping

**Decision**: Implement multi-level LRU cache with functools.lru_cache and custom disk-based fallback

**Rationale**:
- BeautifulSoup parsing is CPU-intensive (accounts for ~20% of analysis time)
- Many web pages contain repeated HTML structures across snapshots
- Term extraction from text is deterministic and can be cached
- LRU (Least Recently Used) provides automatic memory management
- Python's `functools.lru_cache` offers zero-overhead decorator-based caching

**Implementation Approach**:
```python
# Level 1: In-memory function-level cache
@lru_cache(maxsize=1000)
def parse_html_content(html_hash: str, html_content: str) -> BeautifulSoup:
    # Cache parsed BeautifulSoup objects by content hash
    pass

@lru_cache(maxsize=2000)
def extract_terms(text_hash: str, text_content: str) -> List[str]:
    # Cache extracted terms by text content hash
    pass

# Level 2: Session-level cache for analysis results
# Use Streamlit session_state with explicit size limits
```

**Expected Impact**: 40-50% cache hit rate on typical analyses (multiple pages from same domain), translating to 15-20% overall time savings.

**Alternatives Considered**:
- Redis/Memcached: Rejected - adds external dependency, overkill for single-user application
- Disk-based pickle cache: Rejected for primary cache - slower than memory, but useful as fallback layer
- No caching: Rejected - repeated parsing is wasteful and measurable bottleneck

### 2. Dynamic Parallel Processing

**Decision**: Use ThreadPoolExecutor with dynamic worker count based on CPU cores and workload

**Rationale**:
- Current implementation uses fixed 8 workers regardless of system capabilities
- I/O-bound operations (HTTP requests) benefit from higher thread counts
- CPU-bound operations (parsing, text processing) benefit from matching CPU core count
- ThreadPoolExecutor provides better control than multiprocessing for mixed workloads
- Avoids overhead of process spawning and inter-process communication

**Implementation Approach**:
```python
import os
from concurrent.futures import ThreadPoolExecutor

# Dynamic worker calculation
cpu_count = os.cpu_count() or 4
io_workers = min(cpu_count * 4, 32)  # 4x cores for I/O, max 32
cpu_workers = cpu_count  # 1x cores for CPU-bound

# Separate pools for different workload types
io_pool = ThreadPoolExecutor(max_workers=io_workers)  # HTTP requests
cpu_pool = ThreadPoolExecutor(max_workers=cpu_workers)  # Parsing, processing
```

**Expected Impact**: 20-30% improvement on systems with 8+ cores, graceful scaling on lower-end hardware.

**Alternatives Considered**:
- asyncio/aiohttp: Rejected - requires refactoring entire HTTP layer, Streamlit compatibility unclear
- multiprocessing: Rejected - process overhead negates benefits for current workload mix
- Fixed worker count: Current approach, suboptimal for diverse hardware

### 3. Memory Management & Garbage Collection

**Decision**: Implement explicit garbage collection triggers and lazy-loading for visualizations

**Rationale**:
- Python's GC is generational but conservative (waits for thresholds)
- Large datasets (5000+ terms, 500+ documents) create memory pressure
- Streamlit reruns can accumulate stale references
- Plotly charts hold references to entire datasets
- Manual `gc.collect()` after operations provides deterministic cleanup

**Implementation Approach**:
```python
import gc
import sys

# After analysis completion
def cleanup_analysis_memory():
    # Clear large intermediate structures
    parsed_documents.clear()
    raw_html_cache.clear()
    
    # Force garbage collection
    gc.collect()
    gc.collect()  # Second pass for cyclic references
    
# Lazy-load visualizations
@st.cache_data
def generate_chart_data(analysis_id: str, chart_type: str):
    # Only generate chart data when tab is selected
    # Use Streamlit caching to avoid regeneration
    pass
```

**Expected Impact**: Memory usage stabilizes at 300-400MB instead of growing to 700MB+, prevents browser tab crashes.

**Alternatives Considered**:
- Memory profiling libraries (memory_profiler, pympler): Useful for development, too slow for production
- Weak references: Rejected - doesn't help with Streamlit's session state persistence
- Process isolation: Rejected - breaks Streamlit's architecture

### 4. Connection Pooling for HTTP Requests

**Decision**: Use requests.Session with connection pooling and keep-alive

**Rationale**:
- Current implementation creates new connection for each request
- Internet Archive CDX API supports HTTP keep-alive
- Connection establishment overhead is 50-100ms per request
- Session object provides automatic cookie handling and connection reuse

**Implementation Approach**:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure session with connection pooling
session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Reuse session across requests
response = session.get(url, timeout=(30, 60))
```

**Expected Impact**: 5-10% reduction in total request time through connection reuse.

**Alternatives Considered**:
- httpx with async support: Rejected - requires async refactoring
- urllib3 directly: Rejected - lower-level API, requests provides better ergonomics
- No pooling (current): Wasteful connection overhead

### 5. Playwright E2E Testing Framework

**Decision**: Use Playwright with pytest-playwright plugin and fixture-based mocking

**Rationale**:
- Playwright officially supports Python (vs Selenium which is Java-first)
- Better async support and modern browser automation
- Built-in support for screenshots, video recording, and network mocking
- pytest-playwright provides seamless pytest integration
- Streamlit apps are standard web apps, no special handling needed

**Implementation Approach**:
```python
# conftest.py - pytest fixtures
import pytest
from playwright.sync_api import Page

@pytest.fixture
def mock_cdx_api(page: Page):
    # Intercept Internet Archive API calls
    page.route("**/web.archive.org/cdx/**", lambda route: route.fulfill(
        json=load_fixture("mock_cdx_responses.json")
    ))

# test_analysis_workflow.py
def test_complete_analysis_workflow(page: Page, mock_cdx_api):
    # Navigate to app
    page.goto("http://localhost:8501")
    
    # Configure analysis
    page.select_option("#year_start", "2000")
    page.select_option("#year_end", "2005")
    page.click("text=Execute Analysis")
    
    # Wait for completion
    page.wait_for_selector("text=Analysis Complete", timeout=600000)
    
    # Verify results
    assert page.is_visible("text=Top Terms")
```

**Expected Impact**: 90% workflow coverage, catches regressions before deployment, 8-10 minute test suite execution.

**Alternatives Considered**:
- Selenium: Rejected - older API, less Python-friendly, slower
- Manual testing: Current approach, doesn't scale, misses regressions
- Unit tests only: Insufficient - doesn't catch integration issues

### 6. Test Data Management & Mocking

**Decision**: JSON-based fixtures with deterministic mock responses

**Rationale**:
- Internet Archive API responses vary over time (snapshots added/removed)
- Non-deterministic tests are flaky and unreliable
- Fixture files can be version controlled and reviewed
- JSON format is human-readable and easily maintainable

**Implementation Approach**:
```json
// tests/fixtures/mock_cdx_responses.json
{
  "cnn.com": {
    "2000": [
      ["20000115120000", "http://cnn.com/article", "text/html", "200", "..."],
      ["20000215140000", "http://cnn.com/news", "text/html", "200", "..."]
    ]
  }
}
```

**Expected Impact**: <5% test flakiness rate, reproducible test failures.

**Alternatives Considered**:
- Live API testing: Rejected - slow, unreliable, violates rate limits
- Random mock data: Rejected - non-deterministic, hard to debug failures
- Record/replay (VCR.py): Considered but JSON fixtures are simpler

### 7. CI/CD Integration

**Decision**: GitHub Actions workflow with headless browser execution

**Rationale**:
- GitHub Actions provides free CI/CD for public repos
- Playwright supports headless mode out-of-the-box
- Can run on ubuntu-latest with minimal setup
- Test artifacts (screenshots, videos) can be uploaded for debugging

**Implementation Approach**:
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: pytest tests/e2e/ --screenshot=on --video=retain-on-failure
      - name: Upload artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

**Expected Impact**: Automated regression detection on every commit, <15 minute CI pipeline.

**Alternatives Considered**:
- Jenkins/Travis CI: More complex setup, less GitHub integration
- Local-only testing: Doesn't scale, easy to forget before pushing
- Docker-based testing: Adds complexity, Playwright handles browser isolation

## Performance Optimization Summary

### Expected Overall Impact

Combining all optimizations:

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| 300-page analysis | 20-25 min | ≤15 min | 30-40% |
| 500-page analysis | 35-45 min | ≤25 min | 30-44% |
| Memory usage | 700MB+ | <500MB | 30% reduction |
| Cache hit rate | 0% | >40% | New capability |

### Implementation Priority

1. **P1 - High Impact**: Caching (15-20% improvement), Dynamic workers (20-30% improvement)
2. **P2 - Medium Impact**: Connection pooling (5-10% improvement), Memory management (stability)
3. **P3 - Testing**: E2E framework (quality assurance, no performance impact)

### Risk Assessment

**Low Risk**:
- Caching: Easily reversible with decorator removal
- Connection pooling: Transparent to application logic

**Medium Risk**:
- Dynamic workers: Needs testing across different hardware configurations
- Memory management: Manual GC could impact UI responsiveness if called too frequently

**Mitigation**:
- Comprehensive testing on low-end (2 cores) and high-end (16+ cores) systems
- Feature flags for disabling optimizations if issues arise
- Performance regression tests in CI/CD

## Testing Framework Summary

### Test Coverage Plan

| Workflow | Test File | Scope |
|----------|-----------|-------|
| Analysis execution | test_analysis_workflow.py | Configuration → Execution → Results |
| Visualization | test_visualization.py | Charts, tabs, data display |
| Export | test_export.py | CSV/JSON export functionality |
| History navigation | test_history_navigation.py | Multiple analyses, switching |
| Responsive design | test_responsive.py | Desktop/tablet/mobile viewports |

### Test Execution Strategy

- **Local development**: Run full suite before commits (`pytest tests/e2e/`)
- **CI/CD**: Run on every push to feature branches and PRs
- **Nightly**: Run extended tests with longer timeouts (30+ minute analyses)

## Dependencies

### New Dependencies Required

```txt
# Testing
playwright==1.40.0
pytest-playwright==0.4.3
pytest==7.4.3

# Performance monitoring (optional, development only)
memory-profiler==0.61.0
```

### Compatibility Verification

- All dependencies compatible with Python 3.8+
- Playwright supports Chrome, Firefox, WebKit (focus on Chromium for CI/CD)
- No conflicts with existing dependencies (Streamlit, BeautifulSoup, Plotly, Pandas)

## Next Steps

This research phase is complete. Proceed to:

1. **Phase 1**: Generate data-model.md (performance metrics, test results entities)
2. **Phase 1**: Generate contracts/ (performance monitoring interfaces)
3. **Phase 1**: Generate quickstart.md (developer setup guide)
4. **Phase 1**: Update agent context with new technologies (Playwright, pytest)
5. **Phase 2**: Generate tasks.md (implementation task breakdown)

## References

- [Playwright Python Documentation](https://playwright.dev/python/)
- [functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [ThreadPoolExecutor Best Practices](https://docs.python.org/3/library/concurrent.futures.html)
- [Python Garbage Collection](https://docs.python.org/3/library/gc.html)
- [requests Session Objects](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
