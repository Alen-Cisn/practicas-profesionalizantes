"""
Worker Pool Manager Module

Provides dynamic parallel processing with optimal worker count
based on CPU cores and workload type (I/O-bound vs CPU-bound).
"""

from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from performance.models import WorkerPool
import os


class WorkerPoolManager:
    """
    Manages worker pools for parallel task execution.
    
    Creates optimized pools for I/O-bound (network requests, file I/O) and
    CPU-bound (HTML parsing, data processing) workloads.
    """
    
    def __init__(self):
        """Initialize worker pool manager"""
        self._pools: dict[str, tuple[WorkerPool, Any]] = {}  # pool_id -> (config, executor)
        self._cpu_count = os.cpu_count() or 4
    
    def create_pool(self, pool_type: str, workload_size: int) -> WorkerPool:
        """
        Create an optimized worker pool based on workload type.
        
        Args:
            pool_type: Either 'io_bound' or 'cpu_bound'
            workload_size: Number of tasks to process
        
        Returns:
            WorkerPool configuration object
        
        Logic:
            - io_bound: min(cpu_count * 4, 32, workload_size) threads
            - cpu_bound: min(cpu_count, workload_size) processes
        """
        if pool_type == 'io_bound':
            # I/O-bound: Use ThreadPoolExecutor with 4x CPU count
            max_workers = min(self._cpu_count * 4, 32, workload_size)
            executor = ThreadPoolExecutor(max_workers=max_workers)
        elif pool_type == 'cpu_bound':
            # CPU-bound: Use ProcessPoolExecutor with 1x CPU count
            max_workers = min(self._cpu_count, workload_size)
            executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            raise ValueError(f"Invalid pool_type: {pool_type}")
        
        pool = WorkerPool(
            pool_id=f"{pool_type}_{id(executor)}",
            pool_type=pool_type,
            max_workers=max_workers,
            cpu_count=self._cpu_count
        )
        
        self._pools[pool.pool_id] = (pool, executor)
        return pool
    
    def submit_task(
        self,
        pool: WorkerPool,
        task_fn: Callable,
        *args,
        **kwargs
    ) -> Future:
        """
        Submit a task to the specified pool.
        
        Args:
            pool: WorkerPool configuration from create_pool()
            task_fn: Function to execute
            *args: Positional arguments for task_fn
            **kwargs: Keyword arguments for task_fn
        
        Returns:
            Future object for tracking task completion
        
        Side Effects:
            Updates pool.active_workers and pool.queued_tasks
        """
        if pool.pool_id not in self._pools:
            raise ValueError(f"Pool {pool.pool_id} not found")
        
        pool_config, executor = self._pools[pool.pool_id]
        
        # Update pool statistics
        pool_config.queued_tasks += 1
        
        # Submit task
        future = executor.submit(task_fn, *args, **kwargs)
        
        # Callback to update statistics on completion
        def _on_complete(f: Future):
            pool_config.queued_tasks -= 1
            if f.exception():
                pool_config.failed_tasks += 1
            else:
                pool_config.completed_tasks += 1
            
            # Update utilization
            active = pool_config.max_workers - pool_config.queued_tasks
            pool_config.active_workers = max(0, active)
            pool_config.utilization_percent = (
                pool_config.active_workers / pool_config.max_workers * 100
            )
        
        future.add_done_callback(_on_complete)
        return future
    
    def shutdown(self, pool: WorkerPool, wait: bool = True) -> None:
        """
        Gracefully shutdown a worker pool.
        
        Args:
            pool: WorkerPool to shutdown
            wait: If True, blocks until all tasks complete
        
        Side Effects:
            Removes pool from internal registry
        """
        if pool.pool_id not in self._pools:
            return
        
        _, executor = self._pools.pop(pool.pool_id)
        executor.shutdown(wait=wait)
    
    def get_pool_stats(self, pool: WorkerPool) -> dict:
        """
        Get current statistics for a pool.
        
        Args:
            pool: WorkerPool to query
        
        Returns:
            Dictionary with current pool metrics
        """
        if pool.pool_id not in self._pools:
            return {}
        
        pool_config, _ = self._pools[pool.pool_id]
        return {
            'pool_id': pool_config.pool_id,
            'pool_type': pool_config.pool_type,
            'max_workers': pool_config.max_workers,
            'active_workers': pool_config.active_workers,
            'queued_tasks': pool_config.queued_tasks,
            'completed_tasks': pool_config.completed_tasks,
            'failed_tasks': pool_config.failed_tasks,
            'utilization_percent': round(pool_config.utilization_percent, 2)
        }


# Global worker pool manager instance
_worker_pool_manager_instance = None

def get_worker_pool_manager() -> WorkerPoolManager:
    """Get or create the global worker pool manager instance"""
    global _worker_pool_manager_instance
    if _worker_pool_manager_instance is None:
        _worker_pool_manager_instance = WorkerPoolManager()
    return _worker_pool_manager_instance
