# Architecture Overview

## System Architecture

Trapper Keeper MCP is built with a modular, event-driven architecture that supports both CLI and MCP server modes. The system is designed for extensibility, performance, and reliability.

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Interface                          │
├─────────────────┬───────────────────┬──────────────────────────┤
│       CLI       │    MCP Server     │      API Wrapper         │
├─────────────────┴───────────────────┴──────────────────────────┤
│                      Core Application Layer                      │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│   Document   │   Content    │  Category    │    Reference     │
│  Organizer   │  Extractor   │  Detector    │   Generator      │
├──────────────┴──────────────┴──────────────┴──────────────────┤
│                    Infrastructure Layer                          │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│    File      │   Parser     │    Event     │   Metrics        │
│  Monitor     │   Factory    │     Bus      │  Collector       │
├──────────────┴──────────────┴──────────────┴──────────────────┤
│                      Storage Layer                               │
├──────────────┬──────────────┬──────────────┬──────────────────┤
│   Config     │    Cache     │   Output     │    Logs          │
│   Store      │   Manager    │   Writer     │   Handler        │
└──────────────┴──────────────┴──────────────┴──────────────────┘
```

## Design Principles

### 1. Modularity

Each component is self-contained with clear interfaces:

```python
# Example: Parser interface
class Parser(Protocol):
    """Protocol for document parsers."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle file."""
        ...
    
    def parse(self, file_path: Path) -> Document:
        """Parse document into structured format."""
        ...
```

### 2. Event-Driven Architecture

Components communicate through events:

```python
# Event publishing
await event_bus.publish(EventType.FILE_MODIFIED, {
    "file_path": str(file_path),
    "timestamp": datetime.now()
})

# Event subscription
@event_bus.subscribe(EventType.FILE_MODIFIED)
async def handle_file_change(event: Event):
    await process_file(event.data["file_path"])
```

### 3. Async-First Design

All I/O operations are asynchronous:

```python
async def process_document(file_path: Path) -> ProcessingResult:
    """Process document asynchronously."""
    async with aiofiles.open(file_path) as f:
        content = await f.read()
    
    # Parallel processing
    tasks = [
        extract_content(content),
        detect_categories(content),
        analyze_structure(content)
    ]
    
    results = await asyncio.gather(*tasks)
    return ProcessingResult(*results)
```

### 4. Plugin Architecture

Extensible through plugins:

```python
class PluginManager:
    """Manages plugin lifecycle."""
    
    def register_plugin(self, plugin: Plugin):
        """Register a plugin."""
        self.plugins[plugin.name] = plugin
        plugin.initialize(self.config)
    
    async def execute_hook(self, hook_name: str, *args, **kwargs):
        """Execute plugin hooks."""
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                await getattr(plugin, hook_name)(*args, **kwargs)
```

## Component Architecture

### Core Components

#### Document Organizer

The central orchestrator that coordinates all processing:

```python
class DocumentOrganizer:
    def __init__(self, config: Config):
        self.parser_factory = ParserFactory()
        self.extractor = ContentExtractor(config)
        self.detector = CategoryDetector(config)
        self.reference_generator = ReferenceGenerator()
        
    async def process_document(
        self,
        file_path: Path,
        options: ProcessingOptions
    ) -> ProcessingResult:
        # Parse document
        parser = self.parser_factory.get_parser(file_path)
        document = parser.parse(file_path)
        
        # Extract content
        extracted = self.extractor.extract(document, options)
        
        # Detect categories
        for content in extracted:
            content.category = self.detector.detect(content)
        
        # Generate references
        if options.create_references:
            references = self.reference_generator.generate(extracted)
        
        return ProcessingResult(extracted, references)
```

#### Content Extractor

Extracts meaningful content from documents:

```python
class ContentExtractor:
    def extract(
        self,
        document: Document,
        options: ExtractionOptions
    ) -> List[ExtractedContent]:
        extracted = []
        
        for section in document.sections:
            # Calculate importance
            importance = self.calculate_importance(section)
            
            if importance >= options.min_importance:
                # Extract content
                content = ExtractedContent(
                    section_id=section.id,
                    title=section.title,
                    content=section.content,
                    importance=importance
                )
                extracted.append(content)
        
        return extracted
```

#### Category Detector

Intelligent category detection:

```python
class CategoryDetector:
    def detect(self, content: ExtractedContent) -> Tuple[str, float]:
        scores = {}
        
        # Keyword matching
        for category, keywords in self.keywords.items():
            score = self.keyword_score(content.content, keywords)
            scores[category] = score
        
        # Pattern matching
        for category, patterns in self.patterns.items():
            score = self.pattern_score(content.content, patterns)
            scores[category] = max(scores.get(category, 0), score)
        
        # Apply importance boosts
        for category, boost in self.importance_boosts.items():
            if category in scores:
                scores[category] *= (1 + boost)
        
        # Return best match
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            return best_category[0], best_category[1]
        
        return "📚 Documentation", 0.5  # Default
```

### Infrastructure Components

#### File Monitor

Watches for file system changes:

```python
class FileMonitor:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.observer = Observer()
        self.watchers = {}
    
    async def watch_directory(
        self,
        path: Path,
        patterns: List[str],
        recursive: bool = True
    ) -> str:
        # Create event handler
        handler = FileEventHandler(
            patterns=patterns,
            event_bus=self.event_bus
        )
        
        # Start watching
        watch = self.observer.schedule(
            handler,
            str(path),
            recursive=recursive
        )
        
        watch_id = str(uuid.uuid4())
        self.watchers[watch_id] = watch
        
        return watch_id
