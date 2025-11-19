"""Test to verify documents are distributed across years correctly"""

import pytest
from historical_term_analyzer import HistoricalTermAnalyzer


def test_documents_distributed_across_years():
    """Verify that analyze_period distributes documents across all requested years"""
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=1.0)
    
    # Request analysis for 3 years with 30 total documents
    # Should get 10 docs per year
    results = analyzer.analyze_period(
        start_year=2012,
        end_year=2014,
        max_documents=30,
        domains=['cnn.com'],
        analyze_by_year=True
    )
    
    assert 'error' not in results, f"Analysis failed: {results.get('error')}"
    assert 'results_by_year' in results, "Missing results_by_year"
    
    # Check that we have results for all 3 years
    results_by_year = results['results_by_year']
    years = sorted(results_by_year.keys())
    assert years == [2012, 2013, 2014], f"Expected [2012, 2013, 2014], got {years}"
    
    # Check document count per year (should be ~10 each)
    for year in [2012, 2013, 2014]:
        doc_count = results_by_year[year].get('document_count', 0)
        assert doc_count > 0, f"Year {year} has no documents"
        assert 8 <= doc_count <= 12, f"Year {year} has {doc_count} documents, expected ~10"
    
    # Check documents distribution
    if 'documents' in results:
        docs = results['documents']
        year_counts = {}
        for doc in docs:
            year_counts[doc.year] = year_counts.get(doc.year, 0) + 1
        
        assert len(year_counts) == 3, f"Documents only span {len(year_counts)} years instead of 3"
        assert all(count > 0 for count in year_counts.values()), "Some years have 0 documents"


def test_single_year_analysis():
    """Verify single year analysis still works"""
    analyzer = HistoricalTermAnalyzer(rate_limit_delay=1.0)
    
    results = analyzer.analyze_period(
        start_year=2012,
        end_year=2012,
        max_documents=10,
        domains=['cnn.com'],
        analyze_by_year=True
    )
    
    assert 'error' not in results
    assert 'results_by_year' in results
    assert list(results['results_by_year'].keys()) == [2012]
    assert results['results_by_year'][2012]['document_count'] == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
