# Data Model: Performance Optimization & E2E Testing

**Feature**: 001-performance-playwright-tests  
**Date**: 2025-10-31  
**Status**: Complete

## Overview

This document defines the data models and entities required for implementing performance optimizations and E2E testing. Models focus on performance metrics, cache management, and test result representation.

## Core Entities

### 1. PerformanceMetric

Represents measurements of system performance during analysis execution.

**Attributes**:

- `metric_id`: str - Unique identifier for the metric measurement
- `analysis_id`: str - Reference to the analysis being measured
- `timestamp`: datetime - When the measurement was recorded
- `metric_type`: str - Type of metric (execution_time, memory_usage, cache_hit_rate, request_count)
- `value`: float - Numeric value of the measurement
- `unit`: str - Unit of measurement (seconds, MB, percentage, count)
- `phase`: str - Analysis phase (search, download, parse, analyze, visualize)

**Relationships**:

- Belongs to one Analysis (existing entity in application)
- Multiple metrics per analysis (time series)

**Validation Rules**:

- `metric_type` must be one of: execution_time, memory_usage, cache_hit_rate, request_count, worker_utilization
- `value` must be non-negative
- `timestamp` must be within analysis time range

**State Transitions**:

```
Created → Recording → Completed → Archived
```

**Example**:

```python
{
  "metric_id": "pm_001_exec_time",
  "analysis_id": "analysis_20251031_143022",
  "timestamp": "2025-10-31T14:30:45Z",
  "metric_type": "execution_time",
  "value": 892.5,
  "unit": "seconds",
  "phase": "download"
}
```

### 2. CacheEntry

Represents a cached computation result to avoid redundant processing.

**Attributes**:

- `cache_key`: str - Hash-based unique identifier for cached content
- `cache_type`: str - Type of cached data (parsed_html, extracted_terms, api_response)
- `content_hash`: str - SHA256 hash of original content for validation
- `cached_data`: Any - The actual cached result (BeautifulSoup object, list of terms, etc.)
- `created_at`: datetime - When the entry was cached
- `last_accessed`: datetime - Last access timestamp for LRU tracking
- `access_count`: int - Number of times this entry was accessed
- `size_bytes`: int - Memory footprint estimate
- `expires_at`: Optional[datetime] - Expiration timestamp (None for no expiration)

**Relationships**:

- Independent entity (no foreign key relationships)
- Managed by CacheManager service

**Validation Rules**:

- `cache_key` must be unique within cache_type
- `size_bytes` must be positive
- `access_count` must be non-negative
- `last_accessed` must be >= `created_at`

**State Transitions**:

```
Created → Active → Stale → Evicted
            ↓
         Accessed (updates last_accessed, increments access_count)
```

**Example**:

```python
{
  "cache_key": "html_sha256_abc123...",
  "cache_type": "parsed_html",
  "content_hash": "abc123def456...",
  "cached_data": "<BeautifulSoup object>",
  "created_at": "2025-10-31T14:25:10Z",
  "last_accessed": "2025-10-31T14:30:22Z",
  "access_count": 5,
  "size_bytes": 524288,
  "expires_at": None
}
```

### 3. TestScenario

Represents an automated E2E test case with setup, actions, and assertions.

**Attributes**:

- `scenario_id`: str - Unique identifier for the test scenario
- `name`: str - Human-readable test name
- `description`: str - Detailed test description
- `workflow`: str - User workflow being tested (analysis, visualization, export, history)
- `priority`: str - Test priority (critical, high, medium, low)
- `setup_fixtures`: List[str] - Fixture files required for test
- `actions`: List[dict] - Sequence of user actions (clicks, inputs, waits)
- `assertions`: List[dict] - Expected outcomes to validate
- `timeout_seconds`: int - Maximum execution time
- `viewport_size`: tuple - Browser viewport dimensions (width, height)
- `tags`: List[str] - Test categorization tags

**Relationships**:

- Has many TestResult instances (test execution history)
- References fixtures in tests/fixtures/

