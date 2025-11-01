# Performance Monitoring Contract

**Feature**: 001-performance-playwright-tests  
**Date**: 2025-10-31  
**Version**: 1.0.0

## Overview

This document defines the interfaces and contracts for performance monitoring, caching, and test execution. These contracts ensure consistent interaction between components while maintaining the modular architecture principle.

## 1. CacheManager Interface

Manages multi-level caching for parsed HTML and extracted terms.

### Methods

#### `get(cache_key: str, cache_type: str) -> Optional[Any]`

Retrieves cached data by key and type.

**Parameters**:

- `cache_key`: Unique identifier (content hash)
- `cache_type`: Type of cached data ("parsed_html", "extracted_terms", "api_response")

**Returns**:

- Cached data if found and valid
- `None` if not found or expired

**Side Effects**:

- Updates `last_accessed` timestamp
- Increments `access_count`

**Example**:

```python
cached_soup = cache_manager.get("sha256_abc123", "parsed_html")
if cached_soup is None:
    # Cache miss - proceed with parsing
    pass
```

#### `put(cache_key: str, cache_type: str, data: Any, size_bytes: int) -> bool`

Stores data in cache with LRU management.

**Parameters**:

- `cache_key`: Unique identifier for cached content
- `cache_type`: Type of cached data
- `data`: The actual content to cache
- `size_bytes`: Memory footprint estimate

**Returns**:

- `True` if successfully cached
- `False` if cache is full and entry couldn't be evicted

**Side Effects**:

- May evict LRU entries if memory threshold exceeded
- Updates cache statistics

**Constraints**:

- Total cache size must not exceed 450MB
- Individual entry size must not exceed 10MB

**Example**:

```python
success = cache_manager.put(
    cache_key="sha256_abc123",
    cache_type="parsed_html",
    data=soup_object,
    size_bytes=524288
)
```

#### `invalidate(cache_key: str, cache_type: str) -> bool`

Removes specific cache entry.

**Parameters**:

- `cache_key`: Key to invalidate
- `cache_type`: Type of cache

**Returns**:

- `True` if entry was found and removed
- `False` if entry didn't exist

**Example**:

```python
cache_manager.invalidate("sha256_abc123", "parsed_html")
```

#### `clear(cache_type: Optional[str] = None) -> int`

Clears all or specific type of cache entries.

**Parameters**:

- `cache_type`: If provided, only clears this type; otherwise clears all

**Returns**:

- Number of entries cleared

**Example**:

```python
# Clear all caches
total_cleared = cache_manager.clear()

# Clear only parsed HTML cache
html_cleared = cache_manager.clear("parsed_html")
```

#### `get_statistics() -> dict`

Returns current cache statistics.

**Returns**:

```python
{
    "total_entries": int,
    "total_size_bytes": int,
    "hit_count": int,
    "miss_count": int,
    "hit_rate_percent": float,
    "by_type": {
        "parsed_html": {"entries": int, "size_bytes": int},
        "extracted_terms": {"entries": int, "size_bytes": int}
    }
}
```

**Example**:

```python
stats = cache_manager.get_statistics()
print(f"Cache hit rate: {stats['hit_rate_percent']:.1f}%")
```

## 2. PerformanceMonitor Interface

Tracks and reports performance metrics during analysis.

### Methods

#### `start_phase(phase_name: str) -> str`

Marks the beginning of an analysis phase.

**Parameters**:

- `phase_name`: Name of the phase ("search", "download", "parse", "analyze", "visualize")

**Returns**:

- Phase identifier for later reference

**Side Effects**:

- Records start timestamp
- Initializes phase metrics

**Example**:

```python
phase_id = monitor.start_phase("download")
# ... perform download operations ...
monitor.end_phase(phase_id)
```

#### `end_phase(phase_id: str) -> float`

Marks the end of an analysis phase.

**Parameters**:

- `phase_id`: Identifier returned by `start_phase`

**Returns**:

- Phase duration in seconds

**Side Effects**:

- Records end timestamp
- Calculates phase duration
- Stores PerformanceMetric

**Example**:

```python
duration = monitor.end_phase(phase_id)
print(f"Phase completed in {duration:.2f} seconds")
```

#### `record_metric(metric_type: str, value: float, unit: str, phase: str) -> None`

Records a custom performance metric.

**Parameters**:

- `metric_type`: Type of metric ("memory_usage", "cache_hit_rate", "request_count", etc.)
- `value`: Numeric measurement
- `unit`: Unit of measurement ("MB", "percentage", "count", etc.)
- `phase`: Associated analysis phase

**Example**:

```python
monitor.record_metric("memory_usage", 423.5, "MB", "parse")
monitor.record_metric("cache_hit_rate", 45.2, "percentage", "parse")
```

#### `get_metrics(analysis_id: str) -> List[PerformanceMetric]`

Retrieves all metrics for an analysis.

**Parameters**:

- `analysis_id`: Analysis identifier

**Returns**:

- List of PerformanceMetric objects

**Example**:

```python
metrics = monitor.get_metrics("analysis_20251031_143000")
for metric in metrics:
    print(f"{metric.phase}: {metric.value} {metric.unit}")
```

#### `get_summary(analysis_id: str) -> dict`

Returns aggregated performance summary.

**Returns**:

```python
{
    "total_duration_seconds": float,
    "memory_peak_mb": float,
    "cache_hit_rate_percent": float,
    "total_requests": int,
    "phases": {
        "search": {"duration_seconds": float},
        "download": {"duration_seconds": float},
        "parse": {"duration_seconds": float},
        "analyze": {"duration_seconds": float},
        "visualize": {"duration_seconds": float}
    }
}
```

**Example**:

