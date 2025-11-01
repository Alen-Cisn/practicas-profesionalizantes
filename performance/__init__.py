"""
Performance Optimization Module

This module provides performance monitoring, caching, and parallel processing
utilities for the Historical Term Analyzer.

Components:
- PerformanceMonitor: Track execution time and resource usage
- CacheManager: Multi-level caching for HTML parsing and term extraction
- WorkerPoolManager: Dynamic parallel processing based on workload type
"""

from typing import List, Optional, Dict
from datetime import datetime
from performance.models import PerformanceMetric
import time


__version__ = "1.0.0"
__all__ = ["PerformanceMonitor", "CacheManager", "WorkerPoolManager", "get_monitor"]


class PerformanceMonitor:
    """
    Tracks performance metrics across analysis phases.
    
    Records execution time, memory usage, cache efficiency, and custom metrics.
    """
    
    def __init__(self, analysis_id: str):
        """
        Initialize performance monitor for an analysis.
        
        Args:
            analysis_id: Unique identifier for the analysis being monitored
        """
        self.analysis_id = analysis_id
        self._metrics: List[PerformanceMetric] = []
        self._active_phases: Dict[str, dict] = {}  # phase_id -> {name, start_time}
    
    def start_phase(self, phase_name: str) -> str:
        """
        Begin timing a phase of execution.
        
        Args:
            phase_name: Name of the phase (e.g., 'fetch_urls', 'parse_html')
        
        Returns:
            phase_id: Unique identifier for this phase execution
        """
        phase_id = f"{phase_name}_{datetime.now().timestamp()}"
        self._active_phases[phase_id] = {
            'name': phase_name,
            'start_time': time.perf_counter()
        }
        return phase_id
    
    def end_phase(self, phase_id: str) -> float:
        """
        End timing a phase and record the duration metric.
        
        Args:
            phase_id: ID returned from start_phase()
        
        Returns:
            duration: Phase duration in seconds
        
        Side Effects:
            Creates execution_time PerformanceMetric
        """
        if phase_id not in self._active_phases:
            raise ValueError(f"Phase {phase_id} was not started")
        
        phase_info = self._active_phases.pop(phase_id)
        duration = time.perf_counter() - phase_info['start_time']
        
        # Record metric
        metric = PerformanceMetric(
            metric_id=f"exec_{phase_id}",
            analysis_id=self.analysis_id,
            timestamp=datetime.now(),
            metric_type='execution_time',
            value=duration,
            unit='seconds',
            phase=phase_info['name']
        )
        self._metrics.append(metric)
        
        return duration
    
    def record_metric(
        self,
        metric_type: str,
        value: float,
        unit: str,
        phase: str
    ) -> None:
        """
        Record a custom performance metric.
        
        Args:
            metric_type: Type of metric (execution_time, memory_usage, cache_hit_rate, etc.)
            value: Numeric value of the metric
            unit: Unit of measurement
            phase: Phase name this metric belongs to
        """
        metric = PerformanceMetric(
            metric_id=f"{metric_type}_{datetime.now().timestamp()}",
            analysis_id=self.analysis_id,
            timestamp=datetime.now(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            phase=phase
        )
        self._metrics.append(metric)
    
    def get_metrics(self, analysis_id: Optional[str] = None) -> List[PerformanceMetric]:
        """
        Retrieve all metrics for an analysis.
        
        Args:
            analysis_id: Optional filter by analysis ID (defaults to current)
        
        Returns:
            List of performance metrics
        """
        target_id = analysis_id or self.analysis_id
        return [m for m in self._metrics if m.analysis_id == target_id]
    
    def get_summary(self, analysis_id: Optional[str] = None) -> Dict:
        """
        Get aggregated performance summary.
        
        Args:
            analysis_id: Optional filter by analysis ID (defaults to current)
        
        Returns:
            Dictionary with aggregated metrics:
            - total_duration: Sum of all execution times
            - memory_peak: Maximum memory usage
            - cache_hit_rate: Average cache hit rate
            - phases: Breakdown by phase
        """
        metrics = self.get_metrics(analysis_id)
        
        total_duration = 0.0
        memory_peak = 0.0
        cache_hit_rates = []
        phases_summary = {}
        
        for metric in metrics:
            # Aggregate execution time
            if metric.metric_type == 'execution_time':
                total_duration += metric.value
                if metric.phase not in phases_summary:
                    phases_summary[metric.phase] = {'duration': 0.0, 'count': 0}
                phases_summary[metric.phase]['duration'] += metric.value
                phases_summary[metric.phase]['count'] += 1
            
            # Track peak memory
            elif metric.metric_type == 'memory_usage':
                memory_peak = max(memory_peak, metric.value)
            
            # Collect cache hit rates
            elif metric.metric_type == 'cache_hit_rate':
                cache_hit_rates.append(metric.value)
        
        avg_cache_hit_rate = (
            sum(cache_hit_rates) / len(cache_hit_rates)
            if cache_hit_rates else 0.0
        )
        
        return {
            'analysis_id': analysis_id or self.analysis_id,
            'total_duration': round(total_duration, 3),
            'memory_peak_mb': round(memory_peak, 2),
            'cache_hit_rate_percent': round(avg_cache_hit_rate, 2),
            'phases': phases_summary,
            'total_metrics': len(metrics)
        }


# Global monitor registry (supports multiple concurrent analyses)
_monitor_registry: Dict[str, PerformanceMonitor] = {}

def get_monitor(analysis_id: str) -> PerformanceMonitor:
    """Get or create a performance monitor for an analysis"""
    if analysis_id not in _monitor_registry:
        _monitor_registry[analysis_id] = PerformanceMonitor(analysis_id)
    return _monitor_registry[analysis_id]


# Utility Functions for Performance Measurement

def measure_memory() -> float:
    """
    Measure current process memory usage in MB.
    
    Returns:
        Memory usage in megabytes
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert bytes to MB


def time_function(phase_name: str):
    """
    Decorator to automatically time function execution.
    
    Usage:
        @time_function("fetch_data")
        def fetch_data(url):
            # function implementation
            pass
    
    Args:
        phase_name: Name of the phase for metric recording
    
    Returns:
        Decorated function that records execution time
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get analysis_id from kwargs or use function name
            analysis_id = kwargs.get('analysis_id', func.__name__)
            
            monitor = get_monitor(analysis_id)
            phase_id = monitor.start_phase(phase_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.end_phase(phase_id)
        
        return wrapper
    return decorator


def profile_memory(phase_name: str):
    """
    Decorator to measure memory usage before and after function execution.
    
    Usage:
        @profile_memory("parse_html")
        def parse_html(content):
            # function implementation
            pass
    
    Args:
        phase_name: Name of the phase for metric recording
    
    Returns:
        Decorated function that records memory delta
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get analysis_id from kwargs or use function name
            analysis_id = kwargs.get('analysis_id', func.__name__)
            
            monitor = get_monitor(analysis_id)
            mem_before = measure_memory()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                mem_after = measure_memory()
                mem_delta = mem_after - mem_before
                
                monitor.record_metric(
                    metric_type='memory_usage',
                    value=mem_delta,
                    unit='MB',
                    phase=phase_name
                )
        
        return wrapper
    return decorator


def batch_iterator(items: list, batch_size: int):
    """
    Split a list into batches for parallel processing.
    
    Usage:
        for batch in batch_iterator(urls, batch_size=50):
            process_batch(batch)
    
    Args:
        items: List of items to batch
        batch_size: Number of items per batch
    
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "2m 30s", "45s", "1h 15m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_value: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB", "512 KB", "2.3 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"
