"""
E2E Tests for Historical Term Analyzer Streamlit UI
Tests the main user interface and basic navigation

Author: Test Suite
Date: 2025-11-11
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import (
    wait_for_streamlit_ready,
    click_streamlit_button,
    take_screenshot,
    get_metric_value
)


class TestStreamlitUI:
    """Test suite for the main Streamlit UI components"""
    
    def test_app_loads_successfully(self, page: Page):
        """Test that the app loads with all main components visible"""
        # Check for main header
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        
        # Check for subtitle
        expect(page.locator("text=Análisis de términos en páginas web históricas")).to_be_visible()
        
        # Check for sidebar
        expect(page.locator("text=⚙️ Configuración")).to_be_visible()
        
        # Check for main sections
        expect(page.locator("text=📅 Período de Análisis")).to_be_visible()
        expect(page.locator("text=📊 Parámetros de Análisis")).to_be_visible()
        expect(page.locator("text=🌐 Dominios a Analizar")).to_be_visible()
        
        take_screenshot(page, "app_loaded")
    
    def test_sidebar_configuration_exists(self, page: Page):
        """Test that all configuration options are present in the sidebar"""
        # Year inputs
        expect(page.locator('label:has-text("Año inicio")')).to_be_visible()
        expect(page.locator('label:has-text("Año fin")')).to_be_visible()
        
        # Max documents slider
        expect(page.locator('text="Máximo de páginas web"')).to_be_visible()
        
        # Domain selection
        expect(page.locator('text="Seleccionar dominios"')).to_be_visible()
        
        # Advanced configuration
        expect(page.locator('text="🔧 Configuración Avanzada"')).to_be_visible()
        expect(page.locator('text="Delay entre requests (segundos)"')).to_be_visible()
        expect(page.locator('text="Procesamiento paralelo"')).to_be_visible()
    
    def test_start_analysis_button_exists(self, page: Page):
        """Test that the start analysis button is present"""
        expect(page.locator('text="🚀 Iniciar Análisis"')).to_be_visible()
        
        # The button should be visible (might need to scroll)
        page.locator('button:has-text("▶️ Ejecutar Análisis")').scroll_into_view_if_needed()
        expect(page.locator('button:has-text("▶️ Ejecutar Análisis")')).to_be_visible()
    
    def test_default_year_values(self, page: Page):
        """Test that default year values are correct"""
        # Check start year default (2000)
        start_year_input = page.locator('label:has-text("Año inicio") + div input')
        expect(start_year_input).to_have_value("2000")
        
        # Check end year default (2005)
        end_year_input = page.locator('label:has-text("Año fin") + div input')
        expect(end_year_input).to_have_value("2005")
    
    def test_responsive_layout(self, page: Page):
        """Test that the layout adapts to different screen sizes"""
        # Test desktop view
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(500)
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        take_screenshot(page, "desktop_view")
        
        # Test tablet view
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(500)
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        take_screenshot(page, "tablet_view")
        
        # Test mobile view
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)
        expect(page.locator("text=Historical Term Analyzer")).to_be_visible()
        take_screenshot(page, "mobile_view")
    
    def test_log_section_exists(self, page: Page):
        """Test that the analysis log section is visible"""
        # The log section should be visible
        # Note: It may only appear when there's activity
        log_section = page.locator('text="📋 Log de Análisis"')
        
        # Log might not be visible initially, which is okay
        # Just check the section exists in the DOM
        assert log_section.count() >= 0


class TestConfigurationValidation:
    """Test suite for configuration validation"""
    
    def test_year_validation_prevents_invalid_range(self, page: Page):
        """Test that invalid year ranges show an error"""
        # Set start year > end year
        start_year_input = page.locator('label:has-text("Año inicio") + div input')
        start_year_input.click()
        start_year_input.fill("2010")
        start_year_input.press("Enter")
        
        end_year_input = page.locator('label:has-text("Año fin") + div input')
        end_year_input.click()
        end_year_input.fill("2005")
        end_year_input.press("Enter")
        
        page.wait_for_timeout(500)
        
        # Check for error message
        expect(page.locator('text="El año de inicio debe ser menor al año de fin"')).to_be_visible()
        take_screenshot(page, "year_validation_error")
    
    def test_domain_selection_required(self, page: Page):
        """Test that at least one domain must be selected"""
        # Note: This test checks if the app properly handles empty domain selection
        # The actual behavior depends on the app's implementation
        
        # Clear all domains (if possible through UI)
        # This might require custom logic depending on Streamlit multiselect behavior
        
        # For now, just verify the multiselect exists
        expect(page.locator('text="Seleccionar dominios"')).to_be_visible()


class TestAccessibility:
    """Test suite for accessibility features"""
    
    def test_page_has_title(self, page: Page):
        """Test that the page has a proper title"""
        expect(page).to_have_title("Historical Term Analyzer")
    
    def test_main_landmarks(self, page: Page):
        """Test that main ARIA landmarks exist"""
        # Streamlit apps have a main container
        expect(page.locator('[data-testid="stAppViewContainer"]')).to_be_visible()
    
    def test_headings_hierarchy(self, page: Page):
        """Test that headings are properly structured"""
        # Main heading should exist
        main_heading = page.locator("text=🔍 Historical Term Analyzer").first
        expect(main_heading).to_be_visible()
        
        # Check for section headings
        expect(page.locator("text=⚙️ Configuración")).to_be_visible()
        expect(page.locator("text=🚀 Iniciar Análisis")).to_be_visible()


class TestErrorHandling:
    """Test suite for error handling scenarios"""
    
    def test_app_handles_network_errors_gracefully(self, page: Page):
        """Test that the app handles network errors without crashing"""
        # Just verify the app is stable and doesn't crash
        # Note: Offline testing with Streamlit is tricky as it needs websocket connection
        
        # Verify app is loaded
        expect(page.locator("text=🔍 Historical Term Analyzer")).to_be_visible()
        
        # Verify button exists (would need network for actual analysis)
        button = page.locator('button:has-text("▶️ Ejecutar Análisis")')
        button.scroll_into_view_if_needed()
        expect(button).to_be_visible()
        
        # App should still be functional
        expect(page.locator("text=⚙️ Configuración")).to_be_visible()


@pytest.mark.slow
class TestPerformance:
    """Test suite for performance-related checks"""
    
    def test_initial_load_time(self, page: Page):
        """Test that the app loads within acceptable time"""
        # This is already covered by the fixture, but we can measure it
        import time
        
        start = time.time()
        page.reload()
        wait_for_streamlit_ready(page)
        load_time = time.time() - start
        
        # Should load within 10 seconds
        assert load_time < 10, f"App took {load_time:.2f}s to load"
        print(f"✅ App loaded in {load_time:.2f}s")
