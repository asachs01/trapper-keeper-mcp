"""Shared pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator, Dict, Any
from datetime import datetime
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

from trapper_keeper.core.base import EventBus, Component
from trapper_keeper.core.types import (
    Document,
    DocumentType,
    DocumentMetadata,
    DocumentSection,
    ExtractedContent,
    ExtractionCategory,
    ProcessingResult,
    ProcessingConfig,
    WatchConfig,
    OrganizationConfig,
    TrapperKeeperConfig,
    Event,
    EventType,
)


# Configure pytest-asyncio
pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample markdown content for testing."""
    return """---
title: Test Document
author: Test Author
tags: [test, sample]
---

# Test Document

This is a test document for unit testing.

## Architecture Overview

The system follows a microservices architecture with the following components:
- API Gateway
- Authentication Service
- User Service
- Database Layer

### Database Design

We use PostgreSQL with the following schema:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Security Considerations

Important security measures:
- JWT tokens for authentication
- Rate limiting on all endpoints
- Input validation and sanitization

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/users | GET | List all users |
| /api/users/:id | GET | Get user by ID |

## Testing Strategy

We follow TDD principles with:
1. Unit tests for all components
2. Integration tests for API endpoints
3. E2E tests for critical user flows
"""


@pytest.fixture
def sample_document(sample_markdown_content: str) -> Document:
    """Create a sample document for testing."""
    return Document(
        id="test-doc-1",
        type=DocumentType.MARKDOWN,
        content=sample_markdown_content,
        metadata=DocumentMetadata(
            path=Path("/test/doc.md"),
            size=len(sample_markdown_content),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            author="Test Author",
            tags={"test", "sample"},
        ),
        frontmatter={
            "title": "Test Document",
            "author": "Test Author",
            "tags": ["test", "sample"],
        },
    )


@pytest.fixture
def sample_extracted_content() -> List[ExtractedContent]:
    """Create sample extracted content."""
    return [
        ExtractedContent(
            id="extract-1",
            document_id="test-doc-1",
            category=ExtractionCategory.ARCHITECTURE,
            title="Architecture Overview",
            content="The system follows a microservices architecture...",
            importance=0.9,
            tags={"architecture", "microservices"},
        ),
        ExtractedContent(
            id="extract-2",
            document_id="test-doc-1",
            category=ExtractionCategory.DATABASE,
            title="Database Design",
            content="We use PostgreSQL with the following schema...",
            importance=0.8,
            tags={"database", "postgresql"},
        ),
        ExtractedContent(
            id="extract-3",
            document_id="test-doc-1",
            category=ExtractionCategory.SECURITY,
            title="Security Considerations",
            content="Important security measures...",
            importance=0.95,
            tags={"security", "authentication"},
        ),
    ]


@pytest.fixture
def mock_event_bus() -> EventBus:
    """Create a mock event bus."""
    bus = Mock(spec=EventBus)
    bus.subscribe = AsyncMock()
    bus.unsubscribe = AsyncMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def processing_config() -> ProcessingConfig:
    """Create a processing configuration."""
    return ProcessingConfig(
        extract_categories=list(ExtractionCategory),
        min_importance=0.3,
        include_metadata=True,
        preserve_structure=True,
        extract_code_blocks=True,
        extract_links=True,
        extract_images=True,
    )


@pytest.fixture
def watch_config(temp_dir: Path) -> WatchConfig:
    """Create a watch configuration."""
    return WatchConfig(
        paths=[temp_dir],
        patterns=["*.md", "*.txt"],
        ignore_patterns=[".*", "__pycache__", "*.pyc"],
        recursive=True,
        follow_symlinks=False,
        debounce_seconds=0.1,  # Short debounce for tests
    )


@pytest.fixture
def organization_config(temp_dir: Path) -> OrganizationConfig:
    """Create an organization configuration."""
    return OrganizationConfig(
        output_dir=temp_dir / "output",
        group_by_category=True,
        group_by_document=False,
        create_index=True,
        include_metadata=True,
        format="markdown",
    )


@pytest.fixture
def trapper_keeper_config(
    processing_config: ProcessingConfig,
    watch_config: WatchConfig,
    organization_config: OrganizationConfig,
) -> TrapperKeeperConfig:
    """Create a complete Trapper Keeper configuration."""
    return TrapperKeeperConfig(
        processing=processing_config,
        watching=watch_config,
        organization=organization_config,
        enable_metrics=False,  # Disable metrics for tests
        log_level="DEBUG",
        max_concurrent_processing=2,  # Lower for tests
    )


@pytest.fixture
def sample_events() -> List[Event]:
    """Create sample events for testing."""
    return [
        Event(
            type=EventType.FILE_CREATED,
            source="FileMonitor",
            data={"path": "/test/new_file.md"},
        ),
        Event(
            type=EventType.PROCESSING_STARTED,
            source="DocumentProcessor",
            data={"document_id": "test-doc-1"},
        ),
        Event(
            type=EventType.EXTRACTION_COMPLETED,
            source="ContentExtractor",
            data={
                "document_id": "test-doc-1",
                "extracted_count": 3,
            },
        ),
    ]


@pytest.fixture
def mock_component() -> Component:
    """Create a mock component."""
    component = Mock(spec=Component)
    component.name = "MockComponent"
    component.is_initialized = True
    component.is_running = False
    component.initialize = AsyncMock()
    component.start = AsyncMock()
    component.stop = AsyncMock()
    return component


@pytest_asyncio.fixture
async def initialized_event_bus() -> AsyncGenerator[EventBus, None]:
    """Create and initialize a real event bus."""
    bus = EventBus()
    await bus.initialize()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def create_test_files(temp_dir: Path) -> Callable[[List[Tuple[str, str]]], List[Path]]:
    """Factory to create test files."""
    def _create_files(files: List[Tuple[str, str]]) -> List[Path]:
        created = []
        for filename, content in files:
            file_path = temp_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created.append(file_path)
        return created
    return _create_files


@pytest.fixture
def performance_timer():
    """Context manager for timing operations."""
    class Timer:
        def __init__(self):
            self.elapsed = 0.0
            
        def __enter__(self):
            self.start = datetime.now()
            return self
            
        def __exit__(self, *args):
            self.elapsed = (datetime.now() - self.start).total_seconds()
            
    return Timer


# Async fixtures for components
@pytest_asyncio.fixture
async def mock_async_component() -> AsyncGenerator[Component, None]:
    """Create an async mock component."""
    component = AsyncMock(spec=Component)
    component.name = "AsyncMockComponent"
    component.is_initialized = True
    component.is_running = True
    yield component