**Validation Rules**:

- `name` must be unique across scenarios
- `workflow` must be one of: analysis, visualization, export, history, responsive
- `priority` must be one of: critical, high, medium, low
- `timeout_seconds` must be positive
- `viewport_size` must be (width, height) tuple with positive integers

**State Transitions**:

```
Defined → Pending → Running → Passed/Failed → Archived
```

**Example**:

```python
{
  "scenario_id": "test_analysis_workflow_001",
  "name": "Complete 300-page analysis workflow",
  "description": "Validates end-to-end analysis from configuration to results display",
  "workflow": "analysis",
  "priority": "critical",
  "setup_fixtures": ["mock_cdx_responses.json", "mock_html_content.html"],
  "actions": [
    {"type": "navigate", "url": "http://localhost:8501"},
    {"type": "select", "selector": "#year_start", "value": "2000"},
    {"type": "select", "selector": "#year_end", "value": "2005"},
    {"type": "click", "selector": "text=Execute Analysis"},
    {"type": "wait", "selector": "text=Analysis Complete", "timeout": 600000}
  ],
  "assertions": [
    {"type": "visible", "selector": "text=Top Terms"},
    {"type": "visible", "selector": "text=Results by Year"}
  ],
  "timeout_seconds": 900,
  "viewport_size": (1920, 1080),
  "tags": ["critical", "workflow", "performance"]
}
```

### 4. TestResult

Represents the outcome of executing a TestScenario.

**Attributes**:

- `result_id`: str - Unique identifier for test execution result
- `scenario_id`: str - Reference to the TestScenario executed
- `execution_timestamp`: datetime - When the test was run
- `status`: str - Test outcome (passed, failed, skipped, error)
- `duration_seconds`: float - Test execution time
- `error_message`: Optional[str] - Error description if failed
- `screenshots`: List[str] - Paths to captured screenshots
- `logs`: List[dict] - Console logs and application logs
- `network_calls`: List[dict] - HTTP requests made during test
- `performance_metrics`: dict - Timing breakdown by phase
- `environment`: dict - Test environment details (Python version, browser, OS)

**Relationships**:

- Belongs to one TestScenario
- Contains multiple artifacts (screenshots, logs)

**Validation Rules**:

- `status` must be one of: passed, failed, skipped, error
- `duration_seconds` must be non-negative
- If `status` is failed or error, `error_message` must be present
- `screenshots` paths must exist in filesystem

**State Transitions**:

```
Queued → Running → Completed (passed/failed/error/skipped) → Archived
```

**Example**:

```python
{
  "result_id": "tr_20251031_143500",
  "scenario_id": "test_analysis_workflow_001",
  "execution_timestamp": "2025-10-31T14:35:00Z",
  "status": "passed",
  "duration_seconds": 845.2,
  "error_message": None,
  "screenshots": [
    "tests/screenshots/test_analysis_workflow_001_final.png"
  ],
  "logs": [
    {"level": "info", "message": "Analysis started", "timestamp": "2025-10-31T14:35:05Z"},
    {"level": "info", "message": "Analysis completed", "timestamp": "2025-10-31T14:49:05Z"}
  ],
  "network_calls": [
    {"url": "http://web.archive.org/cdx/...", "status": 200, "duration_ms": 250}
  ],
  "performance_metrics": {
    "search_time": 45.2,
    "download_time": 620.5,
    "parse_time": 125.3,
    "analyze_time": 54.2
  },
  "environment": {
    "python_version": "3.10.12",
    "browser": "chromium 119.0",
    "os": "Linux"
  }
}
```

### 5. WorkerPool

Represents the dynamic parallel processing configuration.

**Attributes**:

- `pool_id`: str - Unique identifier for worker pool instance
- `pool_type`: str - Type of workload (io_bound, cpu_bound)
- `max_workers`: int - Maximum number of concurrent workers
- `active_workers`: int - Currently active workers
- `queued_tasks`: int - Tasks waiting for execution
- `completed_tasks`: int - Tasks finished successfully
- `failed_tasks`: int - Tasks that failed
- `cpu_count`: int - Available CPU cores
- `utilization_percent`: float - Current CPU utilization

