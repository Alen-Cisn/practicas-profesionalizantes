"""
Performance benchmarks for caching functionality.

Tests cache hit rates and effectiveness for User Story 1.
"""

import pytest
import time
from performance.cache_manager import get_cache_manager, CacheManager
from performance.models import CacheEntry
import hashlib


class TestCachingPerformance:
    """Benchmark tests for cache performance and hit rates"""
    
    @pytest.fixture(autouse=True)
    def setup_cache(self):
        """Reset cache manager before each test"""
        cache_manager = get_cache_manager()
        cache_manager.clear()
        yield
        cache_manager.clear()
    
    def test_cache_hit_rate_exceeds_40_percent(self):
        """
        US1 Success Criterion: Cache hit rate >40% for repeated analyses.
        
        This test validates that caching provides significant performance benefit
        by achieving a cache hit rate above 40% when analyzing duplicate content.
        
        Test Scenario:
        1. Perform initial analysis (cold cache - all misses)
        2. Repeat analysis with same URLs (warm cache - should hit)
        3. Calculate hit rate: hits / (hits + misses)
        4. Verify hit rate > 40%
        
        Expected Result: Cache hit rate exceeds 40% threshold
        """
        cache_manager = get_cache_manager()
        
        # Simulate analysis with repeated HTML content
        test_urls = [
            f"https://example.com/page{i}" for i in range(100)
        ]
        
        # Simulate 60% duplicate content (realistic scenario)
        test_content = []
        for i, url in enumerate(test_urls):
            if i < 40:
                # Unique content (40%)
                content = f"<html><body>Unique content {i}</body></html>"
            else:
                # Duplicate content (60%) - reuse earlier content
                content = f"<html><body>Unique content {i % 40}</body></html>"
            test_content.append((url, content))
        
        # First pass - populate cache
        for url, content in test_content:
            cache_key = hashlib.sha256(content.encode()).hexdigest()
            result = cache_manager.get(cache_key, "html_parse")
            
            if result is None:
                # Cache miss - store parsed content
                parsed = {"html": content, "parsed": True}
                cache_manager.put(cache_key, "html_parse", parsed, len(content))
        
        # Second pass - should hit cache for duplicates
        initial_stats = cache_manager.get_statistics()
        
        for url, content in test_content:
            cache_key = hashlib.sha256(content.encode()).hexdigest()
            result = cache_manager.get(cache_key, "html_parse")
            assert result is not None, f"Cache miss for duplicate content: {url}"
        
        # Get final statistics
        final_stats = cache_manager.get_statistics()
        
        # Calculate hit rate for second pass
        second_pass_hits = final_stats['hit_count'] - initial_stats['hit_count']
        second_pass_requests = len(test_content)
        hit_rate = (second_pass_hits / second_pass_requests) * 100
        
        # Verify hit rate meets target
        assert hit_rate > 40.0, (
            f"Cache hit rate {hit_rate:.1f}% does not meet 40% target. "
            f"Hits: {second_pass_hits}/{second_pass_requests}"
        )
        
        print(f"\n✅ Cache Hit Rate: {hit_rate:.1f}% (target: >40%)")
        print(f"   Total hits: {second_pass_hits}/{second_pass_requests}")
    
    def test_cache_size_stays_under_450mb_limit(self):
        """
        Verify cache respects 450MB memory limit with LRU eviction.
        
        Test Steps:
        1. Fill cache with large entries
        2. Monitor total cache size
        3. Verify size stays under 450MB
        4. Verify LRU eviction occurs when needed
        """
        cache_manager = get_cache_manager()
        
        # Simulate large HTML documents (1MB each)
        large_content_size = 1024 * 1024  # 1MB
        
        # Try to add 500 x 1MB entries (would exceed 450MB limit)
        entries_added = 0
        for i in range(500):
            cache_key = f"large_doc_{i}"
            content = "x" * large_content_size
            
            success = cache_manager.put(
                cache_key,
                "html_parse",
                content,
                large_content_size
            )
            
            if success:
                entries_added += 1
        
        # Check final cache size
        stats = cache_manager.get_statistics()
        total_size_mb = stats['total_size_mb']
        
        # Verify size is under limit
        assert total_size_mb <= 450, (
            f"Cache size {total_size_mb:.1f}MB exceeds 450MB limit"
        )
        
        # Verify some entries were evicted (not all 500 fit)
        assert entries_added < 500, "Cache should have evicted entries to stay under limit"
        
        print(f"\n✅ Cache Size: {total_size_mb:.1f}MB (limit: 450MB)")
        print(f"   Entries: {stats['total_entries']} (attempted: 500)")
    
    def test_cache_improves_repeated_operation_performance(self):
        """
        Verify caching provides measurable performance improvement.
        
        Test Steps:
        1. Measure time for first operation (cache miss)
        2. Measure time for repeated operation (cache hit)
        3. Verify cache hit is significantly faster (>2x speedup)
        """
        cache_manager = get_cache_manager()
        
        # Simulate expensive parsing operation
        test_content = "<html><body>" + "x" * 100000 + "</body></html>"
        cache_key = hashlib.sha256(test_content.encode()).hexdigest()
        
        # First operation - cache miss
        start_time = time.perf_counter()
        result = cache_manager.get(cache_key, "html_parse")
        if result is None:
            # Simulate expensive parsing
            time.sleep(0.1)  # 100ms "parsing" time
            parsed_data = {"parsed": True, "content_length": len(test_content)}
            cache_manager.put(cache_key, "html_parse", parsed_data, len(test_content))
        miss_time = time.perf_counter() - start_time
        
        # Second operation - cache hit
        start_time = time.perf_counter()
        result = cache_manager.get(cache_key, "html_parse")
        assert result is not None, "Expected cache hit"
        hit_time = time.perf_counter() - start_time
        
        # Verify significant speedup
        speedup = miss_time / hit_time
        assert speedup > 2.0, (
            f"Cache speedup {speedup:.1f}x does not meet 2x minimum. "
            f"Miss: {miss_time*1000:.1f}ms, Hit: {hit_time*1000:.1f}ms"
        )
        
        print(f"\n✅ Cache Speedup: {speedup:.1f}x")
        print(f"   Miss time: {miss_time*1000:.1f}ms, Hit time: {hit_time*1000:.1f}ms")
    
    def test_cache_statistics_accuracy(self):
        """
        Verify cache statistics are accurate and complete.
        
        Test Steps:
        1. Perform mix of operations
        2. Get statistics
        3. Verify counts match expected values
        """
        cache_manager = get_cache_manager()
        
        # Add 10 items
        for i in range(10):
            cache_manager.put(f"key_{i}", "test_type", f"value_{i}", 100)
        
        # Hit 5 items twice each (10 hits)
        for i in range(5):
            cache_manager.get(f"key_{i}", "test_type")
            cache_manager.get(f"key_{i}", "test_type")
        
        # Miss 3 items (3 misses)
        for i in range(10, 13):
            cache_manager.get(f"key_{i}", "test_type")
        
        stats = cache_manager.get_statistics()
        
        # Verify statistics
        assert stats['total_entries'] == 10, "Should have 10 entries"
        assert stats['hit_count'] == 10, f"Should have 10 hits, got {stats['hit_count']}"
        assert stats['miss_count'] == 3, f"Should have 3 misses, got {stats['miss_count']}"
        
        # Verify hit rate calculation
        expected_hit_rate = (10 / 13) * 100
        assert abs(stats['hit_rate_percent'] - expected_hit_rate) < 0.1, (
            f"Hit rate calculation incorrect: {stats['hit_rate_percent']:.1f}% != {expected_hit_rate:.1f}%"
        )
        
        print(f"\n✅ Cache Statistics Accurate")
        print(f"   Entries: {stats['total_entries']}, Hits: {stats['hit_count']}, Misses: {stats['miss_count']}")
        print(f"   Hit Rate: {stats['hit_rate_percent']:.1f}%")
