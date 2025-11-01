"""
Test Data Models for E2E Tests
Dataclasses for test scenarios and results

T050: Test data models for E2E test infrastructure
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class TestScenario:
    """
    Represents an E2E test scenario configuration.
    
    Attributes:
        name: Descriptive name for the scenario
        start_year: Analysis start year
        end_year: Analysis end year
        max_documents: Maximum documents to analyze
        domains: List of domains to analyze
        search_term: Optional search term filter
        expected_min_results: Minimum expected results count
        timeout: Maximum execution time in seconds
        description: Human-readable scenario description
    """
    name: str
    start_year: int
    end_year: int
    max_documents: int
    domains: List[str]
    search_term: Optional[str] = None
    expected_min_results: int = 10
    timeout: int = 300
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to configuration dictionary"""
        return {
            'start_year': self.start_year,
            'end_year': self.end_year,
            'max_documents': self.max_documents,
            'domains': self.domains,
            'search_term': self.search_term
        }


@dataclass
class TestResult:
    """
    Represents the results of an E2E test execution.
    
    Attributes:
        test_name: Name of the test
        passed: Whether the test passed
        execution_time: Test execution time in seconds
        error_message: Error message if test failed
        screenshot_path: Path to screenshot (if captured)
        video_path: Path to video recording (if captured)
        metrics: Additional test metrics
        timestamp: Test execution timestamp
    """
    test_name: str
    passed: bool
    execution_time: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'test_name': self.test_name,
            'passed': self.passed,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'screenshot_path': self.screenshot_path,
            'video_path': self.video_path,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AnalysisMetrics:
    """
    Metrics captured during analysis execution.
    
    Attributes:
        total_documents: Total documents processed
        unique_terms: Number of unique terms found
        execution_time: Total execution time in seconds
        memory_usage_mb: Peak memory usage in MB
        cache_hit_rate: Cache hit rate percentage
        top_term: Most frequent term
        tab_switch_time: Time to switch between tabs
        chart_render_time: Time to render charts
    """
    total_documents: int = 0
    unique_terms: int = 0
    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    cache_hit_rate: float = 0.0
    top_term: Optional[str] = None
    tab_switch_time: float = 0.0
    chart_render_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_documents': self.total_documents,
            'unique_terms': self.unique_terms,
            'execution_time': self.execution_time,
            'memory_usage_mb': self.memory_usage_mb,
            'cache_hit_rate': self.cache_hit_rate,
            'top_term': self.top_term,
            'tab_switch_time': self.tab_switch_time,
            'chart_render_time': self.chart_render_time
        }


# Predefined test scenarios for common cases
QUICK_TEST_SCENARIO = TestScenario(
    name="quick_test",
    start_year=2020,
    end_year=2020,
    max_documents=10,
    domains=['clarin.com'],
    expected_min_results=5,
    timeout=60,
    description="Quick smoke test with minimal data"
)

STANDARD_TEST_SCENARIO = TestScenario(
    name="standard_test",
    start_year=2020,
    end_year=2021,
    max_documents=50,
    domains=['clarin.com', 'lanacion.com.ar'],
    expected_min_results=20,
    timeout=180,
    description="Standard test with moderate data volume"
)

PERFORMANCE_TEST_SCENARIO = TestScenario(
    name="performance_test",
    start_year=2018,
    end_year=2020,
    max_documents=300,
    domains=['clarin.com', 'lanacion.com.ar', 'pagina12.com.ar'],
    expected_min_results=50,
    timeout=900,
    description="Performance test with maximum data volume (15min target)"
)

YEAR_BY_YEAR_SCENARIO = TestScenario(
    name="year_by_year",
    start_year=2019,
    end_year=2021,
    max_documents=100,
    domains=['clarin.com'],
    expected_min_results=30,
    timeout=300,
    description="Multi-year analysis for year-by-year comparison"
)
