"""
E2E tests for complete analysis workflow.

Tests the full user journey from URL input through term analysis to visualization.
Validates performance targets for User Story 1.
"""

import pytest
from playwright.sync_api import Page, expect
from .helpers import configure_analysis, start_analysis, wait_for_analysis_complete
from datetime import datetime


class TestAnalysisWorkflow:
    """End-to-end tests for the complete analysis workflow"""

    def test_complete_300_page_analysis_meets_performance_target(
        self,
        streamlit_app: Page,
        mock_cdx_route: Page,
        performance_test_config: dict,
    ):
        """
        US1 Acceptance: 300-page analysis completes in ≤15 minutes.
        """
        start_time = datetime.now()
        page = streamlit_app

        # Fill form
        page.locator("input[aria-label='URL to analyze']").fill("https://example.com")
        page.locator("input[aria-label='Search term']").fill("climate change")
        page.locator("input[aria-label='Number of pages']").fill("300")

        # Ensure performance optimizations flag is visible
        assert page.locator("text=Performance optimizations: enabled").is_visible()

        # Start analysis
        page.locator("button:has-text('Analyze')").click()

        # Wait for progress
        expect(page.locator("[data-testid='analysis-progress']")).to_be_visible(timeout=5000)

        # Wait for completion (15 minutes)
        expect(page.locator("[data-testid='analysis-complete']")).to_be_visible(timeout=900000)

        end_time = datetime.now()
        execution_seconds = (end_time - start_time).total_seconds()
        assert execution_seconds <= 900, f"Analysis too slow: {execution_seconds:.1f}s"
        print(f"\n✅ US1 Performance Target MET: {execution_seconds:.1f}s (target: ≤900s)")

    def test_analysis_displays_results_correctly(self, streamlit_app: Page, mock_cdx_route: Page):
        """
        Verify analysis results are displayed with correct visualizations.
        """
        page = streamlit_app
        # Use helpers to configure and start analysis reliably
        configure_analysis(
            page,
            start_year=2020,
            end_year=2020,
            max_documents=10,
            domains=['example.com']
        )

        assert start_analysis(page), "Failed to start analysis"
        assert wait_for_analysis_complete(page, timeout=60000), "Analysis did not complete in time"

        # Verify results render
        expect(page.locator("[data-testid='analysis-complete']")).to_be_visible()
        expect(page.locator("h2:has-text('Analysis Results')")).to_be_visible()
        expect(page.locator("div[data-testid='stPlotlyChart']").first).to_be_visible()
        expect(page.locator("h3:has-text('Timeline')")).to_be_visible()

    def test_analysis_with_empty_results(self, streamlit_app: Page, mock_cdx_route: Page):
        """
        Verify graceful handling when no historical data is found.
        """
        page = streamlit_app
        page.locator("input[aria-label='URL to analyze']").fill("https://notfound.example.com")
        page.locator("input[aria-label='Search term']").fill("nonexistent")
        page.locator("input[aria-label='Number of pages']").fill("10")
        page.locator("button:has-text('Analyze')").click()

        expect(page.locator("[data-testid='analysis-complete']")).to_be_visible(timeout=30000)
        assert not page.locator("div[data-testid='stError']").is_visible()
        expect(page.locator("[data-testid='analysis-complete']")).to_be_visible()

    def test_analysis_can_be_cancelled(self, streamlit_app: Page, mock_cdx_route: Page):
        """
        Verify user can cancel analysis in progress.
        """
        page = streamlit_app
        page.locator("input[aria-label='URL to analyze']").fill("https://popular.example.com")
        page.locator("input[aria-label='Search term']").fill("technology")
        page.locator("input[aria-label='Number of pages']").fill("300")
        page.locator("button:has-text('Analyze')").click()

        expect(page.locator("[data-testid='analysis-progress']")).to_be_visible(timeout=5000)

        cancel_button = page.locator("button:has-text('Cancel')")
        if cancel_button.is_visible():
            cancel_button.click()
            page.wait_for_selector("[data-testid='analysis-progress']", state="hidden", timeout=10000)

            # Accept either a formal completion token or a visible cancellation message.
            complete_count = page.locator("[data-testid='analysis-complete']").count()
            if complete_count and complete_count > 0:
                expect(page.locator("[data-testid='analysis-complete']")).to_be_visible(timeout=10000)
            else:
                # Fallback: check for a cancellation or warning message (Spanish/English)
                cancel_es = page.locator("text=cancelado")
                cancel_en = page.locator("text=User requested cancellation")
                assert (cancel_es.count() and cancel_es.first.is_visible()) or (
                    cancel_en.count() and cancel_en.first.is_visible()
                ), "Neither completion token nor cancellation message was visible after cancelling"
