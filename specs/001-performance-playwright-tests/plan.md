# Implementation Plan: Performance Optimization & Automated E2E Testing

**Branch**: `001-performance-playwright-tests` | **Date**: 2025-10-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-performance-playwright-tests/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature delivers 30-40% performance improvements to the Historical Term Analyzer through optimized caching, dynamic parallel processing, and memory management. Additionally, it establishes a comprehensive E2E testing framework using Playwright to validate critical user workflows with 90% coverage and <10 minute execution time.

**Primary Requirements**:
- Reduce 300-page analysis time from 20-25 min to ≤15 min
- Maintain memory usage below 500MB across multiple analyses
- Implement automated E2E tests with Playwright for workflow validation
- Support headless test execution for CI/CD integration

**Technical Approach**:
- Implement multi-level caching (parsed HTML, extracted terms) with LRU eviction
- Dynamic worker pool scaling based on available CPU cores
- Connection pooling for Internet Archive API requests
- Explicit garbage collection triggers after memory-intensive operations
- Playwright test framework with fixture-based mocking for deterministic testing

## Technical Context

**Language/Version**: Python 3.8+ (leveraging async/await, type hints, dataclasses)  
**Primary Dependencies**: Streamlit 1.28+, BeautifulSoup4 4.12+, Plotly 5.15+, Pandas 1.5+, requests 2.28+, Playwright 1.40+ (for testing)  
**Storage**: In-memory session state (Streamlit), file-based cache (optional persistent layer)  
**Testing**: unittest (existing unit tests), Playwright (new E2E tests), pytest (test runner)  
**Target Platform**: Linux/macOS/Windows desktop environments with web browser  
**Project Type**: Single project - Streamlit web application with monolithic architecture  
**Performance Goals**: 30-40% reduction in analysis time, <500MB memory footprint, cache hit rate >40%  
**Constraints**: Internet Archive API rate limiting (1.0s delay), 4+ CPU cores recommended, standard browser compatibility  
**Scale/Scope**: Single-user desktop application, 1-10 concurrent analyses per session, 100-1000 web pages per analysis

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Modular Architecture ✅ PASS

- Performance optimizations maintain separation between `historical_term_analyzer.py` (backend) and `streamlit_app.py` (frontend)
- Caching and parallel processing modules can be implemented as independent components
- Test framework is completely decoupled from application logic

### Principle II: User-First Experience ✅ PASS

- Performance improvements directly address user pain point (long wait times)
- Memory optimization prevents crashes during extended sessions
- Maintains existing real-time progress indicators and feedback mechanisms

### Principle III: Testability & Validation ✅ PASS

- E2E testing framework (Playwright) directly supports this principle
- Performance metrics can be measured independently (execution time, memory usage)
- Test fixtures enable deterministic testing without live API dependency

### Principle IV: Performance Consciousness ✅ PASS

- **Core focus of this feature**: Optimizing caching, parallel processing, memory management
- Implements exactly what the constitution requires (cache strategies, bounded memory)
- Dynamic worker scaling aligns with efficient resource utilization

### Principle V: Graceful External Dependencies ✅ PASS

- Maintains existing rate limiting and retry logic for Internet Archive API
- Connection pooling reduces overhead without violating rate limits
- Test mocking eliminates external dependency during automated testing

### Principle VI: Data Transparency ✅ PASS

- No changes to existing export functionality (CSV/JSON)
- Performance metrics themselves become transparent (cache hit rate, execution time)
- Test results include detailed logs and screenshots for debugging

### Principle VII: Semantic Versioning & Change Documentation ✅ PASS

- Feature will be documented in `CHANGELOG.md` as MINOR version bump (new capabilities)
- `GUIA_USO.md` will be updated if performance characteristics change user workflows
- Test framework documentation will be added to development guides

**Gate Status**: ✅ ALL GATES PASSED - Proceed to Phase 0 Research

## Project Structure

### Documentation (this feature)

