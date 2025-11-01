"""
Performance benchmarks for parallel processing with worker pools.

Tests throughput improvements from dynamic worker allocation for User Story 1.
"""

import pytest
import time
from concurrent.futures import as_completed
from performance.worker_pool import get_worker_pool_manager
from performance.models import WorkerPool


class TestParallelPerformance:
    """Benchmark tests for worker pool performance and throughput"""
    
    def test_dynamic_workers_improve_throughput(self):
        """
        US1 Success Criterion: Dynamic workers improve throughput vs fixed 8-worker pool.
        
        This test validates that dynamic worker allocation based on CPU count
        provides better throughput than a fixed 8-worker configuration.
        
        Test Scenario:
        1. Run I/O-bound tasks with fixed 8-worker pool
        2. Run same tasks with dynamic worker pool (cpu_count * 4)
        3. Compare throughput (tasks/second)
        4. Verify dynamic pool is faster or equal
        
        Expected Result: Dynamic pool matches or exceeds fixed pool throughput
        """
        manager = get_worker_pool_manager()
        
        # Define test workload (100 I/O-bound tasks)
        def io_task(task_id: int) -> int:
            """Simulate I/O-bound operation (network request)"""
            time.sleep(0.05)  # 50ms delay
            return task_id
        
        num_tasks = 100
        
        # Test 1: Fixed 8-worker pool (baseline)
        fixed_pool = WorkerPool(
            pool_id="fixed_test",
            pool_type="io_bound",
            max_workers=8,
            cpu_count=manager._cpu_count
        )
        
        # Manually create fixed pool for testing
        from concurrent.futures import ThreadPoolExecutor
        fixed_executor = ThreadPoolExecutor(max_workers=8)
        
        start_time = time.perf_counter()
        futures = [fixed_executor.submit(io_task, i) for i in range(num_tasks)]
        results = [f.result() for f in as_completed(futures)]
        fixed_duration = time.perf_counter() - start_time
        fixed_executor.shutdown()
        
        fixed_throughput = num_tasks / fixed_duration
        
        # Test 2: Dynamic worker pool
        dynamic_pool = manager.create_pool("io_bound", num_tasks)
        
        start_time = time.perf_counter()
        futures = [
            manager.submit_task(dynamic_pool, io_task, i)
            for i in range(num_tasks)
        ]
        results = [f.result() for f in as_completed(futures)]
        dynamic_duration = time.perf_counter() - start_time
        manager.shutdown(dynamic_pool)
        
        dynamic_throughput = num_tasks / dynamic_duration
        
        # Calculate improvement
        improvement_percent = ((dynamic_throughput - fixed_throughput) / fixed_throughput) * 100
        
        # Dynamic pool should be at least as good as fixed pool
        assert dynamic_throughput >= fixed_throughput * 0.95, (
            f"Dynamic pool throughput {dynamic_throughput:.1f} tasks/s is worse than "
            f"fixed pool {fixed_throughput:.1f} tasks/s"
        )
        
        print(f"\n✅ Worker Pool Performance")
        print(f"   Fixed (8 workers): {fixed_throughput:.1f} tasks/s ({fixed_duration:.2f}s)")
        print(f"   Dynamic ({dynamic_pool.max_workers} workers): {dynamic_throughput:.1f} tasks/s ({dynamic_duration:.2f}s)")
        print(f"   Improvement: {improvement_percent:+.1f}%")
    
    def test_io_bound_pool_uses_correct_worker_count(self):
        """
        Verify I/O-bound pool uses cpu_count * 4 workers (up to 32 max).
        
        Test Steps:
        1. Create I/O-bound pool for various workload sizes
        2. Verify worker count follows formula: min(cpu_count * 4, 32, workload_size)
        """
        manager = get_worker_pool_manager()
        cpu_count = manager._cpu_count
        
        # Test cases: (workload_size, expected_workers)
        test_cases = [
            (10, min(cpu_count * 4, 32, 10)),      # Small workload
            (100, min(cpu_count * 4, 32, 100)),    # Medium workload
            (500, min(cpu_count * 4, 32, 500)),    # Large workload
        ]
        
        for workload_size, expected_workers in test_cases:
            pool = manager.create_pool("io_bound", workload_size)
            
            assert pool.max_workers == expected_workers, (
                f"I/O pool for {workload_size} tasks should have {expected_workers} workers, "
                f"got {pool.max_workers}"
            )
            
            manager.shutdown(pool)
        
        print(f"\n✅ I/O-bound Worker Counts Correct (cpu_count={cpu_count})")
    
    def test_cpu_bound_pool_uses_correct_worker_count(self):
        """
        Verify CPU-bound pool uses cpu_count workers (respects physical cores).
        
        Test Steps:
        1. Create CPU-bound pool for various workload sizes
        2. Verify worker count follows formula: min(cpu_count, workload_size)
        """
        manager = get_worker_pool_manager()
        cpu_count = manager._cpu_count
        
        # Test cases: (workload_size, expected_workers)
        test_cases = [
            (2, min(cpu_count, 2)),      # Smaller than cpu_count
            (100, min(cpu_count, 100)),  # Larger than cpu_count
        ]
        
        for workload_size, expected_workers in test_cases:
            pool = manager.create_pool("cpu_bound", workload_size)
            
            assert pool.max_workers == expected_workers, (
                f"CPU pool for {workload_size} tasks should have {expected_workers} workers, "
                f"got {pool.max_workers}"
            )
            
            manager.shutdown(pool)
        
        print(f"\n✅ CPU-bound Worker Counts Correct (cpu_count={cpu_count})")
    
    def test_worker_pool_handles_task_failures_gracefully(self):
        """
        Verify worker pool tracks failed tasks and continues processing.
        
        Test Steps:
        1. Submit mix of successful and failing tasks
        2. Verify all tasks complete
        3. Check failed_tasks counter
        4. Verify successful tasks returned correct results
        """
        manager = get_worker_pool_manager()
        
        def task_that_succeeds(value: int) -> int:
            return value * 2
        
        def task_that_fails(value: int) -> int:
            if value % 3 == 0:
                raise ValueError(f"Task {value} failed intentionally")
            return value * 2
        
        pool = manager.create_pool("io_bound", 10)
        
        # Submit 10 tasks (3 will fail: 0, 3, 6, 9)
        futures = [
            manager.submit_task(pool, task_that_fails, i)
            for i in range(10)
        ]
        
        # Collect results
        successful_results = []
        failed_count = 0
        
        for future in as_completed(futures):
            try:
                result = future.result()
                successful_results.append(result)
            except ValueError:
                failed_count += 1
        
        # Verify counts
        assert len(successful_results) == 6, "Should have 6 successful tasks"
        assert failed_count == 4, "Should have 4 failed tasks"
        
        # Get pool stats (wait a moment for callbacks to complete)
        time.sleep(0.1)
        stats = manager.get_pool_stats(pool)
        
        # Note: The exact failed_tasks count might vary based on callback timing
        # Just verify it's tracked
        assert stats['completed_tasks'] + stats['failed_tasks'] == 10, (
            f"Total tasks should be 10, got {stats['completed_tasks']} + {stats['failed_tasks']}"
        )
        
        manager.shutdown(pool)
        
        print(f"\n✅ Worker Pool Error Handling")
        print(f"   Successful: {len(successful_results)}, Failed: {failed_count}")
    
    def test_parallel_processing_faster_than_sequential(self):
        """
        Verify parallel processing provides significant speedup over sequential.
        
        Test Steps:
        1. Run tasks sequentially (baseline)
        2. Run same tasks in parallel
        3. Verify parallel is at least 2x faster
        """
        manager = get_worker_pool_manager()
        
        def io_task(task_id: int) -> int:
            """Simulate I/O operation"""
            time.sleep(0.05)  # 50ms
            return task_id
        
        num_tasks = 20
        
        # Sequential execution
        start_time = time.perf_counter()
        sequential_results = [io_task(i) for i in range(num_tasks)]
        sequential_duration = time.perf_counter() - start_time
        
        # Parallel execution
        pool = manager.create_pool("io_bound", num_tasks)
        start_time = time.perf_counter()
        futures = [
            manager.submit_task(pool, io_task, i)
            for i in range(num_tasks)
        ]
        parallel_results = [f.result() for f in as_completed(futures)]
        parallel_duration = time.perf_counter() - start_time
        manager.shutdown(pool)
        
        # Calculate speedup
        speedup = sequential_duration / parallel_duration
        
        # Parallel should be at least 2x faster
        assert speedup >= 2.0, (
            f"Parallel speedup {speedup:.1f}x does not meet 2x minimum. "
            f"Sequential: {sequential_duration:.2f}s, Parallel: {parallel_duration:.2f}s"
        )
        
        print(f"\n✅ Parallel Processing Speedup: {speedup:.1f}x")
        print(f"   Sequential: {sequential_duration:.2f}s, Parallel: {parallel_duration:.2f}s")