```

#### Event Bus

Central event distribution:

```python
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.metrics = EventMetrics()
    
    async def publish(self, event_type: EventType, data: Dict[str, Any]):
        """Publish event to all subscribers."""
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now()
        )
        
        # Update metrics
        self.metrics.record_event(event_type)
        
        # Notify subscribers
        for handler in self.subscribers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error: {e}")
    
    def subscribe(self, event_type: EventType):
        """Decorator to subscribe to events."""
        def decorator(func):
            self.subscribers[event_type].append(func)
            return func
        return decorator
```

## Data Flow

### Processing Pipeline

```
1. Input Document
   ↓
2. Parser Selection (ParserFactory)
   ↓
3. Document Parsing (Parser)
   ↓
4. Content Extraction (ContentExtractor)
   ↓
5. Category Detection (CategoryDetector)
   ↓
6. Importance Scoring (ImportanceCalculator)
   ↓
7. Output Generation (OutputWriter)
   ↓
8. Reference Creation (ReferenceGenerator)
   ↓
9. Final Output
```

### Event Flow

```
File Change Event
   ↓
File Monitor → Event Bus
                   ↓
              ┌────┴────┬──────┬───────┐
              ↓         ↓      ↓       ↓
         Processor  Logger  Metrics  Cache
              ↓         ↓      ↓       ↓
              └────┬────┴──────┴───────┘
                   ↓
            Result Event → Event Bus
                              ↓
                         Subscribers
```

## Scalability Considerations

### Horizontal Scaling

The architecture supports horizontal scaling through:

1. **Stateless Processing**: Each document is processed independently
2. **Event Distribution**: Events can be distributed across multiple instances
3. **Cache Sharing**: Redis or similar for shared caching
4. **Load Balancing**: Multiple MCP server instances behind a load balancer

### Vertical Scaling

Performance optimization through:

1. **Async Processing**: Non-blocking I/O operations
2. **Connection Pooling**: Reuse connections for external services
3. **Memory Management**: Streaming for large files
4. **Worker Pools**: Configurable number of processing workers

### Performance Patterns

```python
class PerformanceOptimizer:
    def __init__(self, config: Config):
        self.executor = ProcessPoolExecutor(
            max_workers=config.max_workers
        )
        self.cache = LRUCache(maxsize=config.cache_size)
        self.semaphore = asyncio.Semaphore(
            config.max_concurrent
        )
    
    async def process_batch(self, files: List[Path]):
        """Process files with rate limiting."""
        tasks = []
        
        for file in files:
            # Check cache
            if cached := self.cache.get(file):
                continue
            
            # Rate limit
            async with self.semaphore:
                task = self.process_file(file)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Update cache
        for file, result in zip(files, results):
            self.cache[file] = result
        
        return results
```

## Security Architecture

### Security Layers

1. **Input Validation**: All inputs sanitized and validated
2. **Path Traversal Protection**: Restricted to allowed directories
3. **Rate Limiting**: Prevent resource exhaustion
4. **Authentication**: MCP server authentication support
5. **Audit Logging**: All operations logged for compliance

### Security Implementation

```python
class SecurityManager:
    def validate_path(self, path: Path) -> bool:
        """Validate path is within allowed directories."""
        resolved = path.resolve()
        
        for allowed in self.allowed_paths:
            if resolved.is_relative_to(allowed):
                return True
        
        return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations."""
        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")
        
        # Remove special characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Limit length
        return filename[:255]
```

## Deployment Architecture

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ /app/src/
COPY config.yaml /app/

# Configure environment
ENV PYTHONPATH=/app/src
ENV TRAPPER_KEEPER_CONFIG=/app/config.yaml

# Run server
CMD ["python", "-m", "trapper_keeper.mcp.server"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trapper-keeper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trapper-keeper
  template:
    metadata:
      labels:
        app: trapper-keeper
    spec:
      containers:
      - name: trapper-keeper
        image: trapper-keeper:latest
        ports:
        - containerPort: 3000
        env:
        - name: TRAPPER_KEEPER_MAX_CONCURRENT
          value: "20"
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
          requests:
            memory: "512Mi"
            cpu: "500m"
```

## Monitoring Architecture

### Metrics Collection

```python
class MetricsCollector:
    def __init__(self):
        self.files_processed = Counter(
            'trapper_keeper_files_processed_total',
            'Total files processed',
            ['status']
        )
        
        self.processing_duration = Histogram(
            'trapper_keeper_processing_duration_seconds',
            'Processing duration in seconds',
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.active_watchers = Gauge(
            'trapper_keeper_active_watchers',
            'Number of active file watchers'
        )
    
    def record_processing(self, duration: float, status: str):
        self.files_processed.labels(status=status).inc()
        self.processing_duration.observe(duration)
```

### Health Checks

```python
class HealthChecker:
    async def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        checks = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Check file system
        checks['checks']['filesystem'] = await self.check_filesystem()
        
        # Check memory
        checks['checks']['memory'] = self.check_memory()
        
        # Check processing queue
        checks['checks']['queue'] = await self.check_queue()
        
        # Overall status
        if any(c['status'] == 'unhealthy' for c in checks['checks'].values()):
            checks['status'] = 'unhealthy'
        
        return checks
```

## Next Steps

- [Component Details](./components.md) - Detailed component documentation
- [Data Flow](./data-flow.md) - Data flow and processing pipeline
- [API Reference](../api-reference.md) - Complete API documentation