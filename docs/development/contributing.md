# Contributing to Trapper Keeper MCP

Thank you for your interest in contributing to Trapper Keeper MCP! This guide will help you get started.

## Code of Conduct

Please read and follow our [Code of Conduct](../../CODE_OF_CONDUCT.md) to ensure a welcoming environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Poetry (recommended) or pip
- Node.js (for pre-commit hooks)

### Development Setup

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/trapper-keeper-mcp.git
cd trapper-keeper-mcp
```

2. **Create Virtual Environment**

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using poetry (recommended)
poetry install
poetry shell
```

3. **Install Development Dependencies**

```bash
# Using pip
pip install -e ".[dev]"

# Using poetry
poetry install --with dev
```

4. **Install Pre-commit Hooks**

```bash
pre-commit install
pre-commit run --all-files  # Run all checks
```

5. **Configure Git**

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Development Workflow

### 1. Create a Branch

```bash
# For features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/issue-description

# For documentation
git checkout -b docs/what-you-are-documenting
```

### 2. Make Changes

Follow these guidelines:

- Write clear, self-documenting code
- Add docstrings to all public functions and classes
- Update tests for new functionality
- Update documentation as needed

### 3. Code Style

We use several tools to maintain code quality:

```bash
# Format code with black
black src tests

# Sort imports with isort
isort src tests

# Check style with flake8
flake8 src tests

# Type checking with mypy
mypy src
```

All these checks run automatically with pre-commit.

### 4. Write Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trapper_keeper --cov-report=html

# Run specific test file
pytest tests/unit/test_content_extractor.py

# Run specific test
pytest tests/unit/test_content_extractor.py::test_extract_content

# Run with verbose output
pytest -vv
```

### 5. Update Documentation

- Update docstrings for API changes
- Update relevant markdown files in `docs/`
- Add examples if introducing new features
- Update CHANGELOG.md

### 6. Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <subject>

# Examples:
git commit -m "feat(extractor): add support for custom categories"
git commit -m "fix(monitor): handle file permission errors"
git commit -m "docs(api): update extraction options documentation"
git commit -m "test(parser): add edge case tests for markdown parsing"
git commit -m "refactor(core): simplify event bus implementation"
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

### 7. Push and Create PR

```bash
# Push your branch
git push origin your-branch-name
```

Then create a Pull Request on GitHub with:
- Clear title following commit convention
- Description of changes
- Link to related issue(s)
- Screenshots for UI changes

## Project Structure

```
trapper-keeper-mcp/
├── src/trapper_keeper/     # Main source code
│   ├── core/              # Core functionality
│   ├── extractor/         # Content extraction
│   ├── monitoring/        # File monitoring
│   ├── parser/           # Document parsers
│   ├── organizer/        # Document organization
│   ├── mcp/             # MCP server implementation
│   ├── cli/             # CLI commands
│   └── utils/           # Utilities
├── tests/                # Test files
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
├── docs/                # Documentation
├── examples/            # Example code and configs
└── scripts/             # Development scripts
```

## Testing Guidelines

### Test Structure

```python
# tests/unit/test_example.py
import pytest
from trapper_keeper.core import Example

