"""
E2E UI responsiveness test for memory stability (User Story 2)
"""
import pytest
from playwright.sync_api import Page, expect

class TestMemoryStability:
    def test_tab_switching_remains_responsive(self, streamlit_app: Page):
        """Switch between 10 stored analyses and verify tab switching <1s."""
        page = streamlit_app
        # Simulate storing 10 analyses
        for i in range(10):
            page.locator("input[aria-label='URL to analyze']").fill(f"https://example.com/{i}")
            page.locator("input[aria-label='Search term']").fill("climate change")
            page.locator("input[aria-label='Number of pages']").fill("10")
            page.locator("button:has-text('Analyze')").click()
            expect(page.locator("text=Analysis complete")).to_be_visible(timeout=60000)
        # Switch tabs and measure responsiveness
        for i in range(10):
            tab = page.locator(f"button:has-text('Analysis {i+1}')")
            start = time.time()
            tab.click()
            expect(page.locator("h2:has-text('Analysis Results')")).to_be_visible(timeout=1000)
            elapsed = time.time() - start
            assert elapsed < 1.0, f"Tab switching too slow: {elapsed:.2f}s"
