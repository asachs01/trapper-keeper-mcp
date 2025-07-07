"""Test utilities and helper functions."""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import random
import string

from trapper_keeper.core.types import (
    Document,
    DocumentType,
    DocumentSection,
    ExtractedContent,
    ExtractionCategory,
    ProcessingResult,
)


class DocumentFactory:
    """Factory for creating test documents."""
    
    @staticmethod
    def create_simple_document(
        title: str = "Test Document",
        content: str = "Test content",
        doc_id: Optional[str] = None,
    ) -> Document:
        """Create a simple test document."""
        if not doc_id:
            doc_id = f"doc-{random.randint(1000, 9999)}"
        
        return Document(
            id=doc_id,
            type=DocumentType.MARKDOWN,
            content=f"# {title}\n\n{content}",
        )
    
    @staticmethod
    def create_document_with_sections(
        title: str = "Multi-Section Document",
        sections: Optional[List[Tuple[str, str]]] = None,
    ) -> Document:
        """Create a document with multiple sections."""
        if not sections:
            sections = [
                ("Introduction", "This is the introduction."),
                ("Main Content", "This is the main content."),
                ("Conclusion", "This is the conclusion."),
            ]
        
        content_parts = [f"# {title}"]
        doc_sections = []
        
        for i, (section_title, section_content) in enumerate(sections):
            content_parts.append(f"\n## {section_title}\n\n{section_content}")
            doc_sections.append(
                DocumentSection(
                    id=f"sec-{i}",
                    title=section_title,
                    content=section_content,
                    level=2,
                )
            )
        
        return Document(
            id=f"doc-{random.randint(1000, 9999)}",
            type=DocumentType.MARKDOWN,
            content="\n".join(content_parts),
            sections=doc_sections,
        )
    
    @staticmethod
    def create_complex_document() -> Document:
        """Create a complex document with various elements."""
        content = """# Complex Document

## Overview

This document contains various markdown elements for testing.

### Lists

**Unordered:**
- Item 1
- Item 2
  - Nested item
- Item 3

**Ordered:**
1. First
2. Second
3. Third

## Code Examples

```python
def hello_world():
    print("Hello, World!")
```

```javascript
const greet = (name) => {
    console.log(`Hello, ${name}!`);
};
```

## Tables

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

## Links and Images

[External Link](https://example.com)
[Internal Link](other-doc.md)

![Image Alt Text](image.png)

## Blockquotes

> This is a blockquote
> with multiple lines

## Security Notes

**CRITICAL**: Fix SQL injection vulnerability in user input!

## Architecture

The system follows microservices architecture with:
- API Gateway
- Service Discovery
- Message Queue
"""
        
        return Document(
            id="complex-doc",
            type=DocumentType.MARKDOWN,
            content=content,
        )


class ContentFactory:
    """Factory for creating test extracted content."""
    
    @staticmethod
    def create_extracted_content(
        category: ExtractionCategory = ExtractionCategory.CUSTOM,
        title: str = "Test Extract",
        content: str = "Extracted content",
        importance: float = 0.5,
        document_id: str = "test-doc",
    ) -> ExtractedContent:
        """Create test extracted content."""
        return ExtractedContent(
            id=f"extract-{random.randint(1000, 9999)}",
            document_id=document_id,
            category=category,
            title=title,
            content=content,
            importance=importance,
        )
    
    @staticmethod
    def create_content_set(
        document_id: str = "test-doc",
        count: int = 5,
    ) -> List[ExtractedContent]:
        """Create a set of diverse extracted content."""
        categories = list(ExtractionCategory)
        content_items = []
        
        for i in range(count):
            category = categories[i % len(categories)]
            content_items.append(
                ExtractedContent(
                    id=f"extract-{i}",
                    document_id=document_id,
                    category=category,
                    title=f"{category.value} Content {i}",
                    content=f"This is {category.value} related content.",
                    importance=random.uniform(0.3, 1.0),
                )
            )
        
        return content_items


class FileSystemHelper:
    """Helper for file system operations in tests."""
    
    @staticmethod
    def create_test_structure(
        base_dir: Path,
        structure: Dict[str, Any],
    ) -> List[Path]:
        """Create a directory structure for testing.
        
        Example structure:
        {
            "docs": {
                "api.md": "# API Docs",
                "guides": {
                    "setup.md": "# Setup Guide",
                    "usage.md": "# Usage Guide",
                }
            },
            "README.md": "# Project Readme"
        }
        """
        created_files = []
        
        def create_items(parent: Path, items: Dict[str, Any]):
            for name, content in items.items():
                path = parent / name
                
                if isinstance(content, dict):
                    # Directory
                    path.mkdir(parents=True, exist_ok=True)
                    create_items(path, content)
                else:
                    # File
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content)
                    created_files.append(path)
        
        create_items(base_dir, structure)
        return created_files
    
    @staticmethod
    def generate_markdown_files(
        base_dir: Path,
        count: int = 10,
        categories: Optional[List[str]] = None,
    ) -> List[Path]:
        """Generate multiple markdown files for testing."""
        if not categories:
            categories = ["Architecture", "API", "Database", "Security", "Testing"]
        
        files = []
        for i in range(count):
            category = categories[i % len(categories)]
            filename = f"{category.lower()}_{i}.md"
            content = f"""# {category} Document {i}

## Overview

This is a test document about {category}.

## Details

Key points about {category}:
- Point 1
- Point 2
- Point 3

## Code Example

```python
# {category} related code
def {category.lower()}_function():
    pass
```
"""
            
            file_path = base_dir / filename
            file_path.write_text(content)
            files.append(file_path)
        
        return files


