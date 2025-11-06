"""
E2E Test Helpers for Historical Term Analyzer
Reusable utilities for Playwright-based end-to-end tests

T048: Base test helpers for E2E testing infrastructure
"""

from playwright.sync_api import Page, expect
import time
from typing import Dict, Any, Optional
import re


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
        # If a progress token appears, wait for it to hide (normal long-running flow)
        try:
            page.wait_for_selector("[data-testid='analysis-progress']", state="visible", timeout=3000)
            page.wait_for_selector("[data-testid='analysis-progress']", state="hidden", timeout=timeout)
        except Exception:
            # No progress token visible quickly — maybe the analysis completed fast.
            # Check for direct completion token and return if present.
            try:
                page.wait_for_selector("[data-testid='analysis-complete']", state="visible", timeout=min(timeout, 5000))
                return True
            except Exception:
                # Fallback to textual tokens if data-testid is not present
                try:
                    page.wait_for_selector("text=Análisis en progreso", state="hidden", timeout=timeout)
                except Exception:
                    try:
                        page.wait_for_selector("text=Analysis in progress", state="hidden", timeout=timeout)
                    except Exception:
                        # As a final fallback, wait for the completion token or results header
                        page.wait_for_selector("[data-testid='analysis-complete']", state="visible", timeout=timeout)

        # Wait for results header preferring English header used in E2E tests
        try:
            page.wait_for_selector("text=Analysis Results", state="visible", timeout=10000)
        except Exception:
            page.wait_for_selector("text=📊 Resultados del Análisis", state="visible", timeout=10000)

        return True

    except Exception as e:
        print(f"Analysis completion wait failed: {e}")
        return False
    finally:
        # As a safety net: poll briefly for completion token or results header
        try:
            for _ in range(10):
                try:
                    if page.locator("[data-testid='analysis-complete']").count():
                        return True
                except Exception:
                    pass
                try:
                    if page.locator("text=Analysis Results").count():
                        return True
                except Exception:
                    pass
                try:
                    if page.locator("text=📊 Resultados del Análisis").count():
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
        except Exception:
            pass


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
    
    # Ensure the Streamlit app root is ready
    try:
        page.wait_for_selector("div[data-testid='stApp']", timeout=10000)
    except Exception:
        pass

    # Locate start and end year inputs with multiple fallbacks
    start_year_input = None
    end_year_input = None

    # 1) Try explicit aria-label selectors (Spanish then English)
    try:
        start_year_input = page.locator("input[aria-label*='Año Inicial'], input[aria-label*='Start year']").first
    except Exception:
        start_year_input = None

    try:
        end_year_input = page.locator("input[aria-label*='Año Final'], input[aria-label*='End year']").first
    except Exception:
        end_year_input = None

    # 2) If missing, fall back to sidebar number inputs (Streamlit renders two number_inputs in the sidebar)
    try:
        if (not start_year_input or start_year_input.count() == 0) or (not end_year_input or end_year_input.count() == 0):
            sidebar_numbers = page.locator("section[role='complementary'] input[type='number']")
            if sidebar_numbers.count() >= 2:
                # Assume first is start, second is end
                start_year_input = sidebar_numbers.nth(0)
                end_year_input = sidebar_numbers.nth(1)
    except Exception:
        pass

    # Ensure we have inputs; otherwise try a broad selector
    if not start_year_input or start_year_input.count() == 0:
        start_year_input = page.locator("input[type='number']").first
    if not end_year_input or end_year_input.count() == 0:
        # Prefer the second number input if available
        try:
            num_inputs = page.locator("input[type='number']")
            if num_inputs.count() >= 2:
                end_year_input = num_inputs.nth(1)
            else:
                end_year_input = num_inputs.first
        except Exception:
            end_year_input = page.locator("input[type='number']").first

    # Ensure end_year > start_year, otherwise the sidebar validation hides controls
    if end_year <= start_year:
        end_year_corrected = start_year + 1
    else:
        end_year_corrected = end_year

    # Fill start year - clear first then set to ensure fresh value
    try:
        start_year_input.click()
        start_year_input.fill('')  # Clear existing value
        start_year_input.type(str(start_year), delay=50)
        start_year_input.press('Tab')  # Trigger onchange
    except Exception:
        try:
            # JS fallback
            handle = start_year_input.element_handle()
            if handle:
                page.evaluate("(el, val) => { el.value = ''; el.value = val; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }", handle, str(start_year))
        except Exception:
            pass

    # Fill end year - clear first then set
    try:
        end_year_input.click()
        end_year_input.fill('')  # Clear existing value
        end_year_input.type(str(end_year_corrected), delay=50)
        end_year_input.press('Tab')  # Trigger onchange
    except Exception:
        try:
            # JS fallback
            handle = end_year_input.element_handle()
            if handle:
                page.evaluate("(el, val) => { el.value = ''; el.value = val; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }", handle, str(end_year_corrected))
        except Exception:
            pass
    
    # Fill in max documents (use exact aria-label created by Streamlit number_input)
    try:
        max_docs_input = page.get_by_label(re.compile(r"Máximo de páginas web|Maximo de páginas web|Number of pages|Máximo", re.I)).first
        max_docs_input.fill(str(max_documents))
    except Exception:
        try:
            max_docs_input = page.locator("input[aria-label='Máximo de páginas web'], input[aria-label='Number of pages']").first
            max_docs_input.fill(str(max_documents))
        except Exception:
            pass
    
    # Select domains (click labels in the multiselect if visible)
    for domain in domains:
        try:
            domain_item = page.locator(f'label:has-text("{domain}")').first
            if domain_item.is_visible():
                domain_item.click()
        except Exception:
            # ignore if domain item not present in multiselect
            pass
    
    # Optional search term (main pane uses English aria-label)
    if search_term:
        try:
            search_input = page.get_by_label(re.compile(r"Search term|Término de búsqueda", re.I)).first
            if search_input.is_visible():
                search_input.fill(search_term)
        except Exception:
            try:
                search_input = page.locator("input[aria-label='Search term'], input[aria-label*='Término']").first
                search_input.fill(search_term)
            except Exception:
                pass
    
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
        # If we're on an e2e_auto URL (left by a previous fallback), navigate to base URL
        try:
            if 'e2e_auto=1' in page.url:
                base = page.url.split('?')[0]
                page.goto(base, wait_until='networkidle')
                time.sleep(1)
        except Exception:
            pass

        # Wait for the app to be fully loaded and interactive
        page.wait_for_selector("div[data-testid='stApp']", state="visible", timeout=10000)
        
        # Try multiple strategies to find and click the run button
        button_clicked = False
        
        # Strategy 1: Look for English "Analyze" button
        try:
            analyze_btn = page.locator("button:has-text('Analyze')").first
            if analyze_btn.is_visible(timeout=2000):
                analyze_btn.click(timeout=5000)
                button_clicked = True
        except Exception:
            pass
        
        # Strategy 2: Look for Spanish "Ejecutar" button
        if not button_clicked:
            try:
                ejecutar_btn = page.locator("button:has-text('▶️ Ejecutar Análisis')").first
                if ejecutar_btn.is_visible(timeout=2000):
                    ejecutar_btn.click(timeout=5000)
                    button_clicked = True
            except Exception:
                pass
        
        # Strategy 3: Use role-based selector with regex
        if not button_clicked:
            try:
                role_btn = page.get_by_role('button', name=re.compile(r'Analy|Ejecut', re.I)).first
                if role_btn.is_visible(timeout=2000):
                    role_btn.click(timeout=5000)
                    button_clicked = True
            except Exception:
                pass
        
        # Strategy 4: Find any primary button (Streamlit type="primary")
        if not button_clicked:
            try:
                primary_btns = page.locator("button[kind='primary'], button[data-testid*='baseButton-primary']")
                for i in range(min(3, primary_btns.count())):
                    btn = primary_btns.nth(i)
                    text = btn.inner_text().lower()
                    if 'analyz' in text or 'ejecut' in text:
                        btn.click(timeout=5000)
                        button_clicked = True
                        break
            except Exception:
                pass
        
        if not button_clicked:
            print("Could not find run button with any strategy")
            return False

        # Wait for progress or completion indicator after clicking
        try:
            page.wait_for_selector("[data-testid='analysis-progress']", state="visible", timeout=30000)
            return True
        except Exception:
            try:
                page.wait_for_selector("[data-testid='analysis-complete']", state="visible", timeout=30000)
                return True
            except Exception:
                try:
                    page.wait_for_selector('text=Analysis in progress', state="visible", timeout=5000)
                    return True
                except Exception:
                    print("No progress indicator appeared after clicking")
                    return False

    except Exception as e:
        print(f"Failed to start analysis (exception): {e}")
        import traceback
        traceback.print_exc()
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
        # Wait a moment for metrics to render
        page.wait_for_timeout(1000)
        
        # Try both data-testid and class selectors
        metrics = page.locator('[data-testid="stMetric"], .stMetric, [data-testid="metric"]')
        
        if metrics.count() == 0:
            print("No metrics found, trying alternative selectors")
            # Fallback: look for metric-like structures
            metrics = page.locator('[data-testid*="metric"]')
        
        print(f"Found {metrics.count()} metric elements")
        
        for i in range(metrics.count()):
            metric = metrics.nth(i)
            try:
                text = metric.inner_text()
                print(f"Metric {i}: {text[:100]}")
                lines = text.split('\n')
                
                # Look for both Spanish and English metric labels
                if any(keyword in text for keyword in ['Total de Páginas', 'Documentos', 'Documents', 'Páginas']):
                    try:
                        # Extract number from lines
                        for line in lines:
                            num_str = ''.join(filter(str.isdigit, line))
                            if num_str and len(num_str) >= 1:
                                summary['total_documents'] = int(num_str)
                                break
                    except (ValueError, IndexError) as e:
                        print(f"Failed to parse documents: {e}")
                        
                elif any(keyword in text for keyword in ['Términos Únicos', 'Unique Terms', 'Términos']):
                    try:
                        for line in lines:
                            num_str = ''.join(filter(str.isdigit, line))
                            if num_str and len(num_str) >= 1:
                                summary['unique_terms'] = int(num_str)
                                break
                    except (ValueError, IndexError) as e:
                        print(f"Failed to parse terms: {e}")
                        
                elif any(keyword in text for keyword in ['Término Top', 'Top Term']):
                    # Extract the value line (should be second or third line)
                    for idx, line in enumerate(lines):
                        if line.strip() and idx > 0:  # Skip the label line
                            summary['top_term'] = line.strip()
                            break
                        
                elif any(keyword in text for keyword in ['Tiempo', 'Time', 'Análisis']):
                    for idx, line in enumerate(lines):
                        if line.strip() and idx > 0 and ('min' in line or 'sec' in line or 's' in line):
                            summary['execution_time'] = line.strip()
                            break
            except Exception as e:
                print(f"Error processing metric {i}: {e}")
                continue
        
    except Exception as e:
        print(f"Failed to extract summary: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Extracted summary: {summary}")
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
