"""Type definitions and dataclasses for Trapper Keeper MCP."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for the event bus."""
    
    # File monitoring events
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"
    FILE_MOVED = "file.moved"
    FILE_THRESHOLD_EXCEEDED = "file.threshold_exceeded"
    
    # Processing events
    PROCESSING_STARTED = "processing.started"
    PROCESSING_COMPLETED = "processing.completed"
    PROCESSING_FAILED = "processing.failed"
    
    # Extraction events
    EXTRACTION_STARTED = "extraction.started"
    EXTRACTION_COMPLETED = "extraction.completed"
    EXTRACTION_FAILED = "extraction.failed"
    
    # Organization events
    ORGANIZATION_STARTED = "organization.started"
    ORGANIZATION_COMPLETED = "organization.completed"
    ORGANIZATION_FAILED = "organization.failed"
    
    # System events
    COMPONENT_INITIALIZED = "component.initialized"
    COMPONENT_STARTED = "component.started"
    COMPONENT_STOPPED = "component.stopped"
    COMPONENT_ERROR = "component.error"


class DocumentType(str, Enum):
    """Supported document types."""
    
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    HTML = "html"
    UNKNOWN = "unknown"


class ExtractionCategory(str, Enum):
    """Standard extraction categories with emojis."""
    
    ARCHITECTURE = "🏗️ Architecture"
    DATABASE = "🗄️ Database"
    SECURITY = "🔐 Security"
    FEATURES = "✅ Features"
    MONITORING = "📊 Monitoring"
    CRITICAL = "🚨 Critical"
    SETUP = "📋 Setup"
    API = "🌐 API"
    TESTING = "🧪 Testing"
    PERFORMANCE = "⚡ Performance"
    DOCUMENTATION = "📚 Documentation"
    DEPLOYMENT = "🚀 Deployment"
    CONFIGURATION = "⚙️ Configuration"
    DEPENDENCIES = "📦 Dependencies"
    CUSTOM = "🔧 Custom"


@dataclass
class Event:
    """Event for component communication."""
    
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    

@dataclass
class DocumentMetadata:
    """Metadata for a document."""
    
    path: Optional[Path] = None
    size: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a document to be processed."""
    
    id: str
    type: DocumentType
    content: str
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    sections: List["DocumentSection"] = field(default_factory=list)
    

@dataclass
class DocumentSection:
    """A section within a document."""
    
    id: str
    title: str
    content: str
    level: int
    parent_id: Optional[str] = None
    children: List["DocumentSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedContent:
    """Content extracted from a document."""
    
    id: str
    document_id: str
    category: Union[ExtractionCategory, str]
    title: str
    content: str
    importance: float = 1.0  # 0.0 to 1.0
    source_section: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProcessingResult:
    """Result of processing a document."""
    
    document_id: str
    success: bool
    extracted_contents: List[ExtractedContent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""
    
    extract_categories: List[Union[ExtractionCategory, str]] = Field(
        default_factory=lambda: list(ExtractionCategory)
    )
    min_importance: float = Field(0.3, ge=0.0, le=1.0)
    include_metadata: bool = True
    preserve_structure: bool = True
    extract_code_blocks: bool = True
    extract_links: bool = True
    extract_images: bool = True
    custom_patterns: Dict[str, str] = Field(default_factory=dict)


class WatchConfig(BaseModel):
    """Configuration for file watching."""
    
    paths: List[Path] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=lambda: ["*.md", "*.txt"])
    ignore_patterns: List[str] = Field(default_factory=lambda: [".*", "__pycache__", "*.pyc"])
    recursive: bool = True
    follow_symlinks: bool = False
    debounce_seconds: float = 1.0


class OrganizationConfig(BaseModel):
    """Configuration for content organization."""
    
    output_dir: Path
    group_by_category: bool = True
    group_by_document: bool = False
    create_index: bool = True
    include_metadata: bool = True
    format: str = "markdown"  # markdown, json, yaml
    template: Optional[str] = None


class TrapperKeeperConfig(BaseModel):
    """Main configuration for Trapper Keeper."""
    
    # Component configs
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    watching: WatchConfig = Field(default_factory=WatchConfig)
    organization: OrganizationConfig = Field(default_factory=lambda: OrganizationConfig(output_dir=Path("output")))
    
    # System configs
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    max_concurrent_processing: int = 10
    plugin_dirs: List[Path] = Field(default_factory=list)
    
    # MCP specific
    mcp_enabled: bool = True
    mcp_host: str = "localhost"
    mcp_port: int = 8765