"""
Memory management benchmarks for User Story 2.
"""
import pytest
import gc
from performance.memory_profiler import MemoryProfiler
from historical_term_analyzer import HistoricalTermAnalyzer

class TestMemoryManagement:
    @pytest.fixture(autouse=True)
    def setup_profiler(self):
        self.profiler = MemoryProfiler()
        yield
        self.profiler.reset_peak()
    
    def test_memory_remains_below_500mb(self):
        """Run 5 analyses and verify memory stays below 500MB."""
        analyzer = HistoricalTermAnalyzer()
        for i in range(5):
            analyzer.analyze_period(2000, 2001, max_documents=100)
            mem = self.profiler.get_current_usage()
            assert mem < 500, f"Memory usage exceeded: {mem:.1f}MB"
        peak = self.profiler.track_peak()
        assert peak < 500, f"Peak memory exceeded: {peak:.1f}MB"
    
    def test_memory_cleanup_after_analysis(self):
        """Verify memory is released after analysis and gc.collect()."""
        analyzer = HistoricalTermAnalyzer()
        analyzer.analyze_period(2000, 2001, max_documents=100)
        mem_before = self.profiler.get_current_usage()
        del analyzer
        gc.collect()
        mem_after = self.profiler.get_current_usage()
        assert mem_after < mem_before, f"Memory not released: before={mem_before:.1f}MB, after={mem_after:.1f}MB"
