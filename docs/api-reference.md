# API Reference

This document provides a complete reference for the Trapper Keeper MCP Python API and MCP tools.

## Python API

### Core Classes

#### DocumentOrganizer

The main class for organizing documents.

```python
from trapper_keeper.organizer import DocumentOrganizer

# Initialize organizer
organizer = DocumentOrganizer(config)

# Process a document
result = await organizer.process_document(
    file_path="document.md",
    categories=["🏗️ Architecture", "🔐 Security"],
    min_importance=0.6
)
```

**Methods:**

```python
class DocumentOrganizer:
    async def process_document(
        self,
        file_path: str | Path,
        categories: List[str] | None = None,
        min_importance: float = 0.5,
        dry_run: bool = False
    ) -> ProcessingResult:
        """Process a document and extract content."""
        
    async def process_directory(
        self,
        directory_path: str | Path,
        patterns: List[str] | None = None,
        recursive: bool = True,
        parallel: bool = True
    ) -> List[ProcessingResult]:
        """Process all matching files in a directory."""
        
    def generate_index(
        self,
        results: List[ProcessingResult],
        output_format: str = "markdown"
    ) -> str:
        """Generate an index from processing results."""
```

#### ContentExtractor

Extracts content from parsed documents.

```python
from trapper_keeper.extractor import ContentExtractor

extractor = ContentExtractor(config)

# Extract content
extracted = extractor.extract(
    document,
    categories=["🏗️ Architecture"],
    min_importance=0.5
)
```

**Methods:**

```python
class ContentExtractor:
    def extract(
        self,
        document: Document,
        categories: List[str] | None = None,
        min_importance: float = 0.5
    ) -> List[ExtractedContent]:
        """Extract categorized content from document."""
        
    def extract_code_blocks(
        self,
        document: Document
    ) -> List[CodeBlock]:
        """Extract all code blocks from document."""
        
    def extract_links(
        self,
        document: Document
    ) -> List[Link]:
        """Extract all links from document."""
```

#### CategoryDetector

Detects content categories using various methods.

```python
from trapper_keeper.extractor import CategoryDetector

detector = CategoryDetector(config)

# Detect category
category, confidence = detector.detect_category(
    content="Security configuration for authentication",
    context={"title": "Auth Setup"}
)
```

**Methods:**

```python
class CategoryDetector:
    def detect_category(
        self,
        content: str,
        context: Dict[str, Any] | None = None
    ) -> Tuple[str, float]:
        """Detect category and confidence for content."""
        
    def detect_multiple(
        self,
        content: str,
        context: Dict[str, Any] | None = None,
        threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """Detect multiple possible categories."""
```

#### FileMonitor

Monitors directories for file changes.

```python
from trapper_keeper.monitoring import FileMonitor

monitor = FileMonitor(config)

# Add directory to watch
await monitor.watch_directory(
    path="/path/to/docs",
    patterns=["*.md", "*.txt"],
    callback=process_file
)

# Start monitoring
await monitor.start()
```

**Methods:**

```python
class FileMonitor:
    async def watch_directory(
        self,
        path: str | Path,
        patterns: List[str] | None = None,
        recursive: bool = True,
        callback: Callable = None
    ) -> str:
        """Add directory to watch list."""
        
    async def stop_watching(self, watch_id: str):
        """Stop watching a directory."""
        
    async def start(self):
        """Start monitoring all watched directories."""
        
    async def stop(self):
        """Stop all monitoring."""
```

### Data Types

#### ProcessingResult

Result from processing a document.

```python
@dataclass
class ProcessingResult:
    document_id: str
    file_path: str
    success: bool
    extracted_content: List[ExtractedContent]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    processing_time: float
```

#### ExtractedContent

Extracted content with metadata.

```python
@dataclass
class ExtractedContent:
    content_id: str
    category: str
    title: str
    content: str
    importance: float
    metadata: Dict[str, Any]
    source_location: SourceLocation
```

#### Document

Parsed document structure.

```python
@dataclass
class Document:
    document_id: str
    title: str
    sections: List[Section]
    metadata: Dict[str, Any]
    raw_content: str
```

## MCP Tools API

### organize_documentation

Main tool for organizing documentation files.

**Request:**
```json
{
  "file_path": "/path/to/CLAUDE.md",
  "dry_run": false,
  "output_dir": "./organized",
  "categories": ["🏗️ Architecture", "🔐 Security"],
  "min_importance": 0.6,
  "create_references": true
}
```

**Response:**
```json
{
  "success": true,
  "document_id": "doc_123",
  "suggestions": [
    {
      "section_id": "sec_456",
      "title": "System Architecture",
      "category": "🏗️ Architecture",
      "importance": 0.85,
      "reason": "Contains architecture keywords and diagrams",
      "content_preview": "The system uses a microservices..."
    }
  ],
  "extracted_count": 5,
  "categories_found": ["🏗️ Architecture", "🔐 Security"],
  "output_files": [
    "./organized/architecture.md",
    "./organized/security.md"
  ],
  "errors": [],
  "warnings": [],
  "processing_time": 1.23,
  "dry_run": false
}
```

### extract_content

Extract specific content from files.

