# Trapper Keeper MCP Test Suite

This directory contains the comprehensive test suite for Trapper Keeper MCP, following Test-Driven Development (TDD) principles.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_file_monitor.py     # File monitoring tests
│   ├── test_markdown_parser.py  # Markdown parser tests
│   ├── test_content_extractor.py # Content extraction tests
│   └── test_category_detector.py # Category detection tests
├── integration/             # Integration tests
│   ├── test_mcp_tools.py       # MCP tool integration tests
│   └── test_cli_commands.py    # CLI command tests
├── e2e/                     # End-to-end tests
│   └── test_workflows.py       # Complete workflow tests
├── performance/             # Performance benchmarks
│   └── test_benchmarks.py      # Performance and scalability tests
├── fixtures/                # Test fixtures and data
├── conftest.py             # Shared pytest configuration
├── utils.py                # Test utilities and helpers
└── README.md               # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage
make test-all

# Run specific test types
make test-unit
make test-integration
make test-e2e
make test-performance
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trapper_keeper --cov-report=html

# Run specific test file
pytest tests/unit/test_file_monitor.py

# Run specific test
pytest tests/unit/test_file_monitor.py::TestFileMonitor::test_initialization

# Run tests matching pattern
pytest -k "test_extract"

# Run with verbose output
pytest -vv

# Run in parallel
pytest -n auto
```

### Using the test runner

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py --type unit

# Run with coverage
python run_tests.py --coverage

# Run in watch mode
python run_tests.py --watch

# Run benchmarks
python run_tests.py --benchmark
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 100ms per test)
- High coverage (>95% per module)

### Integration Tests
- Test component interactions
- Use real implementations where possible
- Test MCP server integration
- CLI command testing

### End-to-End Tests
- Complete workflow testing
- Real file operations
- Performance under load
- Error recovery scenarios

### Performance Tests
- Benchmark critical operations
- Memory usage monitoring
- Scalability testing
- Concurrent operation testing

## Coverage Requirements

- Overall coverage: >90%
- Unit test coverage: >95%
- Critical paths: 100%
- New code: 100%

## Writing Tests

### Test Structure

```python
class TestComponent:
    """Test ComponentName functionality."""
    
    @pytest.fixture
    def component(self):
        """Create component instance."""
        return Component()
    
    def test_feature(self, component):
        """Test specific feature."""
        # Arrange
        input_data = "test"
        
        # Act
        result = component.process(input_data)
        
        # Assert
        assert result.success
        assert result.output == "expected"
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation(self, component):
    """Test async operation."""
    result = await component.async_process()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_cases(self, component, input, expected):
    """Test with multiple input cases."""
    assert component.process(input) == expected
```

### Performance Tests

```python
def test_performance(self, benchmark, component):
    """Benchmark component performance."""
    result = benchmark(component.process, large_input)
    assert result is not None
```

## Test Utilities

### Document Factory

```python
from tests.utils import DocumentFactory

# Create simple document
doc = DocumentFactory.create_simple_document()

# Create complex document
doc = DocumentFactory.create_complex_document()

# Create with sections
doc = DocumentFactory.create_document_with_sections()
```

### File System Helper

```python
from tests.utils import FileSystemHelper

# Create test structure
FileSystemHelper.create_test_structure(temp_dir, {
    "docs": {
        "api.md": "# API Docs",
        "guide.md": "# Guide"
    }
})

# Generate test files
files = FileSystemHelper.generate_markdown_files(temp_dir, count=10)
```

### Async Test Helper

```python
from tests.utils import AsyncTestHelper

# Wait for condition
await AsyncTestHelper.wait_for_condition(
    lambda: component.is_ready,
    timeout=5.0
)

# Run with timeout
result = await AsyncTestHelper.run_with_timeout(
    component.long_operation(),
    timeout=10.0
)
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

CI Matrix:
- OS: Ubuntu, macOS, Windows
- Python: 3.8, 3.9, 3.10, 3.11, 3.12

## Debugging Tests

```bash
# Run with debugging output
pytest -vv -s

# Run with pdb on failure
pytest --pdb

# Run with breakpoint
pytest --trace

# Show local variables on failure
pytest -l

# Run specific test with full traceback
pytest path/to/test.py::test_name -vv --tb=long
```

## Performance Monitoring

```bash
# Run benchmarks
pytest tests/performance --benchmark-only

# Compare benchmarks
pytest tests/performance --benchmark-compare

# Save benchmark results
pytest tests/performance --benchmark-save=my_benchmark

# Generate benchmark report
pytest tests/performance --benchmark-histogram
```

## Best Practices

1. **Follow TDD**: Write tests first, then implementation
2. **Keep tests fast**: Unit tests should run in milliseconds
3. **Test one thing**: Each test should verify a single behavior
4. **Use descriptive names**: Test names should explain what they test
5. **Avoid test interdependence**: Tests should run in any order
6. **Mock external dependencies**: Unit tests should not hit network/disk
7. **Use fixtures**: Share setup code via pytest fixtures
8. **Test edge cases**: Include boundary conditions and error cases
9. **Maintain tests**: Update tests when requirements change
10. **Review test coverage**: Ensure critical paths are tested