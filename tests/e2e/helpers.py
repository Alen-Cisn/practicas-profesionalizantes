"""
E2E Test Helpers for Historical Term Analyzer
Reusable utilities for Playwright-based end-to-end tests

T048: Base test helpers for E2E testing infrastructure
"""

from playwright.sync_api import Page, expect
import time
from typing import Dict, Any, Optional


def wait_for_analysis_complete(
    page: Page, 
    timeout: int = 300000  # 5 minutes default
) -> bool:
    """
    Wait for analysis to complete by monitoring progress indicators.
    
    Args:
        page: Playwright page object
        timeout: Maximum wait time in milliseconds
        
    Returns:
        True if analysis completed successfully, False otherwise
    """
    try:
        # Wait for "Análisis en progreso" message to disappear
        page.wait_for_selector(
            "text=Análisis en progreso", 
            state="hidden", 
            timeout=timeout
        )
        
        # Wait for results to appear
        page.wait_for_selector(
            "text=📊 Resultados del Análisis",
            state="visible",
            timeout=10000
        )
        
        return True
        
    except Exception as e:
        print(f"Analysis completion wait failed: {e}")
        return False


def configure_analysis(
    page: Page,
    start_year: int = 2020,
    end_year: int = 2021,
    max_documents: int = 50,
    domains: Optional[list[str]] = None,
    search_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure analysis parameters in the Streamlit sidebar.
    
    Args:
        page: Playwright page object
        start_year: Analysis start year
        end_year: Analysis end year
        max_documents: Maximum documents to analyze
        domains: List of domains to select (default: ['clarin.com'])
        search_term: Optional search term
        
    Returns:
        Configuration dictionary with parameters used
    """
    if domains is None:
        domains = ['clarin.com']
    
    # Fill in start year
    start_year_input = page.locator('input[aria-label*="Año Inicial"]').first
    start_year_input.fill(str(start_year))
    
    # Fill in end year
    end_year_input = page.locator('input[aria-label*="Año Final"]').first
    end_year_input.fill(str(end_year))
    
    # Fill in max documents
    max_docs_input = page.locator('input[aria-label*="Máximo"]').first
    max_docs_input.fill(str(max_documents))
    
    # Select domains
    for domain in domains:
        # Check if domain checkbox exists and click it
        domain_checkbox = page.locator(f'label:has-text("{domain}")').first
        if domain_checkbox.is_visible():
            domain_checkbox.click()
    
    # Optional search term
    if search_term:
        search_input = page.locator('input[aria-label*="Término"]').first
        if search_input.is_visible():
            search_input.fill(search_term)
    
    return {
        'start_year': start_year,
        'end_year': end_year,
        'max_documents': max_documents,
        'domains': domains,
        'search_term': search_term
    }


def verify_results_displayed(page: Page, min_terms: int = 10) -> bool:
    """
    Verify that analysis results are properly displayed.
    
    Args:
        page: Playwright page object
        min_terms: Minimum number of terms expected in results
        
    Returns:
        True if results are valid, False otherwise
    """
    try:
        # Check for results header
        results_header = page.locator('text=📊 Resultados del Análisis')
        expect(results_header).to_be_visible()
        
        # Check for top terms chart
        chart_container = page.locator('.plotly')
        expect(chart_container.first).to_be_visible(timeout=10000)
        
        # Check for at least minimum number of terms in table
        term_rows = page.locator('table tbody tr')
        term_count = term_rows.count()
        
        if term_count < min_terms:
            print(f"Warning: Only {term_count} terms found, expected at least {min_terms}")
            return False
        
        # Check for export buttons
        csv_button = page.locator('text=Descargar CSV')
        json_button = page.locator('text=Descargar JSON')
        
        expect(csv_button).to_be_visible()
        expect(json_button).to_be_visible()
        
        return True
        
    except Exception as e:
        print(f"Results verification failed: {e}")
        return False


def start_analysis(page: Page) -> bool:
    """
    Click the "Ejecutar Análisis" button to start analysis.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if button was clicked successfully
    """
    try:
        run_button = page.locator('button:has-text("▶️ Ejecutar Análisis")')
        expect(run_button).to_be_visible(timeout=5000)
        run_button.click()
        
        # Wait for analysis to actually start
        page.wait_for_selector(
            'text=Análisis en progreso',
            state="visible",
            timeout=5000
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to start analysis: {e}")
        return False


def get_analysis_summary(page: Page) -> Dict[str, Any]:
    """
    Extract summary statistics from displayed results.
    
    Args:
        page: Playwright page object
        
    Returns:
        Dictionary with summary metrics
    """
    summary = {
        'total_documents': 0,
        'unique_terms': 0,
        'top_term': None,
        'execution_time': None
    }
    
    try:
        # Extract metrics from summary cards
        metrics = page.locator('.stMetric')
        
        for i in range(metrics.count()):
            metric = metrics.nth(i)
            text = metric.inner_text()
            
            if 'Documentos' in text:
                summary['total_documents'] = int(''.join(filter(str.isdigit, text)))
            elif 'Términos Únicos' in text:
                summary['unique_terms'] = int(''.join(filter(str.isdigit, text)))
            elif 'Término Top' in text:
                summary['top_term'] = text.split('\n')[1] if '\n' in text else None
            elif 'Tiempo de Ejecución' in text:
                summary['execution_time'] = text.split('\n')[1] if '\n' in text else None
        
    except Exception as e:
        print(f"Failed to extract summary: {e}")
    
    return summary


def switch_to_tab(page: Page, tab_name: str, timeout: int = 5000) -> float:
    """
    Switch to a specific results tab and measure switching time.
    
    Args:
        page: Playwright page object
        tab_name: Name of tab to switch to
        timeout: Maximum wait time in milliseconds
        
    Returns:
        Time taken to switch tabs in seconds
    """
    start_time = time.time()
    
    try:
        # Click tab
        tab = page.locator(f'button:has-text("{tab_name}")')
        expect(tab).to_be_visible(timeout=timeout)
        tab.click()
        
        # Wait for tab content to be visible
        page.wait_for_timeout(500)  # Brief wait for render
        
        elapsed = time.time() - start_time
        return elapsed
        
    except Exception as e:
        print(f"Failed to switch to tab '{tab_name}': {e}")
        return -1
