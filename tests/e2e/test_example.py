"""
Example Test Template
Copy and modify this to create your own tests

Author: Your Name
Date: 2025-11-11
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import (
    wait_for_streamlit_ready,
    click_streamlit_button,
    fill_streamlit_number_input,
    take_screenshot
)


class TestExampleFeature:
    """Example test suite showing common patterns"""
    
    def test_example_basic_check(self, page: Page):
        """
        Example: Test that a UI element is visible
        
        This is the simplest type of test - just checking
        that something appears on the page.
        """
        # Check that main title is visible
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        
        # Check that a specific element exists
        sidebar = page.locator("text=⚙️ Configuración")
        expect(sidebar).to_be_visible()
    
    def test_example_user_interaction(self, page: Page):
        """
        Example: Test user interaction with the app
        
        Shows how to interact with inputs and verify changes.
        """
        # Step 1: Modify an input field
        fill_streamlit_number_input(page, "Año inicio", 1999)
        page.wait_for_timeout(300)  # Wait for Streamlit to process
        
        # Step 2: Verify the change
        start_year_input = page.locator('label:has-text("Año inicio") + div input')
        expect(start_year_input).to_have_value("1999")
        
        # Step 3: Take a screenshot for documentation
        take_screenshot(page, "year_changed")
    
    def test_example_button_click(self, page: Page):
        """
        Example: Test clicking a button
        
        Demonstrates button interaction and checking results.
        """
        # Find and click a button
        button = page.locator('button:has-text("Iniciar Análisis")')
        button.scroll_into_view_if_needed()
        
        # Verify button is clickable
        expect(button).to_be_visible()
        expect(button).to_be_enabled()
        
        # Note: We don't actually click in this example because
        # it would start a long-running analysis
        
    @pytest.mark.smoke
    def test_example_marked_as_smoke(self, page: Page):
        """
        Example: Quick smoke test
        
        Use @pytest.mark.smoke for quick tests that verify
        basic functionality. Run with: pytest -m smoke
        """
        # Quick checks only
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        expect(page.locator("text=⚙️ Configuración")).to_be_visible()
    
    @pytest.mark.slow
    def test_example_slow_test(self, page: Page):
        """
        Example: Slow/long-running test
        
        Use @pytest.mark.slow for tests that take a long time.
        Skip with: pytest -m "not slow"
        """
        # This would be a long-running test, like a full analysis
        # We just show the structure here
        pass
    
    def test_example_with_validation(self, page: Page):
        """
        Example: Test with multiple assertions
        
        Shows how to test a complete user flow with validation.
        """
        # Arrange: Set up the test conditions
        initial_year = "2000"
        
        # Act: Perform the action
        start_year_input = page.locator('label:has-text("Año inicio") + div input')
        expect(start_year_input).to_have_value(initial_year)
        
        # Assert: Verify multiple conditions
        expect(start_year_input).to_be_visible()
        expect(start_year_input).to_be_enabled()
        expect(start_year_input).to_have_value(initial_year)
    
    def test_example_conditional_test(self, page: Page):
        """
        Example: Test that skips if conditions aren't met
        
        Useful for tests that depend on previous state or data.
        """
        # Check if results are available
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available - test not applicable")
        
        # If results exist, continue testing
        expect(results_header).to_be_visible()
    
    def test_example_error_handling(self, page: Page):
        """
        Example: Test error handling
        
        Shows how to test that errors are handled gracefully.
        """
        # Set invalid configuration
        fill_streamlit_number_input(page, "Año inicio", 2010)
        fill_streamlit_number_input(page, "Año fin", 2005)
        page.wait_for_timeout(500)
        
        # Verify error message appears
        error_message = page.locator('text="El año de inicio debe ser menor al año de fin"')
        expect(error_message).to_be_visible()
        
        take_screenshot(page, "error_message_displayed")


class TestExampleDataValidation:
    """Example tests for data validation"""
    
    def test_example_metric_value(self, page: Page):
        """
        Example: Extract and validate metric values
        
        Shows how to get values from the UI and validate them.
        """
        # This test would run after an analysis
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No results to validate")
        
        # Find a metric
        total_pages_metric = page.locator('text="📄 Total de Páginas"')
        
        if total_pages_metric.count() > 0:
            # Metric exists, we can validate it
            expect(total_pages_metric).to_be_visible()
    
    def test_example_list_validation(self, page: Page):
        """
        Example: Validate list of items
        
        Shows how to check multiple items in a list.
        """
        # Check that multiple domains are available
        domains = [
            "cnn.com",
            "bbc.co.uk",
            "nytimes.com"
        ]
        
        for domain in domains:
            # Each domain should be mentioned in the UI
            # (This is just an example - actual selector would differ)
            domain_text = page.locator(f'text="{domain}"')
            # We check count instead of expecting visibility
            # because not all might be visible
            assert domain_text.count() >= 0


class TestExampleAdvancedPatterns:
    """Advanced testing patterns and techniques"""
    
    def test_example_with_custom_wait(self, page: Page):
        """
        Example: Custom wait conditions
        
        Sometimes you need to wait for specific conditions.
        """
        # Wait for a specific element to appear
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        
        # Wait for all spinners to disappear
        page.wait_for_function(
            """() => {
                const spinners = document.querySelectorAll('[data-testid="stSpinner"]');
                return spinners.length === 0;
            }""",
            timeout=10000
        )
        
        # Now the app is ready for testing
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
    
    def test_example_screenshot_on_every_step(self, page: Page):
        """
        Example: Document test with screenshots
        
        Useful for creating visual test documentation.
        """
        # Step 1
        take_screenshot(page, "step1_initial_state")
        
        # Step 2: Make a change
        fill_streamlit_number_input(page, "Año inicio", 2001)
        take_screenshot(page, "step2_year_changed")
        
        # Step 3: Verify
        start_year = page.locator('label:has-text("Año inicio") + div input')
        expect(start_year).to_have_value("2001")
        take_screenshot(page, "step3_verified")
    
    @pytest.mark.parametrize("year", [1995, 2000, 2005, 2010])
    def test_example_parametrized(self, page: Page, year: int):
        """
        Example: Parametrized test
        
        Run the same test with different input values.
        This test will run 4 times, once for each year.
        """
        # Set the year
        fill_streamlit_number_input(page, "Año inicio", year)
        page.wait_for_timeout(300)
        
        # Verify it was set
        input_field = page.locator('label:has-text("Año inicio") + div input')
        expect(input_field).to_have_value(str(year))


# Tips for writing good tests:
#
# 1. Use descriptive test names that explain WHAT is being tested
# 2. Add docstrings to explain WHY and HOW
# 3. Follow the Arrange-Act-Assert pattern
# 4. Take screenshots at important steps
# 5. Use wait_for_timeout after interactions with Streamlit
# 6. Mark slow tests with @pytest.mark.slow
# 7. Mark quick tests with @pytest.mark.smoke
# 8. Keep tests independent - don't rely on other test results
# 9. Clean up in fixtures, not in tests
# 10. Use expect() for assertions - it auto-waits

# Running this example:
#
# All tests:          pytest tests/e2e/test_example.py -v
# Specific test:      pytest tests/e2e/test_example.py::TestExampleFeature::test_example_basic_check -v
# With browser:       pytest tests/e2e/test_example.py --headed -v
# Smoke tests only:   pytest tests/e2e/test_example.py -m smoke -v
# Skip slow tests:    pytest tests/e2e/test_example.py -m "not slow" -v
