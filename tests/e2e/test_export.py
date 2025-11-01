"""
E2E Tests for Export Functionality
Tests CSV export, JSON export, and empty results handling

T057: test_csv_export_functionality - validates CSV download
T058: test_json_export_functionality - validates JSON download
T059: test_export_empty_results - edge case for empty analysis
"""

import pytest
from playwright.sync_api import Page, expect, Download
import json
import csv
import io
from pathlib import Path
from tests.e2e.helpers import (
    configure_analysis,
    start_analysis,
    wait_for_analysis_complete,
    switch_to_tab
)
from tests.e2e.models import QUICK_TEST_SCENARIO


def test_csv_export_functionality(page: Page, app_url: str):
    """
    T057: Validate CSV export downloads with correct data.
    
    Tests:
    1. CSV download button is visible
    2. Click triggers download
    3. Downloaded file contains valid CSV data
    4. CSV has expected columns (Término, Frecuencia)
    5. CSV contains actual term data
    """
    # Navigate and run analysis
    page.goto(app_url, wait_until="networkidle")
    
    configure_analysis(
        page,
        start_year=QUICK_TEST_SCENARIO.start_year,
        end_year=QUICK_TEST_SCENARIO.end_year,
        max_documents=QUICK_TEST_SCENARIO.max_documents,
        domains=QUICK_TEST_SCENARIO.domains
    )
    
    assert start_analysis(page), "Failed to start analysis"
    assert wait_for_analysis_complete(page, timeout=120000), "Analysis timeout"
    
    # Switch to export tab
    switch_time = switch_to_tab(page, "📁 Exportar")
    assert switch_time > 0, "Failed to switch to export tab"
    
    # Find CSV download button
    csv_button = page.locator('button:has-text("Descargar CSV")')
    expect(csv_button).to_be_visible(timeout=5000)
    
    # Setup download handler and click
    with page.expect_download() as download_info:
        csv_button.click()
    
    download = download_info.value
    
    # Verify download occurred
    assert download is not None, "CSV download did not trigger"
    
    # Verify filename pattern
    filename = download.suggested_filename
    assert filename.endswith('.csv'), f"Downloaded file is not CSV: {filename}"
    assert 'top_terms' in filename.lower(), f"Unexpected filename: {filename}"
    
    # Save and read download content
    download_path = f"/tmp/{filename}"
    download.save_as(download_path)
    
    # Parse CSV content
    with open(download_path, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        rows = list(csv_reader)
    
    # Validate CSV structure
    assert len(rows) > 0, "CSV file is empty"
    assert 'Término' in rows[0] or 'Termino' in rows[0], "CSV missing 'Término' column"
    assert 'Frecuencia' in rows[0], "CSV missing 'Frecuencia' column"
    
    # Validate data content
    first_row = rows[0]
    term_key = 'Término' if 'Término' in first_row else 'Termino'
    assert len(first_row[term_key]) > 0, "First term is empty"
    assert int(first_row['Frecuencia']) > 0, "First frequency is not positive"
    
    # Cleanup
    Path(download_path).unlink(missing_ok=True)
    
    print(f"✅ CSV export test passed ({len(rows)} terms exported)")


def test_json_export_functionality(page: Page, app_url: str):
    """
    T058: Validate JSON export downloads with correct structure.
    
    Tests:
    1. JSON download button is visible
    2. Click triggers download
    3. Downloaded file contains valid JSON
    4. JSON has expected structure (summary, top_terms, metadata)
    5. JSON contains actual analysis data
    """
    # Navigate and run analysis
    page.goto(app_url, wait_until="networkidle")
    
    configure_analysis(
        page,
        start_year=QUICK_TEST_SCENARIO.start_year,
        end_year=QUICK_TEST_SCENARIO.end_year,
        max_documents=QUICK_TEST_SCENARIO.max_documents,
        domains=QUICK_TEST_SCENARIO.domains
    )
    
    assert start_analysis(page), "Failed to start analysis"
    assert wait_for_analysis_complete(page, timeout=120000), "Analysis timeout"
    
    # Switch to export tab
    switch_time = switch_to_tab(page, "📁 Exportar")
    assert switch_time > 0, "Failed to switch to export tab"
    
    # Find JSON download button
    json_button = page.locator('button:has-text("Descargar JSON")')
    expect(json_button).to_be_visible(timeout=5000)
    
    # Setup download handler and click
    with page.expect_download() as download_info:
        json_button.click()
    
    download = download_info.value
    
    # Verify download occurred
    assert download is not None, "JSON download did not trigger"
    
    # Verify filename pattern
    filename = download.suggested_filename
    assert filename.endswith('.json'), f"Downloaded file is not JSON: {filename}"
    assert 'analysis_results' in filename.lower(), f"Unexpected filename: {filename}"
    
    # Save and read download content
    download_path = f"/tmp/{filename}"
    download.save_as(download_path)
    
    # Parse JSON content
    with open(download_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate JSON structure
    assert 'summary' in data or 'top_terms' in data, "JSON missing expected keys"
    
    if 'top_terms' in data:
        assert isinstance(data['top_terms'], list), "top_terms is not a list"
        assert len(data['top_terms']) > 0, "top_terms list is empty"
        
        # Validate first term structure
        first_term = data['top_terms'][0]
        assert isinstance(first_term, list) and len(first_term) == 2, \
            "Term entry is not [term, frequency] pair"
        assert isinstance(first_term[0], str), "Term is not a string"
        assert isinstance(first_term[1], (int, float)), "Frequency is not a number"
    
    if 'analysis_metadata' in data:
        metadata = data['analysis_metadata']
        assert isinstance(metadata, dict), "Metadata is not a dictionary"
    
    # Cleanup
    Path(download_path).unlink(missing_ok=True)
    
    print(f"✅ JSON export test passed")


def test_export_empty_results(page: Page, app_url: str):
    """
    T059: Validate graceful handling of export with empty/minimal results.
    
    Tests:
    1. Export buttons are still visible with minimal data
    2. CSV export doesn't crash with few terms
    3. JSON export doesn't crash with minimal data
    4. Downloads still work correctly
    
    Note: This test uses minimal document count to simulate near-empty results
    """
    # Navigate to app
    page.goto(app_url, wait_until="networkidle")
    
    # Configure analysis with very small dataset
    configure_analysis(
        page,
        start_year=2020,
        end_year=2020,
        max_documents=5,  # Minimal documents
        domains=['clarin.com']
    )
    
    assert start_analysis(page), "Failed to start analysis"
    
    # Wait for completion (should be quick with only 5 docs)
    assert wait_for_analysis_complete(page, timeout=60000), "Analysis timeout"
    
    # Switch to export tab
    switch_time = switch_to_tab(page, "📁 Exportar")
    assert switch_time > 0, "Failed to switch to export tab"
    
    # Verify export buttons exist even with minimal data
    csv_button = page.locator('button:has-text("Descargar CSV")')
    json_button = page.locator('button:has-text("Descargar JSON")')
    
    expect(csv_button).to_be_visible(timeout=5000)
    expect(json_button).to_be_visible(timeout=5000)
    
    # Test CSV export with minimal data
    with page.expect_download(timeout=10000) as download_info:
        csv_button.click()
    
    csv_download = download_info.value
    assert csv_download is not None, "CSV download failed with minimal data"
    
    # Verify CSV is valid
    csv_path = f"/tmp/minimal_{csv_download.suggested_filename}"
    csv_download.save_as(csv_path)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "CSV file is empty"
        # Should have at least header
        assert 'Frecuencia' in content or 'Frequency' in content, "CSV missing header"
    
    Path(csv_path).unlink(missing_ok=True)
    
    # Test JSON export with minimal data
    with page.expect_download(timeout=10000) as download_info:
        json_button.click()
    
    json_download = download_info.value
    assert json_download is not None, "JSON download failed with minimal data"
    
    # Verify JSON is valid
    json_path = f"/tmp/minimal_{json_download.suggested_filename}"
    json_download.save_as(json_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert isinstance(data, dict), "JSON is not a valid object"
    
    Path(json_path).unlink(missing_ok=True)
    
    print("✅ Empty results export test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