```text
specs/001-performance-playwright-tests/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - caching strategies, Playwright setup
├── data-model.md        # Phase 1 output - performance metrics, cache entries, test results
├── quickstart.md        # Phase 1 output - developer guide for running optimized analyzer + tests
├── contracts/           # Phase 1 output - performance monitoring interfaces
│   └── performance-monitoring.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single project structure (existing)
/
├── historical_term_analyzer.py    # Backend - to be optimized
├── streamlit_app.py                # Frontend - UI optimizations
├── requirements.txt                # Dependencies (add: playwright, pytest-playwright)
├── test_historical_analyzer.py     # Existing unit tests
├── test_cdx_connection.py          # Existing integration tests
│
├── tests/                          # NEW: E2E test directory
│   ├── e2e/                        # Playwright E2E tests
│   │   ├── __init__.py
│   │   ├── conftest.py            # Pytest fixtures, mocks
│   │   ├── test_analysis_workflow.py
│   │   ├── test_visualization.py
│   │   ├── test_export.py
│   │   └── test_history_navigation.py
│   ├── fixtures/                   # Mock data for testing
│   │   ├── mock_cdx_responses.json
│   │   └── mock_html_content.html
│   └── screenshots/                # Test failure screenshots
│
├── performance/                    # NEW: Performance optimization modules
│   ├── __init__.py
│   ├── cache_manager.py           # Multi-level caching implementation
│   ├── worker_pool.py             # Dynamic parallel processing
│   └── memory_profiler.py         # Memory monitoring utilities
│
└── .github/
    └── workflows/
        └── e2e-tests.yml          # NEW: CI/CD workflow for automated testing
```

**Structure Decision**: Single project structure with new directories for E2E tests (`tests/e2e/`) and performance modules (`performance/`). This maintains the existing monolithic architecture while organizing new components logically. The `tests/` directory follows the constitution's `test_*.py` naming convention at the root level for compatibility, while organizing E2E tests separately to distinguish them from existing unit/integration tests.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations identified** - All constitution principles align with this feature's requirements. Performance optimization and testing framework directly support existing architectural principles.

## Phase Summary

### Phase 0: Research ✅ COMPLETE

**Artifacts Generated**:

- `research.md` - Comprehensive research on caching strategies, parallel processing, memory management, and Playwright testing

**Key Decisions**:

1. **Caching**: Multi-level LRU cache using functools.lru_cache + custom disk fallback
2. **Parallel Processing**: ThreadPoolExecutor with dynamic worker count (CPU-bound vs I/O-bound)
3. **Memory Management**: Explicit gc.collect() triggers + lazy-loading for visualizations
4. **Connection Pooling**: requests.Session with HTTPAdapter
5. **E2E Testing**: Playwright with pytest-playwright plugin
6. **Test Fixtures**: JSON-based mock data for deterministic tests
7. **CI/CD**: GitHub Actions with headless browser execution

**All NEEDS CLARIFICATION resolved** - No ambiguities remain.

### Phase 1: Design & Contracts ✅ COMPLETE

**Artifacts Generated**:

- `data-model.md` - Entities for PerformanceMetric, CacheEntry, TestScenario, TestResult, WorkerPool
- `contracts/performance-monitoring.md` - Interfaces for CacheManager, PerformanceMonitor, WorkerPoolManager, TestRunner
- `quickstart.md` - Developer guide with installation, usage, and troubleshooting
- `.github/copilot-instructions.md` - Updated with new technologies (Playwright, pytest)

**Key Entities Defined**:

1. **PerformanceMetric**: Timing and resource measurements
2. **CacheEntry**: Cached computation results with LRU tracking
3. **TestScenario**: E2E test definitions with setup/actions/assertions
4. **TestResult**: Test execution outcomes with artifacts
5. **WorkerPool**: Dynamic parallel processing configuration

**Contract Interfaces**:

1. **CacheManager**: get(), put(), invalidate(), clear(), get_statistics()
2. **PerformanceMonitor**: start_phase(), end_phase(), record_metric(), get_summary()
3. **WorkerPoolManager**: create_pool(), submit_task(), shutdown()
4. **TestRunner**: register_scenario(), run_scenario(), run_all(), generate_report()

**Constitution Re-Check**: ✅ ALL GATES STILL PASSED after design phase.

### Phase 2: Tasks (Next Step)

Ready to proceed to `/speckit.tasks` command to generate detailed implementation tasks.

**Expected Task Categories**:

1. **Setup**: Project structure, dependencies, CI/CD configuration
2. **Performance Module**: Cache manager, worker pool, memory profiler
3. **Analyzer Integration**: Update existing code with performance optimizations
4. **E2E Testing**: Test framework, fixtures, test scenarios
5. **Documentation**: Update user guides with performance improvements
6. **Validation**: Performance benchmarks, regression tests

## Implementation Readiness

✅ All planning phases complete  
✅ No constitution violations  
✅ All research questions resolved  
✅ Entities and contracts defined  
✅ Developer guide available  
✅ Agent context updated

**Status**: Ready for task generation (`/speckit.tasks`) and implementation.
