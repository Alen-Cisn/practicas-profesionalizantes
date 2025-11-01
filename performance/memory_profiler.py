"""
Memory Profiler Module

Provides memory monitoring and profiling utilities for tracking
memory usage during analysis execution.
"""

import psutil
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryProfiler:
    """
    T040: Memory profiler for tracking current and peak memory usage.
    
    Monitors process memory consumption during analysis to ensure
    memory usage stays within acceptable limits (<500MB).
    """
    
    def __init__(self):
        """Initialize memory profiler with current process"""
        self._process = psutil.Process(os.getpid())
        self._peak_mb = 0.0
        self._baseline_mb = self.get_current_usage()
        logger.info(f"MemoryProfiler initialized (baseline: {self._baseline_mb:.1f}MB)")
    
    def get_current_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Current RSS memory in megabytes
        
        Side Effects:
            Updates peak memory if current exceeds previous peak
        """
        mem_bytes = self._process.memory_info().rss
        mem_mb = mem_bytes / (1024 * 1024)
        
        # Track peak
        if mem_mb > self._peak_mb:
            self._peak_mb = mem_mb
        
        return mem_mb
    
    def track_peak(self) -> float:
        """
        Get peak memory usage since profiler creation.
        
        Returns:
            Peak memory usage in MB
        
        Side Effects:
            Calls get_current_usage() to ensure peak is up-to-date
        """
        self.get_current_usage()  # Update peak
        return self._peak_mb
    
    def reset_peak(self):
        """Reset peak memory tracking to current usage"""
        self._peak_mb = self.get_current_usage()
        logger.debug(f"Peak memory reset to {self._peak_mb:.1f}MB")
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get comprehensive memory statistics.
        
        Returns:
            Dictionary with current, peak, and baseline memory metrics
        """
        current = self.get_current_usage()
        return {
            'current_mb': current,
            'peak_mb': self._peak_mb,
            'baseline_mb': self._baseline_mb,
            'delta_mb': current - self._baseline_mb
        }
    
    def check_threshold(self, threshold_mb: float = 500.0) -> bool:
        """
        Check if current memory usage exceeds threshold.
        
        Args:
            threshold_mb: Memory limit in MB (default 500MB)
        
        Returns:
            True if within threshold, False if exceeded
        """
        current = self.get_current_usage()
        if current > threshold_mb:
            logger.warning(f"⚠️ Memory threshold exceeded: {current:.1f}MB > {threshold_mb:.0f}MB")
            return False
        return True


# Global memory profiler instance (singleton pattern)
_memory_profiler_instance: Optional[MemoryProfiler] = None


def get_memory_profiler() -> MemoryProfiler:
    """Get or create the global memory profiler instance"""
    global _memory_profiler_instance
    if _memory_profiler_instance is None:
        _memory_profiler_instance = MemoryProfiler()
    return _memory_profiler_instance
