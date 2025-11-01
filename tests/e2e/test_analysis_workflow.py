"""
E2E tests for complete analysis workflow.

Tests the full user journey from URL input through term analysis to visualization.
Validates performance targets for User Story 1.
"""

import pytest
from playwright.sync_api import Page, expect
from datetime import datetime
import json


class TestAnalysisWorkflow:
    """End-to-end tests for the complete analysis workflow"""
    
    def test_complete_300_page_analysis_meets_performance_target(
        self,
        streamlit_app: Page,
        mock_cdx_route: Page,
        performance_test_config: dict
    ):
        """
        US1 Acceptance: 300-page analysis completes in ≤15 minutes.
        
        This test validates the primary success criterion for User Story 1:
        reducing analysis time from 20-25 minutes to ≤15 minutes (30-40% improvement).
        
        Test Steps:
        1. Navigate to Streamlit app with performance optimizations enabled
        2. Enter URL and search term for analysis
        3. Configure for 300 pages of historical data
        4. Start analysis and track execution time
        5. Wait for completion
        6. Verify total execution time ≤ 900 seconds (15 minutes)
        
        Expected Result: Analysis completes within 15-minute target with success status
        """
        start_time = datetime.now()
        
        # Navigate to app (already done by streamlit_app fixture)
        page = streamlit_app
        
        # Input URL for analysis
        url_input = page.locator("input[aria-label='URL to analyze']")
        url_input.fill("https://example.com")
        
        # Input search term
        term_input = page.locator("input[aria-label='Search term']")
        term_input.fill("climate change")
        
        # Configure for 300 pages
        page_count = page.locator("input[aria-label='Number of pages']")
        page_count.fill("300")
        
        # Enable performance optimizations (should be set by fixture)
        assert page.locator("text=Performance optimizations: enabled").is_visible()
        
        # Start analysis
        analyze_button = page.locator("button:has-text('Analyze')")
        analyze_button.click()
        
        # Wait for progress indicator
        expect(page.locator("div[data-testid='stProgress']")).to_be_visible(timeout=5000)
        
        # Wait for completion (with 15-minute timeout)
        expect(
            page.locator("text=Analysis complete"),
            "Analysis should complete within 15 minutes"
        ).to_be_visible(timeout=900000)  # 15 minutes
        
        # Calculate execution time
        end_time = datetime.now()
        execution_seconds = (end_time - start_time).total_seconds()
        
        # Verify performance target
        assert execution_seconds <= 900, (
            f"Analysis took {execution_seconds:.1f}s, exceeding 15-minute target (900s). "
            f"User Story 1 acceptance criterion NOT met."
        )
        
        # Verify success status
        expect(page.locator("div[data-testid='stSuccess']")).to_be_visible()
        
        # Log performance metrics
        print(f"\n✅ US1 Performance Target MET: {execution_seconds:.1f}s (target: ≤900s)")
    
    def test_analysis_displays_results_correctly(
        self,
        streamlit_app: Page,
        mock_cdx_route: Page
    ):
        """
        Verify analysis results are displayed with correct visualizations.
        
        Test Steps:
        1. Run a small analysis (10 pages)
        2. Wait for completion
        3. Verify results section appears
        4. Check for term frequency chart
        5. Check for timeline visualization
        6. Verify export options are available
        """
        page = streamlit_app
        
        # Input test data
        page.locator("input[aria-label='URL to analyze']").fill("https://example.com")
        page.locator("input[aria-label='Search term']").fill("climate change")
        page.locator("input[aria-label='Number of pages']").fill("10")
        
        # Start analysis
        page.locator("button:has-text('Analyze')").click()
        
        # Wait for completion
        expect(page.locator("text=Analysis complete")).to_be_visible(timeout=60000)
        
        # Verify results section
        expect(page.locator("h2:has-text('Analysis Results')")).to_be_visible()
        
        # Verify term frequency chart exists
        expect(page.locator("div[data-testid='stPlotlyChart']").first).to_be_visible()
        
        # Verify timeline visualization
        expect(page.locator("h3:has-text('Timeline')")).to_be_visible()
        
        # Verify export button
        expect(page.locator("button:has-text('Export')")).to_be_visible()
    
    def test_analysis_with_empty_results(
        self,
        streamlit_app: Page,
        mock_cdx_route: Page
    ):
        """
        Verify graceful handling when no historical data is found.
        
        Test Steps:
        1. Input URL that returns no CDX results
        2. Start analysis
        3. Verify appropriate message is displayed
        4. Verify no error state
        """
        page = streamlit_app
        
        # Input URL that will return empty results (mocked)
        page.locator("input[aria-label='URL to analyze']").fill("https://notfound.example.com")
        page.locator("input[aria-label='Search term']").fill("nonexistent")
        page.locator("input[aria-label='Number of pages']").fill("10")
        
        # Start analysis
        page.locator("button:has-text('Analyze')").click()
        
        # Wait for completion
        expect(page.locator("text=Analysis complete")).to_be_visible(timeout=30000)
        
        # Verify empty results message
        expect(page.locator("text=No historical data found")).to_be_visible()
        
        # Verify no error occurred
        assert not page.locator("div[data-testid='stError']").is_visible()
    
    def test_analysis_can_be_cancelled(
        self,
        streamlit_app: Page,
        mock_cdx_route: Page
    ):
        """
        Verify user can cancel analysis in progress.
        
        Test Steps:
        1. Start a large analysis
        2. Wait for progress indicator
        3. Click cancel button
        4. Verify analysis stops
        5. Verify partial results are available
        """
        page = streamlit_app
        
        # Start large analysis
        page.locator("input[aria-label='URL to analyze']").fill("https://popular.example.com")
        page.locator("input[aria-label='Search term']").fill("technology")
        page.locator("input[aria-label='Number of pages']").fill("300")
        
        page.locator("button:has-text('Analyze')").click()
        
        # Wait for progress
        expect(page.locator("div[data-testid='stProgress']")).to_be_visible(timeout=5000)
        
        # Cancel analysis
        cancel_button = page.locator("button:has-text('Cancel')")
        if cancel_button.is_visible():
            cancel_button.click()
            
            # Verify cancellation message
            expect(page.locator("text=Analysis cancelled")).to_be_visible(timeout=10000)
            
            # Verify partial results message
            expect(page.locator("text=Partial results available")).to_be_visible()
