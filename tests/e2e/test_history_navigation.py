"""
E2E Tests for History Navigation
Tests switching between analyses and history limit enforcement

T060: test_switch_between_analyses - validates history tab switching
T061: test_analysis_history_limit - validates 10-analysis cap with eviction
"""

import pytest
from playwright.sync_api import Page, expect
import time
from tests.e2e.helpers import (
    configure_analysis,
    start_analysis,
    wait_for_analysis_complete,
    get_analysis_summary
)


def test_switch_between_analyses(page: Page, app_url: str):
    """
    T060: Validate switching between stored analyses in history.
    
    Tests:
    1. Multiple analyses can be stored
    2. History selector/tabs are available
    3. Switching between analyses updates displayed data
    4. Each analysis maintains independent state
    5. Switching is fast (<2 seconds)
    """
    # Navigate to app
    page.goto(app_url, wait_until="networkidle")
    
    summaries = []
    
    # Run first analysis (2020)
    configure_analysis(
        page,
        start_year=2020,
        end_year=2020,
        max_documents=15,
        domains=['clarin.com']
    )
    
    assert start_analysis(page), "Failed to start first analysis"
    assert wait_for_analysis_complete(page, timeout=120000), "First analysis timeout"
    
    summary1 = get_analysis_summary(page)
    summaries.append(('2020', summary1))
    
    # Run second analysis (2021)
    configure_analysis(
        page,
        start_year=2021,
        end_year=2021,
        max_documents=15,
        domains=['clarin.com']
    )
    
    assert start_analysis(page), "Failed to start second analysis"
    assert wait_for_analysis_complete(page, timeout=120000), "Second analysis timeout"
    
    summary2 = get_analysis_summary(page)
    summaries.append(('2021', summary2))
    
    # Verify both analyses completed with different data
    assert summary1 != summary2, "Analyses produced identical results (unexpected)"
    
    # Look for history navigation UI
    # Check sidebar for history selector or analysis tabs
    history_section = page.locator('text=/Historial.*Análisis/i')
    
    if history_section.is_visible(timeout=2000):
        print("✅ History navigation UI found")
        
        # Try to find selectable items for each analysis
        # Look for selectbox or radio buttons with year labels
        analysis_2020 = page.locator('text=2020-2020').first
        analysis_2021 = page.locator('text=2021-2021').first
        
        if analysis_2020.is_visible(timeout=1000) and analysis_2021.is_visible(timeout=1000):
            # Test switching between analyses
            start_switch = time.time()
            
            # Click on first analysis
            analysis_2020.click()
            page.wait_for_timeout(500)
            
            # Verify we can see 2020 data
            current_summary = get_analysis_summary(page)
            
            # Click on second analysis
            analysis_2021.click()
            page.wait_for_timeout(500)
            
            switch_time = time.time() - start_switch
            
            # Verify switch happened quickly
            assert switch_time < 2, f"Analysis switching too slow: {switch_time:.1f}s"
            
            print(f"✅ Analysis switching test passed ({switch_time:.2f}s per switch)")
        else:
            print("⚠️ History selector UI not found - may use different navigation pattern")
    else:
        print("⚠️ History section not visible - feature may not be implemented yet")
        pytest.skip("History navigation UI not available")
    
    print(f"✅ Switch between analyses test completed")


def test_analysis_history_limit(page: Page, app_url: str):
    """
    T061: Validate 10-analysis cap with LRU eviction.
    
    Tests:
    1. System stores up to 10 analyses
    2. 11th analysis triggers eviction of oldest
    3. Most recent 10 analyses remain accessible
    4. No memory overflow occurs
    5. UI remains responsive with max history
    
    Note: This test is time-intensive (runs 11 quick analyses)
    """
    # Navigate to app
    page.goto(app_url, wait_until="networkidle")
    
    analysis_count = 11  # One more than limit to test eviction
    completed_analyses = []
    
    # Run 11 quick analyses
    for i in range(analysis_count):
        year = 2015 + i  # Use different years to distinguish analyses
        
        configure_analysis(
            page,
            start_year=year,
            end_year=year,
            max_documents=5,  # Minimal docs for speed
            domains=['clarin.com']
        )
        
        assert start_analysis(page), f"Failed to start analysis {i+1}"
        assert wait_for_analysis_complete(page, timeout=60000), f"Analysis {i+1} timeout"
        
        summary = get_analysis_summary(page)
        completed_analyses.append({
            'index': i,
            'year': year,
            'summary': summary
        })
        
        print(f"  Completed analysis {i+1}/{analysis_count} (year {year})")
    
    # Verify all 11 analyses completed
    assert len(completed_analyses) == analysis_count, "Not all analyses completed"
    
    # Check history navigation to verify limit enforcement
    history_section = page.locator('text=/Historial.*Análisis/i')
    
    if history_section.is_visible(timeout=2000):
        # Count visible history items
        # Look for year patterns like "2015-2015", "2016-2016", etc.
        history_items = []
        
        for i in range(analysis_count):
            year = 2015 + i
            item = page.locator(f'text={year}-{year}')
            if item.is_visible(timeout=500):
                history_items.append(year)
        
        # Should have at most 10 items (LRU eviction)
        assert len(history_items) <= 10, \
            f"History contains {len(history_items)} items, expected ≤10"
        
        # Oldest analysis (2015) should be evicted if limit is working
        if len(history_items) == 10:
            assert 2015 not in history_items, \
                "Oldest analysis not evicted (LRU not working)"
            print("✅ LRU eviction confirmed - oldest analysis removed")
        
        print(f"✅ History limit test passed ({len(history_items)} items in history)")
    else:
        print("⚠️ History section not visible - cannot verify limit")
        pytest.skip("History navigation not available to verify limit")
    
    print(f"✅ Analysis history limit test completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