**Relationships**:

- Associated with one Analysis session
- Manages multiple task executions

**Validation Rules**:

- `max_workers` must be positive
- `active_workers` must be <= `max_workers`
- `utilization_percent` must be 0-100
- `pool_type` must be one of: io_bound, cpu_bound

**State Transitions**:

```
Initialized → Running → Scaling (up/down) → Shutdown
```

**Example**:

```python
{
  "pool_id": "wp_io_20251031_143000",
  "pool_type": "io_bound",
  "max_workers": 32,
  "active_workers": 28,
  "queued_tasks": 45,
  "completed_tasks": 180,
  "failed_tasks": 2,
  "cpu_count": 8,
  "utilization_percent": 87.5
}
```

## Data Relationships

```
Analysis (existing)
├── PerformanceMetric (1:N) - Multiple metrics per analysis
├── WorkerPool (1:1) - One pool per analysis session
└── CacheEntry (N:M) - Shared cache across analyses

TestScenario (1:N) → TestResult - One scenario, many executions
```

## Storage Considerations

### In-Memory Storage

- `CacheEntry`: Stored in memory with LRU eviction policy
- `PerformanceMetric`: Accumulated during analysis, flushed to session state
- `WorkerPool`: Active only during analysis execution

### Session State (Streamlit)

- Analysis results with embedded performance metrics
- Recent test results for CI/CD reporting
- Cache statistics for debugging

### File System

- Test artifacts (screenshots, logs) in `tests/screenshots/`
- Mock fixtures in `tests/fixtures/`
- Optional persistent cache in `.cache/` directory

### No Database Required

All entities are ephemeral or session-scoped. No persistent database needed for this feature.

## Serialization Requirements

All entities must be JSON-serializable for:

- Export functionality (CSV/JSON)
- CI/CD test result reporting
- Session state persistence
- Cache key generation (for hashing)

**Serialization Strategy**:

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional

@dataclass
class PerformanceMetric:
    metric_id: str
    analysis_id: str
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    phase: str
    
    def to_dict(self) -> dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PerformanceMetric':
        return cls(
            **{**data, 'timestamp': datetime.fromisoformat(data['timestamp'])}
        )
```

## Performance Considerations

### Memory Footprint Estimates

- `CacheEntry` (parsed HTML): ~500KB per entry, max 1000 entries = ~500MB
- `CacheEntry` (extracted terms): ~10KB per entry, max 2000 entries = ~20MB
- `PerformanceMetric`: ~1KB per metric, ~100 per analysis = ~100KB
- `TestResult`: ~500KB per result (with screenshots), max 50 retained = ~25MB

**Total estimated memory**: <600MB for typical usage, aligns with <500MB target.

### Cache Eviction Strategy

LRU (Least Recently Used) with memory threshold:

1. Track `last_accessed` timestamp and `access_count`
2. When memory exceeds 450MB, evict entries with oldest `last_accessed`
3. Never evict entries accessed in last 60 seconds (active analysis)
4. Clear entire cache on session end

## Validation & Constraints

### Business Rules

1. Performance metrics must be recorded for all analyses when optimization is enabled
2. Cache entries must be validated against content hash before use
3. Test results must be retained for at least 30 days in CI/CD
4. Failed tests must always capture screenshots and logs

### Data Integrity

1. Metric timestamps must be monotonically increasing within an analysis
2. Cache keys must use secure hash algorithm (SHA256)
3. Test scenario actions must be executable in sequence
4. Worker pool max_workers must not exceed system CPU count * 4

## Next Steps

Data models defined. Proceed to:

1. Generate contracts/ (performance monitoring interfaces)
2. Generate quickstart.md (developer setup guide)
3. Update agent context with new entities
