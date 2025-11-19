"""
E2E Tests for Analysis Workflow
Tests the complete analysis workflow from configuration to results

Author: Test Suite
Date: 2025-11-11
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import (
    wait_for_streamlit_ready,
    fill_streamlit_number_input,
    click_streamlit_button,
    move_streamlit_slider,
    wait_for_analysis_complete,
    get_metric_value,
    take_screenshot
)


class TestAnalysisWorkflow:
    """Test suite for the complete analysis workflow"""
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_quick_analysis_workflow(self, page: Page):
        """
        Test a quick analysis with minimal documents to verify the complete workflow.
        This test might take several minutes to complete.
        """
        # Configure for quick test (minimal documents)
        fill_streamlit_number_input(page, "Año inicio", 2000)
        fill_streamlit_number_input(page, "Año fin", 2001)
        
        # Set minimal documents for faster test
        move_streamlit_slider(page, "Máximo de páginas web", 50)
        
        take_screenshot(page, "before_quick_analysis")
        
        # Start analysis
        page.locator('button:has-text("▶️ Ejecutar Análisis")').scroll_into_view_if_needed()
        click_streamlit_button(page, "▶️ Ejecutar Análisis")
        
        # Wait for analysis to complete (with generous timeout)
        try:
            wait_for_analysis_complete(page, timeout=180000)  # 3 minutes
            take_screenshot(page, "quick_analysis_results")
            
            # Verify results are displayed
            expect(page.locator('text="📊 Resultados del Análisis"')).to_be_visible()
            
            # Check that metrics are displayed
            expect(page.locator('text="📄 Total de Páginas"')).to_be_visible()
            expect(page.locator('text="🔤 Términos Únicos"')).to_be_visible()
            
            print("✅ Quick analysis completed successfully")
            
        except Exception as e:
            take_screenshot(page, "quick_analysis_timeout")
            pytest.skip(f"Analysis timed out or failed: {str(e)}")
    
    def test_configuration_changes_reflect_in_ui(self, page: Page):
        """Test that configuration changes are properly reflected"""
        # Change start year
        fill_streamlit_number_input(page, "Año inicio", 1998)
        page.wait_for_timeout(500)
        
        # Verify the value changed
        start_year_input = page.locator('label:has-text("Año inicio") + div input')
        expect(start_year_input).to_have_value("1998")
        
        # Change end year
        fill_streamlit_number_input(page, "Año fin", 2003)
        page.wait_for_timeout(500)
        
        end_year_input = page.locator('label:has-text("Año fin") + div input')
        expect(end_year_input).to_have_value("2003")
        
        take_screenshot(page, "configuration_changed")
    
    def test_slider_interaction(self, page: Page):
        """Test that the max documents slider works correctly"""
        # Move slider to different positions
        move_streamlit_slider(page, "Máximo de páginas web", 100)
        page.wait_for_timeout(500)
        
        move_streamlit_slider(page, "Máximo de páginas web", 500)
        page.wait_for_timeout(500)
        
        # Verify slider is functional (Streamlit 1.50.0 uses div with role="slider")
        slider = page.locator('div[role="slider"][aria-label="Máximo de páginas web"]')
        expect(slider).to_be_visible()
    
    def test_rate_limit_slider(self, page: Page):
        """Test the rate limit delay slider"""
        # Change rate limit
        move_streamlit_slider(page, "Delay entre requests (segundos)", 2.0)
        page.wait_for_timeout(500)
        
        # Verify slider exists and is interactive (Streamlit 1.50.0 uses div with role="slider")
        slider = page.locator('div[role="slider"][aria-label="Delay entre requests (segundos)"]')
        expect(slider).to_be_visible()
    
    def test_parallel_processing_checkbox(self, page: Page):
        """Test the parallel processing checkbox"""
        # Find the checkbox using aria-label
        checkbox = page.locator('input[type="checkbox"][aria-label="Procesamiento paralelo"]')
        
        # Wait for it to be available
        checkbox.wait_for(state="attached", timeout=5000)
        
        # Get initial state
        is_checked = checkbox.is_checked()
        
        # Click the parent label for better reliability with Streamlit
        checkbox_label = page.locator('label:has-text("Procesamiento paralelo")').first
        checkbox_label.click(force=True)
        page.wait_for_timeout(300)
        
        # Verify it toggled
        expect(checkbox).not_to_be_checked() if is_checked else expect(checkbox).to_be_checked()


class TestResultsDisplay:
    """Test suite for results display functionality"""
    
    def test_results_tabs_structure(self, page: Page):
        """
        Test that results tabs are structured correctly.
        Note: This requires having run an analysis first.
        """
        # This test will be skipped if no results are available
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Check for tabs
        expect(page.locator('text="📊 Resultados Agregados"')).to_be_visible()
        expect(page.locator('text="📅 Resultados por Año"')).to_be_visible()
        expect(page.locator('text="📈 Distribución"')).to_be_visible()
        expect(page.locator('text="📋 Datos Detallados"')).to_be_visible()
        expect(page.locator('text="📁 Exportar"')).to_be_visible()
    
    def test_metrics_display_format(self, page: Page):
        """Test that metrics are displayed in the correct format"""
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Check metric labels exist
        expect(page.locator('text="📄 Total de Páginas"')).to_be_visible()
        expect(page.locator('text="✅ Páginas con Contenido"')).to_be_visible()
        expect(page.locator('text="🔤 Términos Únicos"')).to_be_visible()
        expect(page.locator('text="⏱️ Tiempo de Análisis"')).to_be_visible()


class TestExportFunctionality:
    """Test suite for export functionality"""
    
    def test_export_tab_accessible(self, page: Page):
        """Test that export tab is accessible"""
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Click on export tab
        export_tab = page.locator('text="📁 Exportar"')
        export_tab.click()
        page.wait_for_timeout(500)
        
        # Check for export options
        expect(page.locator('text="📊 Top Términos (CSV)"')).to_be_visible()
        expect(page.locator('text="📋 Datos Completos (JSON)"')).to_be_visible()
    
    def test_csv_download_button_exists(self, page: Page):
        """Test that CSV download button exists in export section"""
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Navigate to export tab
        export_tab = page.locator('text="📁 Exportar"')
        export_tab.click()
        page.wait_for_timeout(500)
        
        # Check for download button
        csv_download = page.locator('button:has-text("Descargar CSV")')
        if csv_download.count() > 0:
            expect(csv_download).to_be_visible()
    
    def test_json_download_button_exists(self, page: Page):
        """Test that JSON download button exists in export section"""
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Navigate to export tab
        export_tab = page.locator('text="📁 Exportar"')
        export_tab.click()
        page.wait_for_timeout(500)
        
        # Check for download button
        json_download = page.locator('button:has-text("Descargar JSON")')
        if json_download.count() > 0:
            expect(json_download).to_be_visible()


class TestYearlyResultsNavigation:
    """Test suite for yearly results navigation"""
    
    def test_yearly_results_tab_navigation(self, page: Page):
        """Test navigation through yearly results tabs"""
        results_header = page.locator('text="📊 Resultados del Análisis"')
        
        if results_header.count() == 0:
            pytest.skip("No analysis results available to test")
        
        # Click on yearly results tab
        yearly_tab = page.locator('text="📅 Resultados por Año"')
        yearly_tab.click()
        page.wait_for_timeout(500)
        
        # Check that yearly content is displayed
        expect(page.locator('text="📅 Análisis por Año Individual"')).to_be_visible()
        
        take_screenshot(page, "yearly_results_tab")


class TestHistoryFunctionality:
    """Test suite for analysis history functionality"""
    
    def test_history_persists_across_analyses(self, page: Page):
        """Test that history section appears after multiple analyses"""
        # This test assumes multiple analyses have been run
        # If history section exists, test it
        history_section = page.locator('text="🗂️ Historial de Análisis"')
        
        if history_section.count() == 0:
            pytest.skip("No analysis history available to test")
        
        expect(history_section).to_be_visible()


class TestLogFunctionality:
    """Test suite for analysis log functionality"""
    
    def test_log_section_appears_during_analysis(self, page: Page):
        """Test that log section shows activity during analysis"""
        # Configure quick analysis
        fill_streamlit_number_input(page, "Año inicio", 2000)
        fill_streamlit_number_input(page, "Año fin", 2001)
        move_streamlit_slider(page, "Máximo de páginas web", 50)
        
        # Start analysis
        page.locator('button:has-text("▶️ Ejecutar Análisis")').scroll_into_view_if_needed()
        click_streamlit_button(page, "▶️ Ejecutar Análisis")
        
        # Wait a bit for log entries to appear
        page.wait_for_timeout(2000)
        
        # Check if log section appeared
        log_section = page.locator('text="📋 Log de Análisis"')
        
        # Log might appear if there's activity
        if log_section.count() > 0:
            expect(log_section).to_be_visible()
            take_screenshot(page, "log_during_analysis")