**Request:**
```json
{
  "file_paths": ["/path/to/doc1.md", "/path/to/doc2.md"],
  "categories": ["🔐 Security"],
  "include_code_blocks": true,
  "include_links": true,
  "min_importance": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "extracted": [
    {
      "file_path": "/path/to/doc1.md",
      "content": [
        {
          "category": "🔐 Security",
          "title": "Authentication Setup",
          "content": "Configure OAuth2...",
          "importance": 0.9,
          "line_start": 45,
          "line_end": 67
        }
      ],
      "code_blocks": [
        {
          "language": "python",
          "content": "def authenticate(user):",
          "line_number": 50
        }
      ],
      "links": [
        {
          "text": "OAuth2 Spec",
          "url": "https://oauth.net/2/",
          "line_number": 52
        }
      ]
    }
  ],
  "total_extracted": 15,
  "processing_time": 0.45
}
```

### validate_structure

Validate document structure and content.

**Request:**
```json
{
  "file_path": "/path/to/document.md",
  "checks": [
    "structure",
    "categories",
    "links",
    "code_blocks"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "checks": {
    "structure": {
      "valid": true,
      "issues": []
    },
    "categories": {
      "valid": true,
      "found": ["🏗️ Architecture", "🔐 Security"],
      "missing_content": []
    },
    "links": {
      "valid": false,
      "broken": ["https://example.com/404"],
      "total": 12
    },
    "code_blocks": {
      "valid": true,
      "languages": ["python", "bash"],
      "syntax_errors": []
    }
  },
  "recommendations": [
    "Fix broken link on line 123",
    "Add content for '🧪 Testing' category"
  ]
}
```

### analyze_content

Analyze documentation content and provide insights.

**Request:**
```json
{
  "file_paths": ["/path/to/docs"],
  "recursive": true,
  "metrics": [
    "complexity",
    "coverage",
    "quality",
    "trends"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "total_files": 24,
    "total_sections": 156,
    "complexity": {
      "score": 7.2,
      "details": {
        "avg_section_length": 245,
        "max_nesting_level": 4,
        "readability_score": 72
      }
    },
    "coverage": {
      "categories": {
        "🏗️ Architecture": 0.85,
        "🔐 Security": 0.92,
        "🧪 Testing": 0.45
      },
      "missing_topics": [
        "Error handling",
        "Performance optimization"
      ]
    },
    "quality": {
      "score": 8.1,
      "issues": [
        "5 sections missing descriptions",
        "3 code blocks without language tags"
      ]
    },
    "trends": {
      "growth_rate": 0.15,
      "most_updated": "🔐 Security",
      "stale_sections": 8
    }
  },
  "recommendations": [
    "Improve testing documentation coverage",
    "Add descriptions to incomplete sections",
    "Update stale security sections"
  ]
}
```

### generate_references

Generate reference links for extracted content.

**Request:**
```json
{
  "source_file": "/path/to/CLAUDE.md",
  "extracted_dir": "./organized",
  "reference_style": "inline",
  "update_source": true
}
```

**Response:**
```json
{
  "success": true,
  "references_created": 12,
  "reference_map": {
    "architecture": {
      "file": "./organized/architecture.md",
      "sections": [
        {
          "title": "System Design",
          "anchor": "#system-design",
          "line": 45
        }
      ]
    }
  },
  "source_updated": true,
  "backup_created": "/path/to/CLAUDE.md.bak"
}
```

## Event System

### Event Types

```python
from trapper_keeper.core.events import EventType

# Available events
EventType.FILE_CREATED
EventType.FILE_MODIFIED
EventType.FILE_DELETED
EventType.PROCESSING_STARTED
EventType.PROCESSING_COMPLETED
EventType.PROCESSING_FAILED
EventType.EXTRACTION_COMPLETED
EventType.CATEGORY_DETECTED
```

### Event Subscription

```python
from trapper_keeper.core.events import EventBus

bus = EventBus()

# Subscribe to events
@bus.subscribe(EventType.FILE_MODIFIED)
async def handle_file_modified(event):
    print(f"File modified: {event.data['file_path']}")

# Publish events
await bus.publish(EventType.FILE_MODIFIED, {
    "file_path": "/path/to/file.md",
    "timestamp": datetime.now()
})
```

## Error Handling

### Exception Types

```python
from trapper_keeper.core.exceptions import (
    TrapperKeeperError,
    ConfigurationError,
    ParsingError,
    ExtractionError,
    ValidationError
)

try:
    result = await organizer.process_document("file.md")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except ParsingError as e:
    print(f"Failed to parse document: {e}")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except TrapperKeeperError as e:
    print(f"General error: {e}")
```

## Async Context Managers

```python
from trapper_keeper import TrapperKeeper

# Using context manager
async with TrapperKeeper(config) as tk:
    # Process documents
    results = await tk.process_directory("./docs")
    
    # Monitor changes
    await tk.watch_directory("./docs")
    
    # Wait for events
    await tk.wait_for_idle()
```

## Plugins

### Creating a Plugin

```python
from trapper_keeper.core.plugin import Plugin

class CustomPlugin(Plugin):
    """Custom plugin for Trapper Keeper."""
    
    name = "custom-plugin"
    version = "1.0.0"
    
    async def initialize(self, config):
        """Initialize plugin with configuration."""
        self.config = config
    
    async def process(self, document):
        """Process a document."""
        # Custom processing logic
        return document
    
    async def cleanup(self):
        """Cleanup plugin resources."""
        pass
```

### Registering Plugins

```python
from trapper_keeper import TrapperKeeper

tk = TrapperKeeper(config)
tk.register_plugin(CustomPlugin())
```

## Next Steps

- [MCP Tools Reference](./mcp-tools.md) - Detailed MCP tools documentation
- [Python Examples](../examples/scripts/) - Example Python scripts
- [Plugin Development](./development/plugin-development.md) - Create custom plugins