class TestExample:
    """Test cases for Example class."""
    
    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        example = Example()
        result = example.process("input")
        assert result == "expected output"
    
    @pytest.mark.parametrize("input,expected", [
        ("test1", "output1"),
        ("test2", "output2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input cases."""
        example = Example()
        assert example.process(input) == expected
    
    def test_error_handling(self):
        """Test error handling."""
        example = Example()
        with pytest.raises(ValueError):
            example.process(None)
```

### Test Coverage

We aim for at least 80% test coverage:

```bash
# Check coverage
pytest --cov=trapper_keeper --cov-report=term-missing

# Generate HTML report
pytest --cov=trapper_keeper --cov-report=html
# Open htmlcov/index.html in browser
```

### Testing Best Practices

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Fixtures**: Use pytest fixtures for reusable test data
4. **Mocking**: Mock external dependencies
5. **Async Tests**: Use `pytest-asyncio` for async code

## Code Guidelines

### Python Style

```python
"""Module docstring explaining purpose."""

from typing import List, Optional, Dict, Any
import asyncio

from trapper_keeper.core.base import BaseClass


class ExampleClass(BaseClass):
    """Class docstring with description.
    
    Attributes:
        name: Description of name attribute
        value: Description of value attribute
    """
    
    def __init__(self, name: str, value: Optional[int] = None):
        """Initialize ExampleClass.
        
        Args:
            name: The name for this instance
            value: Optional value parameter
        """
        self.name = name
        self.value = value or 0
    
    async def process(self, data: List[str]) -> Dict[str, Any]:
        """Process data asynchronously.
        
        Args:
            data: List of strings to process
            
        Returns:
            Dictionary containing processed results
            
        Raises:
            ValueError: If data is empty
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        results = {}
        for item in data:
            # Process each item
            result = await self._process_item(item)
            results[item] = result
        
        return results
    
    async def _process_item(self, item: str) -> Any:
        """Private method for processing individual items."""
        # Implementation here
        await asyncio.sleep(0.1)  # Simulate async work
        return item.upper()
```

### Documentation Style

- Use Google-style docstrings
- Include type hints for all parameters
- Document return values and exceptions
- Add examples for complex functions

```python
def complex_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """Brief description of function.
    
    Longer description explaining what the function does,
    when to use it, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2 with default
        
    Returns:
        Description of return value structure
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> result = complex_function("test", 20)
        >>> print(result)
        {'value': 'TEST', 'count': 20}
    """
```

## Adding New Features

### 1. Create New Category

To add a new extraction category:

```python
# src/trapper_keeper/core/types.py
class ExtractionCategory(str, Enum):
    # ... existing categories ...
    YOUR_CATEGORY = "🆕 Your Category"
```

```python
# src/trapper_keeper/extractor/category_detector.py
DEFAULT_PATTERNS = {
    # ... existing patterns ...
    ExtractionCategory.YOUR_CATEGORY: {
        "keywords": ["your", "keywords", "here"],
        "patterns": [r".*your pattern.*"],
        "importance_boost": 0.2
    }
}
```

### 2. Create New Parser

To support a new file format:

```python
# src/trapper_keeper/parser/your_parser.py
from typing import Optional
from pathlib import Path

from .base import Parser
from ..core.types import Document

class YourParser(Parser):
    """Parser for your file format."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file."""
        return file_path.suffix in ['.your', '.format']
    
    def parse(self, file_path: Path) -> Document:
        """Parse the file into a Document."""
        # Implementation here
        pass
```

Register in parser factory:

```python
# src/trapper_keeper/parser/parser_factory.py
from .your_parser import YourParser

PARSERS = [
    MarkdownParser(),
    YourParser(),  # Add here
]
```

### 3. Create New MCP Tool

```python
# src/trapper_keeper/mcp/tools/your_tool.py
from pydantic import BaseModel, Field
from .base import BaseTool

class YourToolRequest(BaseModel):
    """Request model for your tool."""
    param1: str = Field(..., description="Description")
    param2: int = Field(10, description="Description")

class YourToolResponse(BaseModel):
    """Response model for your tool."""
    success: bool
    result: str

class YourTool(BaseTool):
    """Your tool description."""
    
    name = "your_tool"
    description = "What your tool does"
    
    async def run(self, request: YourToolRequest) -> YourToolResponse:
        """Execute your tool."""
        # Implementation here
        return YourToolResponse(success=True, result="Done")
```

## Debugging

### Debug Configuration

VS Code `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug CLI",
            "type": "python",
            "request": "launch",
            "module": "trapper_keeper.cli",
            "args": ["process", "test.md"],
            "console": "integratedTerminal"
        },
        {
            "name": "Debug MCP Server",
            "type": "python",
            "request": "launch",
            "module": "trapper_keeper.mcp.server",
            "console": "integratedTerminal",
            "env": {
                "TRAPPER_KEEPER_LOG_LEVEL": "DEBUG"
            }
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-xvs", "${file}"],
            "console": "integratedTerminal"
        }
    ]
}
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Debug logging
logger.debug("Detailed information: %s", variable)

# Info logging
logger.info("Processing file: %s", file_path)

# Warning logging
logger.warning("Deprecated feature used: %s", feature)

# Error logging
logger.error("Failed to process: %s", error)
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. GitHub Actions will handle the rest

## Getting Help

- **Discord**: Join our [Discord server](https://discord.gg/trapper-keeper)
- **Issues**: Check [existing issues](https://github.com/yourusername/trapper-keeper-mcp/issues)
- **Discussions**: Start a [discussion](https://github.com/yourusername/trapper-keeper-mcp/discussions)

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes

Thank you for contributing to Trapper Keeper MCP! 🎉