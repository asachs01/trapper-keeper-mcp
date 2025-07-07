"""Performance benchmark tests."""

import asyncio
import time
import psutil
import statistics
from pathlib import Path
from typing import List, Dict, Any
import pytest
import pytest_asyncio
import pytest_benchmark

from trapper_keeper.parser.markdown_parser import MarkdownParser
from trapper_keeper.extractor.content_extractor import ContentExtractor
from trapper_keeper.monitoring.file_monitor import FileMonitor
from trapper_keeper.core.types import (
    ProcessingConfig,
    WatchConfig,
    Document,
    DocumentType,
)


class TestParsingPerformance:
    """Benchmark parsing performance."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return MarkdownParser()
    
    @pytest.fixture
    def small_document(self):
        """Small document (1KB)."""
        return "# Title\n\n" + "This is a paragraph. " * 50
    
    @pytest.fixture
    def medium_document(self):
        """Medium document (10KB)."""
        sections = []
        for i in range(20):
            sections.append(f"## Section {i}\n\n" + "Content paragraph. " * 50)
        return "# Main Title\n\n" + "\n\n".join(sections)
    
    @pytest.fixture
    def large_document(self):
        """Large document (100KB)."""
        sections = []
        for i in range(100):
            sections.append(f"## Section {i}\n\n" + "Content paragraph. " * 100)
        return "# Main Title\n\n" + "\n\n".join(sections)
    
    @pytest.fixture
    def complex_document(self):
        """Complex document with various elements."""
        return """# Complex Document

