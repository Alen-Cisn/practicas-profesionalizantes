"""
Data Models for Performance Optimization & E2E Testing

Defines dataclasses for performance metrics, cache entries, worker pools,
test scenarios, and test results.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, List, Dict, Tuple
import json


@dataclass
class PerformanceMetric:
    """
    Represents measurements of system performance during analysis execution.
    
    Attributes:
        metric_id: Unique identifier for the metric measurement
        analysis_id: Reference to the analysis being measured
        timestamp: When the measurement was recorded
        metric_type: Type of metric (execution_time, memory_usage, cache_hit_rate, etc.)
        value: Numeric value of the measurement
        unit: Unit of measurement (seconds, MB, percentage, count)
        phase: Analysis phase (search, download, parse, analyze, visualize)
    """
    metric_id: str
    analysis_id: str
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    phase: str
    
    def __post_init__(self):
        """Validate metric data"""
        valid_types = ['execution_time', 'memory_usage', 'cache_hit_rate', 
                      'request_count', 'worker_utilization']
        if self.metric_type not in valid_types:
            raise ValueError(f"metric_type must be one of: {valid_types}")
        if self.value < 0:
            raise ValueError("value must be non-negative")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with ISO timestamp"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PerformanceMetric':
        """Create from dictionary with ISO timestamp"""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data_copy)


@dataclass
class CacheEntry:
    """
    Represents a cached computation result to avoid redundant processing.
    
    Attributes:
        cache_key: Hash-based unique identifier for cached content
        cache_type: Type of cached data (parsed_html, extracted_terms, api_response)
        content_hash: SHA256 hash of original content for validation
        cached_data: The actual cached result
        created_at: When the entry was cached
        last_accessed: Last access timestamp for LRU tracking
        access_count: Number of times this entry was accessed
        size_bytes: Memory footprint estimate
        expires_at: Optional expiration timestamp
    """
    cache_key: str
    cache_type: str
    content_hash: str
    cached_data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate cache entry data"""
        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be positive")
        if self.access_count < 0:
            raise ValueError("access_count must be non-negative")
        if self.last_accessed < self.created_at:
            raise ValueError("last_accessed must be >= created_at")
    
    def accessed(self):
        """Update access tracking"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class WorkerPool:
    """
    Represents the dynamic parallel processing configuration.
    
    Attributes:
        pool_id: Unique identifier for worker pool instance
        pool_type: Type of workload (io_bound, cpu_bound)
        max_workers: Maximum number of concurrent workers
        active_workers: Currently active workers
        queued_tasks: Tasks waiting for execution
        completed_tasks: Tasks finished successfully
        failed_tasks: Tasks that failed
        cpu_count: Available CPU cores
        utilization_percent: Current CPU utilization
    """
    pool_id: str
    pool_type: str
    max_workers: int
    active_workers: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cpu_count: int = 0
    utilization_percent: float = 0.0
    
    def __post_init__(self):
        """Validate worker pool data"""
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if self.active_workers > self.max_workers:
            raise ValueError("active_workers must be <= max_workers")
        if not 0 <= self.utilization_percent <= 100:
            raise ValueError("utilization_percent must be 0-100")
        valid_types = ['io_bound', 'cpu_bound']
        if self.pool_type not in valid_types:
            raise ValueError(f"pool_type must be one of: {valid_types}")


@dataclass
class TestScenario:
    """
    Represents an automated E2E test case with setup, actions, and assertions.
    
    Attributes:
        scenario_id: Unique identifier for the test scenario
        name: Human-readable test name
        description: Detailed test description
        workflow: User workflow being tested
        priority: Test priority
        setup_fixtures: Fixture files required for test
        actions: Sequence of user actions
        assertions: Expected outcomes to validate
        timeout_seconds: Maximum execution time
        viewport_size: Browser viewport dimensions (width, height)
        tags: Test categorization tags
    """
    scenario_id: str
    name: str
    description: str
    workflow: str
    priority: str
    setup_fixtures: List[str] = field(default_factory=list)
    actions: List[Dict] = field(default_factory=list)
    assertions: List[Dict] = field(default_factory=list)
    timeout_seconds: int = 600
    viewport_size: Tuple[int, int] = (1920, 1080)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate test scenario data"""
        valid_workflows = ['analysis', 'visualization', 'export', 'history', 'responsive']
        if self.workflow not in valid_workflows:
            raise ValueError(f"workflow must be one of: {valid_workflows}")
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if self.priority not in valid_priorities:
            raise ValueError(f"priority must be one of: {valid_priorities}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if len(self.viewport_size) != 2 or any(v <= 0 for v in self.viewport_size):
            raise ValueError("viewport_size must be (width, height) with positive integers")


@dataclass
class TestResult:
    """
    Represents the outcome of executing a TestScenario.
    
    Attributes:
        result_id: Unique identifier for test execution result
        scenario_id: Reference to the TestScenario executed
        execution_timestamp: When the test was run
        status: Test outcome (passed, failed, skipped, error)
        duration_seconds: Test execution time
        error_message: Error description if failed
        screenshots: Paths to captured screenshots
        logs: Console logs and application logs
        network_calls: HTTP requests made during test
        performance_metrics: Timing breakdown by phase
        environment: Test environment details
    """
    result_id: str
    scenario_id: str
    execution_timestamp: datetime
    status: str
    duration_seconds: float
    error_message: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[Dict] = field(default_factory=list)
    network_calls: List[Dict] = field(default_factory=list)
    performance_metrics: Dict = field(default_factory=dict)
    environment: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate test result data"""
        valid_statuses = ['passed', 'failed', 'skipped', 'error']
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of: {valid_statuses}")
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be non-negative")
        if self.status in ['failed', 'error'] and not self.error_message:
            raise ValueError("error_message must be present for failed/error status")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with ISO timestamp"""
        data = asdict(self)
        data['execution_timestamp'] = self.execution_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestResult':
        """Create from dictionary with ISO timestamp"""
        data_copy = data.copy()
        data_copy['execution_timestamp'] = datetime.fromisoformat(data['execution_timestamp'])
        return cls(**data_copy)
