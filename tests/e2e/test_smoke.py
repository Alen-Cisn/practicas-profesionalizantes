"""
Smoke Tests for Historical Term Analyzer
Quick tests to verify basic functionality

Author: Test Suite  
Date: 2025-11-11
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import wait_for_streamlit_ready, take_screenshot


@pytest.mark.smoke
class TestSmokeTests:
    """Quick smoke tests to verify app is functional"""
    
    def test_app_is_accessible(self, page: Page):
        """Verify the app loads and is accessible"""
        # Main header should be visible
        expect(page.locator("text=🔍 Historical Term Analyzer")).to_be_visible()
        
        # Subtitle should be visible
        expect(page.locator("text=Análisis de términos")).to_be_visible()
    
    def test_critical_ui_elements_present(self, page: Page):
        """Verify all critical UI elements are present"""
        # Sidebar configuration
        expect(page.locator("text=⚙️ Configuración")).to_be_visible()
        
        # Year inputs
        expect(page.locator('label:has-text("Año inicio")')).to_be_visible()
        expect(page.locator('label:has-text("Año fin")')).to_be_visible()
        
        # Start button
        page.locator('button:has-text("▶️ Ejecutar Análisis")').scroll_into_view_if_needed()
        expect(page.locator('button:has-text("▶️ Ejecutar Análisis")')).to_be_visible()
        
        take_screenshot(page, "smoke_test_ui")
    
    def test_configuration_inputs_are_functional(self, page: Page):
        """Verify configuration inputs accept values"""
        # Test year input
        start_year = page.locator('label:has-text("Año inicio") + div input')
        start_year.click()
        start_year.fill("2001")
        start_year.press("Enter")
        page.wait_for_timeout(300)
        
        # Verify value changed
        expect(start_year).to_have_value("2001")
    
    def test_app_responds_to_interactions(self, page: Page):
        """Verify app responds to user interactions"""
        # Click on different sections
        page.locator("text=📊 Parámetros de Análisis").click()
        page.wait_for_timeout(300)
        
        page.locator("text=🌐 Dominios a Analizar").click()
        page.wait_for_timeout(300)
        
        # App should still be stable
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
    
    def test_no_console_errors(self, page: Page):
        """Verify no critical JavaScript errors in console"""
        console_errors = []
        
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
        
        page.on("console", handle_console)
        
        # Interact with the page
        page.wait_for_timeout(2000)
        
        # Check for critical errors (ignore minor warnings)
        critical_errors = [
            err for err in console_errors 
            if "critical" in err.lower() or "failed" in err.lower()
        ]
        
        assert len(critical_errors) == 0, f"Found console errors: {critical_errors}"