## Table of Contents
- [Introduction](#introduction)
- [Architecture](#architecture)
- [Implementation](#implementation)

## Introduction

This document contains **bold**, *italic*, and `inline code`.

### Subsection with Lists

1. Ordered item 1
2. Ordered item 2
   - Nested unordered
   - Another nested

## Architecture

```python
class Example:
    def __init__(self):
        self.value = 42
```

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |

## Implementation

> Blockquote with important information
> spanning multiple lines

[Link to resource](https://example.com)
![Image description](image.png)

---

### Code Examples

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255)
);
```

```javascript
function processData(data) {
    return data.map(item => item.value * 2);
}
```
""" * 10  # Repeat to make it larger
    
    @pytest.mark.asyncio
    async def test_parse_small_document(self, benchmark, parser):
        """Benchmark parsing small documents."""
        await parser.initialize()
        
        async def parse():
            return await parser.parse(self.small_document)
        
        result = benchmark(asyncio.run, parse())
        assert result is not None
        assert isinstance(result, Document)
    
    @pytest.mark.asyncio
    async def test_parse_medium_document(self, benchmark, parser, medium_document):
        """Benchmark parsing medium documents."""
        await parser.initialize()
        
        async def parse():
            return await parser.parse(medium_document)
        
        result = benchmark(asyncio.run, parse())
        assert result is not None
        assert len(result.sections) > 10
    
    @pytest.mark.asyncio
    async def test_parse_large_document(self, benchmark, parser, large_document):
        """Benchmark parsing large documents."""
        await parser.initialize()
        
        async def parse():
            return await parser.parse(large_document)
        
        result = benchmark(asyncio.run, parse())
        assert result is not None
        assert len(result.sections) > 50
    
    @pytest.mark.asyncio
    async def test_parse_complex_document(self, benchmark, parser, complex_document):
        """Benchmark parsing complex documents with various elements."""
        await parser.initialize()
        
        async def parse():
            return await parser.parse(complex_document)
        
        result = benchmark(asyncio.run, parse())
        assert result is not None
        # Complex document should have code blocks, tables, etc.
        assert "```" in result.content
        assert "|" in result.content
    
    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, parser, medium_document):
        """Benchmark concurrent document parsing."""
        await parser.initialize()
        
        num_documents = 20
        documents = [medium_document for _ in range(num_documents)]
        
        start_time = time.time()
        
        # Parse concurrently
        tasks = [parser.parse(doc) for doc in documents]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert len(results) == num_documents
        assert all(isinstance(r, Document) for r in results)
        
        # Should benefit from concurrency
        avg_time_per_doc = total_time / num_documents
        assert avg_time_per_doc < 0.1  # Should parse each in under 100ms


class TestExtractionPerformance:
    """Benchmark content extraction performance."""
    
    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        config = ProcessingConfig()
        return ContentExtractor(config)
    
    @pytest.fixture
    def document_with_many_sections(self):
        """Document with many sections to extract."""
        sections = []
        categories = ["Architecture", "Database", "Security", "API", "Testing"]
        
        for i in range(50):
            category = categories[i % len(categories)]
            sections.append(f"""## {category} Section {i}

This section contains important {category.lower()} information.
Key points about {category.lower()}:
- Point 1 about {category.lower()}
- Point 2 about {category.lower()}
- Critical: {category.lower()} consideration
""")
        
        content = "# Large Document\n\n" + "\n\n".join(sections)
        
        return Document(
            id="perf-doc",
            type=DocumentType.MARKDOWN,
            content=content,
        )
    
    @pytest.mark.asyncio
    async def test_extract_performance(self, benchmark, extractor, document_with_many_sections):
        """Benchmark content extraction."""
        await extractor.initialize()
        
        async def extract():
            return await extractor.extract(document_with_many_sections)
        
        results = benchmark(asyncio.run, extract())
        
        assert len(results) > 0
        # Should extract from multiple sections
        assert len(results) >= 20
    
    @pytest.mark.asyncio
    async def test_extraction_with_filtering(self, extractor, document_with_many_sections):
        """Benchmark extraction with importance filtering."""
        await extractor.initialize()
        
        # High importance threshold
        extractor._config.min_importance = 0.8
        
        start_time = time.time()
        high_importance = await extractor.extract(document_with_many_sections)
        high_time = time.time() - start_time
        
        # Low importance threshold
        extractor._config.min_importance = 0.1
        
        start_time = time.time()
        low_importance = await extractor.extract(document_with_many_sections)
        low_time = time.time() - start_time
        
        # High threshold should be faster (less results)
        assert len(high_importance) < len(low_importance)
        assert high_time <= low_time * 1.5  # Should not be much slower
    
    @pytest.mark.asyncio
    async def test_category_detection_performance(self, extractor):
        """Benchmark category detection speed."""
        await extractor.initialize()
        
        test_texts = [
            "Database schema design for user tables",
            "API endpoint for authentication",
            "Security vulnerability in input validation",
            "Performance optimization for queries",
            "Testing strategy for integration tests",
        ] * 100  # 500 texts to categorize
        
        start_time = time.time()
        
        for text in test_texts:
            category = extractor._detect_category(text)
            assert category is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should categorize quickly
        avg_time = total_time / len(test_texts)
        assert avg_time < 0.001  # Less than 1ms per text


class TestFileMonitoringPerformance:
    """Benchmark file monitoring performance."""
    
    @pytest_asyncio.fixture
    async def monitor(self, temp_dir):
        """Create a file monitor."""
        config = WatchConfig(
            paths=[temp_dir],
            patterns=["*.md"],
            recursive=True,
            debounce_seconds=0.1,
        )
        monitor = FileMonitor(config)
        await monitor.initialize()
        yield monitor
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_monitor_many_files(self, monitor, temp_dir):
        """Benchmark monitoring many files."""
        # Create many files
        num_files = 100
        for i in range(num_files):
            file_path = temp_dir / f"file_{i}.md"
            file_path.write_text(f"# File {i}\n\nContent")
        
        # Start monitoring
        await monitor.start()
        
        # Track events
        events_received = []
        
        async def event_handler(event):
            events_received.append(event)
        
        monitor.on_file_changed = event_handler
        
        # Modify multiple files
        start_time = time.time()
        
        for i in range(10):
            file_path = temp_dir / f"file_{i}.md"
            file_path.write_text(f"# Modified File {i}\n\nNew content")
        
        # Wait for debounce
        await asyncio.sleep(0.3)
        
        end_time = time.time()
        
        # Should handle multiple file changes efficiently
        assert len(events_received) >= 10
        assert (end_time - start_time) < 1.0  # Should process quickly
    
    @pytest.mark.asyncio
    async def test_recursive_monitoring_performance(self, monitor, temp_dir):
        """Benchmark recursive directory monitoring."""
        # Create nested directory structure
        for i in range(5):
            for j in range(5):
                dir_path = temp_dir / f"level1_{i}" / f"level2_{j}"
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create files in each directory
                for k in range(5):
                    file_path = dir_path / f"file_{k}.md"
                    file_path.write_text(f"# File {i}-{j}-{k}")
        
        # Total: 5 * 5 * 5 = 125 files
        
        # Start monitoring
        start_time = time.time()
        await monitor.start()
        setup_time = time.time() - start_time
        
        # Should start quickly even with many files
        assert setup_time < 1.0
        
        # Get metrics
        metrics = monitor.get_metrics()
        assert metrics["files_monitored"] >= 125


class TestMemoryUsage:
    """Test memory usage under load."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_large_files(self, temp_dir):
        """Test memory usage when processing large files."""
        process = psutil.Process()
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large document (10MB)
        large_content = "# Large Document\n\n" + ("x" * 1024 * 1024 * 10)
        
        parser = MarkdownParser()
        await parser.initialize()
        
        # Parse large document
        doc = await parser.parse(large_content)
        
        # Extract content
        extractor = ContentExtractor(ProcessingConfig())
        await extractor.initialize()
        
        extracted = await extractor.extract(doc)
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase
        
        # Cleanup
        del large_content
        del doc
        del extracted
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        process = psutil.Process()
        parser = MarkdownParser()
        await parser.initialize()
        
        memory_readings = []
        
        # Perform many iterations
        for i in range(100):
            # Create and parse document
            content = f"# Document {i}\n\n" + "Content " * 100
            doc = await parser.parse(content)
            
            # Record memory every 10 iterations
            if i % 10 == 0:
                memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_readings.append(memory)
        
        # Check for memory leak
        # Memory should stabilize, not continuously increase
        first_half_avg = statistics.mean(memory_readings[:5])
        second_half_avg = statistics.mean(memory_readings[5:])
        
        # Allow some increase but not linear growth
        assert second_half_avg < first_half_avg * 1.5


class TestScalabilityBenchmarks:
    """Test scalability with increasing load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_scalability(self):
        """Test how performance scales with concurrent operations."""
        parser = MarkdownParser()
        await parser.initialize()
        
        content = "# Document\n\n" + "Content paragraph. " * 100
        
        results = {}
        
        for num_concurrent in [1, 5, 10, 20, 50]:
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = [parser.parse(content) for _ in range(num_concurrent)]
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            results[num_concurrent] = {
                "total_time": total_time,
                "avg_time": total_time / num_concurrent,
            }
        
        # Verify scalability
        # Time should not increase linearly with concurrency
        assert results[50]["total_time"] < results[1]["total_time"] * 50
        
        # Average time per document should decrease with concurrency
        assert results[50]["avg_time"] < results[1]["avg_time"]
    
    @pytest.mark.asyncio
    async def test_throughput_measurement(self, temp_dir):
        """Measure document processing throughput."""
        from trapper_keeper.core.orchestrator import TrapperKeeperOrchestrator
        from trapper_keeper.core.types import TrapperKeeperConfig
        
        config = TrapperKeeperConfig(
            processing=ProcessingConfig(),
            watching=WatchConfig(paths=[temp_dir]),
            organization={"output_dir": temp_dir / "output"},
            max_concurrent_processing=10,
        )
        
        orchestrator = TrapperKeeperOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start()
        
        # Create test documents
        num_docs = 100
        for i in range(num_docs):
            doc_path = temp_dir / f"doc_{i}.md"
            doc_path.write_text(f"# Document {i}\n\nContent for document {i}")
        
        # Measure throughput
        start_time = time.time()
        
        tasks = []
        for i in range(num_docs):
            task = orchestrator.process_file(temp_dir / f"doc_{i}.md")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = num_docs / total_time  # documents per second
        
        await orchestrator.stop()
        
        # Should process at reasonable throughput
        assert throughput > 10  # At least 10 docs/second
        assert all(r.success for r in results)