```python
summary = monitor.get_summary("analysis_20251031_143000")
print(f"Total time: {summary['total_duration_seconds']:.1f}s")
print(f"Cache hit rate: {summary['cache_hit_rate_percent']:.1f}%")
```

## 3. WorkerPoolManager Interface

Manages dynamic parallel processing workers.

### Methods

#### `create_pool(pool_type: str, workload_size: int) -> WorkerPool`

Creates optimized worker pool based on workload type.

**Parameters**:

- `pool_type`: "io_bound" or "cpu_bound"
- `workload_size`: Expected number of tasks

**Returns**:

- Configured WorkerPool instance

**Logic**:

```python
if pool_type == "io_bound":
    max_workers = min(cpu_count * 4, 32, workload_size)
elif pool_type == "cpu_bound":
    max_workers = min(cpu_count, workload_size)
```

**Example**:

```python
# For downloading 300 web pages (I/O bound)
io_pool = pool_manager.create_pool("io_bound", 300)

# For parsing HTML (CPU bound)
cpu_pool = pool_manager.create_pool("cpu_bound", 300)
```

#### `submit_task(pool: WorkerPool, task_fn: Callable, *args, **kwargs) -> Future`

Submits task to worker pool.

**Parameters**:

- `pool`: WorkerPool instance
- `task_fn`: Function to execute
- `*args, **kwargs`: Function arguments

**Returns**:

- Future object for result retrieval

**Example**:

```python
future = pool_manager.submit_task(
    io_pool,
    download_webpage,
    url="http://example.com"
)
result = future.result(timeout=60)
```

#### `shutdown(pool: WorkerPool, wait: bool = True) -> None`

Gracefully shuts down worker pool.

**Parameters**:

- `pool`: WorkerPool to shutdown
- `wait`: If True, blocks until all tasks complete

**Side Effects**:

- Cancels pending tasks if wait=False
- Releases worker resources

**Example**:

```python
pool_manager.shutdown(io_pool, wait=True)
```

## 4. TestRunner Interface

Executes Playwright E2E tests with mocking and reporting.

### Methods

#### `register_scenario(scenario: TestScenario) -> None`

Registers a test scenario for execution.

**Parameters**:

- `scenario`: TestScenario object with test definition

**Example**:

```python
scenario = TestScenario(
    scenario_id="test_001",
    name="Analysis workflow",
    workflow="analysis",
    ...
)
runner.register_scenario(scenario)
```

#### `run_scenario(scenario_id: str, headless: bool = True) -> TestResult`

Executes a single test scenario.

**Parameters**:

- `scenario_id`: Scenario identifier
- `headless`: Run browser in headless mode

**Returns**:

- TestResult with execution outcome

**Side Effects**:

- Launches browser
- Captures screenshots on failure
- Records console logs

**Example**:

```python
result = runner.run_scenario("test_001", headless=True)
assert result.status == "passed"
```

#### `run_all(filter_tags: Optional[List[str]] = None, headless: bool = True) -> List[TestResult]`

Executes all registered scenarios, optionally filtered by tags.

**Parameters**:

- `filter_tags`: Only run scenarios with these tags
- `headless`: Run browser in headless mode

**Returns**:

- List of TestResult objects

**Example**:

```python
# Run only critical tests
results = runner.run_all(filter_tags=["critical"], headless=True)

# Run all tests
all_results = runner.run_all()
```

#### `generate_report(results: List[TestResult], format: str = "html") -> str`

Generates test execution report.

**Parameters**:

- `results`: List of TestResult objects
- `format`: Report format ("html", "json", "markdown")

**Returns**:

- Report content as string

**Example**:

```python
results = runner.run_all()
html_report = runner.generate_report(results, format="html")
with open("test-report.html", "w") as f:
    f.write(html_report)
```

## 5. Callback Interfaces

Progress callbacks for frontend integration.

### ProgressCallback

Function signature for progress updates:

```python
def progress_callback(
    progress_percent: float,
    status_message: str,
    phase: str
) -> None:
    """
    Called periodically during analysis execution.
    
    Args:
        progress_percent: 0-100 indicating completion
        status_message: Human-readable status description
        phase: Current phase name
    """
    pass
```

**Example Implementation** (Streamlit):

```python
def update_progress(progress: float, message: str, phase: str):
    st.session_state.progress = progress
    st.session_state.status = message
    st.rerun()

analyzer = HistoricalTermAnalyzer(progress_callback=update_progress)
```

## Contract Validation

### Type Checking

All interfaces should be validated with Python type hints:

```python
from typing import Protocol, Optional, List, Callable, Any

class CacheManagerProtocol(Protocol):
    def get(self, cache_key: str, cache_type: str) -> Optional[Any]: ...
    def put(self, cache_key: str, cache_type: str, data: Any, size_bytes: int) -> bool: ...
    # ... other methods
```

### Error Handling

All methods must raise appropriate exceptions:

- `CacheFullError`: When cache exceeds memory threshold
- `InvalidCacheKeyError`: When cache key format is invalid
- `PhaseNotFoundError`: When phase_id doesn't exist
- `TestTimeoutError`: When test exceeds timeout

### Testing Contracts

Mock implementations must adhere to contracts:

```python
class MockCacheManager:
    """Test double for CacheManager"""
    def __init__(self):
        self._cache = {}
    
    def get(self, cache_key: str, cache_type: str) -> Optional[Any]:
        return self._cache.get((cache_key, cache_type))
    
    # ... implement all interface methods
```

## Next Steps

Contracts defined. Proceed to:

1. Generate quickstart.md (developer setup guide)
2. Update agent context with new interfaces
3. Phase 2: Generate tasks.md for implementation