class AsyncTestHelper:
    """Helper for async testing."""
    
    @staticmethod
    async def wait_for_condition(
        condition_func,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    async def run_with_timeout(
        coro,
        timeout: float = 5.0,
    ):
        """Run a coroutine with a timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(f"Operation timed out after {timeout} seconds")


class MetricsCollector:
    """Helper for collecting and analyzing metrics during tests."""
    
    def __init__(self):
        self.metrics = {
            "timings": [],
            "memory": [],
            "events": [],
        }
    
    def record_timing(self, operation: str, duration: float):
        """Record operation timing."""
        self.metrics["timings"].append({
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now(),
        })
    
    def record_memory(self, usage_mb: float):
        """Record memory usage."""
        self.metrics["memory"].append({
            "usage_mb": usage_mb,
            "timestamp": datetime.now(),
        })
    
    def record_event(self, event_type: str, data: Dict[str, Any]):
        """Record an event."""
        self.metrics["events"].append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(),
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not self.metrics["timings"]:
            avg_timing = 0
        else:
            avg_timing = sum(t["duration"] for t in self.metrics["timings"]) / len(self.metrics["timings"])
        
        if not self.metrics["memory"]:
            max_memory = 0
        else:
            max_memory = max(m["usage_mb"] for m in self.metrics["memory"])
        
        return {
            "total_events": len(self.metrics["events"]),
            "average_timing": avg_timing,
            "max_memory_mb": max_memory,
            "event_types": list(set(e["type"] for e in self.metrics["events"])),
        }


class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate a random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_markdown_content(
        paragraphs: int = 3,
        include_code: bool = True,
        include_lists: bool = True,
    ) -> str:
        """Generate random markdown content."""
        content_parts = []
        
        # Title
        content_parts.append(f"# {MockDataGenerator.random_string(20)}")
        
        # Paragraphs
        for i in range(paragraphs):
            content_parts.append(f"\n## Section {i+1}\n")
            content_parts.append(f"{MockDataGenerator.random_string(100)}.")
            
            if include_lists and i == 0:
                content_parts.append("\n- " + MockDataGenerator.random_string(20))
                content_parts.append("- " + MockDataGenerator.random_string(20))
                content_parts.append("- " + MockDataGenerator.random_string(20))
            
            if include_code and i == 1:
                content_parts.append("\n```python")
                content_parts.append(f"def {MockDataGenerator.random_string(10)}():")
                content_parts.append(f"    return '{MockDataGenerator.random_string(15)}'")
                content_parts.append("```")
        
        return "\n".join(content_parts)
    
    @staticmethod
    def generate_processing_result(
        document_id: str,
        success: bool = True,
        num_extracts: int = 5,
    ) -> ProcessingResult:
        """Generate a mock processing result."""
        extracted_contents = []
        
        if success:
            extracted_contents = ContentFactory.create_content_set(
                document_id=document_id,
                count=num_extracts,
            )
        
        return ProcessingResult(
            document_id=document_id,
            success=success,
            extracted_contents=extracted_contents,
            errors=[] if success else ["Processing failed"],
            processing_time=random.uniform(0.1, 2.0),
        )


def assert_valid_document(doc: Document):
    """Assert that a document is valid."""
    assert doc is not None
    assert doc.id
    assert doc.type in DocumentType
    assert isinstance(doc.content, str)
    assert len(doc.content) > 0


def assert_valid_extracted_content(content: ExtractedContent):
    """Assert that extracted content is valid."""
    assert content is not None
    assert content.id
    assert content.document_id
    assert content.category
    assert content.title
    assert content.content
    assert 0.0 <= content.importance <= 1.0


def assert_valid_processing_result(result: ProcessingResult):
    """Assert that a processing result is valid."""
    assert result is not None
    assert result.document_id
    assert isinstance(result.success, bool)
    assert isinstance(result.extracted_contents, list)
    assert isinstance(result.errors, list)
    
    if result.success:
        assert len(result.errors) == 0
    else:
        assert len(result.errors) > 0