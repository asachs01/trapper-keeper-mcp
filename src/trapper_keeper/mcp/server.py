"""FastMCP server implementation for Trapper Keeper."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import structlog

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from ..core.base import EventBus
from ..core.config import get_config, get_config_manager
from ..core.types import (
    TrapperKeeperConfig,
    WatchConfig,
    ProcessingConfig,
    OrganizationConfig,
    ExtractedContent,
    ProcessingResult,
)
from ..monitoring import DirectoryWatcher
from ..parser import get_parser
from ..extractor import ContentExtractor
from ..organizer import DocumentOrganizer
from .orchestrator import ProcessingOrchestrator
from .tools import (
    OrganizeDocumentationTool,
    ExtractContentTool,
    CreateReferenceTool,
    ValidateStructureTool,
    AnalyzeDocumentTool,
)
from .metrics import MCPMetricsCollector, MetricsContext, format_metrics_report

logger = structlog.get_logger()

# FastMCP server instance
mcp = FastMCP("trapper-keeper")


# Request/Response models for MCP
class ProcessFileRequest(BaseModel):
    """Request to process a single file."""
    file_path: str = Field(..., description="Path to the file to process")
    extract_categories: Optional[List[str]] = Field(None, description="Categories to extract")
    output_format: str = Field("markdown", description="Output format (markdown, json, yaml)")


class ProcessDirectoryRequest(BaseModel):
    """Request to process a directory."""
    directory_path: str = Field(..., description="Path to the directory to process")
    patterns: List[str] = Field(["*.md", "*.txt"], description="File patterns to match")
    recursive: bool = Field(True, description="Process subdirectories recursively")
    extract_categories: Optional[List[str]] = Field(None, description="Categories to extract")
    output_dir: Optional[str] = Field(None, description="Output directory path")
    output_format: str = Field("markdown", description="Output format (markdown, json, yaml)")


class WatchDirectoryRequest(BaseModel):
    """Request to watch a directory."""
    directory_path: str = Field(..., description="Path to the directory to watch")
    patterns: List[str] = Field(["*.md", "*.txt"], description="File patterns to match")
    recursive: bool = Field(True, description="Watch subdirectories recursively")
    process_existing: bool = Field(True, description="Process existing files")


class ExtractedContentResponse(BaseModel):
    """Response containing extracted content."""
    content_id: str
    document_id: str
    category: str
    title: str
    content: str
    importance: float
    tags: List[str]
    extracted_at: str


class ProcessingResultResponse(BaseModel):
    """Response for processing operations."""
    success: bool
    document_id: str
    extracted_count: int
    errors: List[str]
    warnings: List[str]
    processing_time: Optional[float]
    contents: List[ExtractedContentResponse]


class TrapperKeeperMCP:
    """Main MCP server for Trapper Keeper."""

    def __init__(self, config: Optional[TrapperKeeperConfig] = None):
        self.config = config or get_config()
        self.event_bus = EventBus()
        self.orchestrator: Optional[ProcessingOrchestrator] = None
        self.watchers: Dict[str, DirectoryWatcher] = {}
        self._logger = logger.bind(component="TrapperKeeperMCP")

        # Initialize tools
        self.organize_tool = OrganizeDocumentationTool(self.config, self.event_bus)
        self.extract_tool = ExtractContentTool(self.config, self.event_bus)
        self.reference_tool = CreateReferenceTool(self.config, self.event_bus)
        self.validate_tool = ValidateStructureTool(self.config, self.event_bus)
        self.analyze_tool = AnalyzeDocumentTool(self.config, self.event_bus)

        # Initialize metrics collector
        self.metrics = MCPMetricsCollector()

    async def initialize(self) -> None:
        """Initialize the MCP server."""
        self._logger.info("initializing_mcp_server")

        # Create orchestrator
        self.orchestrator = ProcessingOrchestrator(
            config=self.config,
            event_bus=self.event_bus
        )
        await self.orchestrator.initialize()

        # Initialize tools
        await self.organize_tool.initialize()
        await self.extract_tool.initialize()
        await self.reference_tool.initialize()
        # validate_tool and analyze_tool don't need initialization

        self._logger.info("mcp_server_initialized")

    async def shutdown(self) -> None:
        """Shutdown the MCP server."""
        self._logger.info("shutting_down_mcp_server")

        # Stop all watchers
        for watcher in self.watchers.values():
            await watcher.stop()

        # Stop orchestrator
        if self.orchestrator:
            await self.orchestrator.stop()

        self._logger.info("mcp_server_shutdown")


# Global server instance
_server: Optional[TrapperKeeperMCP] = None


async def get_server() -> TrapperKeeperMCP:
    """Get or create the server instance."""
    global _server
    if _server is None:
        _server = TrapperKeeperMCP()
        await _server.initialize()
    return _server


# MCP Tool implementations
@mcp.tool()
async def process_file(request: ProcessFileRequest) -> ProcessingResultResponse:
    """Process a single file and extract categorized content.

    Args:
        request: Processing configuration for the file

    Returns:
        Processing result with extracted contents
    """
    server = await get_server()

    with MetricsContext(server.metrics, "process_file") as ctx:
        try:
            # Update config if needed
            if request.extract_categories:
                server.config.processing.extract_categories = request.extract_categories

            # Process file
            path = Path(request.file_path)
            result = await server.orchestrator.process_file(path)

            # Update metrics
            if result.success:
                server.metrics.increment_processed_files()
                server.metrics.add_extracted_contents(len(result.extracted_contents))
            else:
                ctx.set_error(result.errors[0] if result.errors else "Processing failed")

            # Convert to response
            contents = [
                ExtractedContentResponse(
                    content_id=content.id,
                    document_id=content.document_id,
                    category=content.category.value if hasattr(content.category, 'value') else content.category,
                    title=content.title,
                    content=content.content,
                    importance=content.importance,
                    tags=list(content.tags),
                    extracted_at=content.extracted_at.isoformat()
                )
                for content in result.extracted_contents
            ]

            return ProcessingResultResponse(
                success=result.success,
                document_id=result.document_id,
                extracted_count=len(result.extracted_contents),
                errors=result.errors,
                warnings=result.warnings,
                processing_time=result.processing_time,
                contents=contents
            )
        except Exception as e:
            ctx.set_error(str(e))
            raise


@mcp.tool()
async def process_directory(request: ProcessDirectoryRequest) -> Dict[str, ProcessingResultResponse]:
    """Process all matching files in a directory.

    Args:
        request: Processing configuration for the directory

    Returns:
        Dictionary mapping file paths to processing results
    """
    server = await get_server()

    # Update config
    if request.extract_categories:
        server.config.processing.extract_categories = request.extract_categories
    if request.output_dir:
        server.config.organization.output_dir = Path(request.output_dir)
    server.config.organization.format = request.output_format

    # Find matching files
    directory = Path(request.directory_path)
    files = []

    for pattern in request.patterns:
        if request.recursive:
            files.extend(directory.rglob(pattern))
        else:
            files.extend(directory.glob(pattern))

    # Process files
    results = {}
    for file_path in files:
        if file_path.is_file():
            result = await server.orchestrator.process_file(file_path)

            # Convert to response
            contents = [
                ExtractedContentResponse(
                    content_id=content.id,
                    document_id=content.document_id,
                    category=content.category.value if hasattr(content.category, 'value') else content.category,
                    title=content.title,
                    content=content.content,
                    importance=content.importance,
                    tags=list(content.tags),
                    extracted_at=content.extracted_at.isoformat()
                )
                for content in result.extracted_contents
            ]

            results[str(file_path)] = ProcessingResultResponse(
                success=result.success,
                document_id=result.document_id,
                extracted_count=len(result.extracted_contents),
                errors=result.errors,
                warnings=result.warnings,
                processing_time=result.processing_time,
                contents=contents
            )

    # Save organized content
    all_contents = []
    for result in results.values():
        if result.success:
            all_contents.extend([
                ExtractedContent(
                    id=c.content_id,
                    document_id=c.document_id,
                    category=c.category,
                    title=c.title,
                    content=c.content,
                    importance=c.importance,
                    tags=set(c.tags),
                    extracted_at=datetime.fromisoformat(c.extracted_at)
                )
                for c in result.contents
            ])

    if all_contents:
        organizer = DocumentOrganizer(server.config.organization, server.event_bus)
        await organizer.initialize()
        organized = await organizer.organize(all_contents)
        await organizer.save(organized)

    return results


@mcp.tool()
async def watch_directory(request: WatchDirectoryRequest) -> Dict[str, str]:
    """Start watching a directory for changes.

    Args:
        request: Watch configuration

    Returns:
        Status information
    """
    server = await get_server()

    directory = Path(request.directory_path)
    if not directory.exists():
        return {"status": "error", "message": f"Directory {directory} does not exist"}

    # Create watch config
    watch_config = WatchConfig(
        paths=[directory],
        patterns=request.patterns,
        recursive=request.recursive
    )

    # Create and start watcher
    watcher = DirectoryWatcher(
        config=watch_config,
        event_bus=server.event_bus,
        process_existing=request.process_existing
    )

    await watcher.initialize()
    await watcher.start()

    # Store watcher
    server.watchers[str(directory)] = watcher

    return {
        "status": "watching",
        "directory": str(directory),
        "patterns": request.patterns,
        "recursive": request.recursive
    }


@mcp.tool()
async def stop_watching(directory_path: str) -> Dict[str, str]:
    """Stop watching a directory.

    Args:
        directory_path: Path to the directory

    Returns:
        Status information
    """
    server = await get_server()

    if directory_path in server.watchers:
        watcher = server.watchers[directory_path]
        await watcher.stop()
        del server.watchers[directory_path]
        return {"status": "stopped", "directory": directory_path}
    else:
        return {"status": "error", "message": f"Not watching {directory_path}"}


@mcp.tool()
async def list_watched_directories() -> List[Dict[str, Union[str, int]]]:
    """List all currently watched directories.

    Returns:
        List of watched directory information
    """
    server = await get_server()

    watched = []
    for path, watcher in server.watchers.items():
        watched.append({
            "directory": path,
            "processed_files": len(watcher.get_processed_files()),
            "queue_size": watcher.get_queue_size()
        })

    return watched


@mcp.tool()
async def get_categories() -> List[str]:
    """Get list of available extraction categories.

    Returns:
        List of category names with emojis
    """
    from ..core.types import ExtractionCategory
    return [cat.value for cat in ExtractionCategory]


@mcp.tool()
async def update_config(config_updates: Dict[str, Union[str, int, bool, List[str]]]) -> Dict[str, str]:
    """Update server configuration.

    Args:
        config_updates: Dictionary of configuration updates

    Returns:
        Status information
    """
    server = await get_server()
    config_manager = get_config_manager()

    try:
        config_manager.update(config_updates)
        server.config = config_manager.load()
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Core Trapper Keeper Tools

@mcp.tool()
async def organize_documentation(
    file_path: str,
    dry_run: bool = False,
    output_dir: Optional[str] = None,
    categories: Optional[List[str]] = None,
    min_importance: float = 0.5,
    create_references: bool = True
) -> Dict[str, Any]:
    """Analyze and organize documentation from a CLAUDE.md file.

    This is the main orchestration tool that:
    1. Analyzes the document structure
    2. Suggests content extractions by category
    3. Executes the organization (unless dry_run)
    4. Returns a summary of actions taken

    Args:
        file_path: Path to CLAUDE.md or similar documentation file
        dry_run: If True, only analyze and suggest without making changes
        output_dir: Directory for organized content (uses config default if not provided)
        categories: Specific categories to extract (all by default)
        min_importance: Minimum importance threshold (0.0-1.0)
        create_references: Create reference links in source document

    Returns:
        Organization results including suggestions and extracted content
    """
    from .tools.organize import OrganizeDocumentationRequest

    server = await get_server()

    with MetricsContext(server.metrics, "organize_documentation") as ctx:
        try:
            request = OrganizeDocumentationRequest(
                file_path=file_path,
                dry_run=dry_run,
                output_dir=output_dir,
                categories=categories,
                min_importance=min_importance,
                create_references=create_references
            )

            response = await server.organize_tool.execute(request)

            # Update metrics
            if response.success and not dry_run:
                server.metrics.increment_processed_files()
                server.metrics.add_extracted_contents(response.extracted_count)

            if not response.success:
                ctx.set_error(response.errors[0] if response.errors else "Unknown error")

            return response.dict()
        except Exception as e:
            ctx.set_error(str(e))
            raise


@mcp.tool()
async def extract_content(
    file_path: str,
    section_ids: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    preserve_context: bool = True,
    update_references: bool = True,
    dry_run: bool = False,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Extract specific sections from a document.

    Supports extraction by:
    - Section IDs
    - Regex patterns
    - Categories

    Args:
        file_path: Path to the file to extract from
        section_ids: Specific section IDs to extract
        patterns: Regex patterns to match content
        categories: Categories to extract
        preserve_context: Include surrounding context
        update_references: Update references in source
        dry_run: Preview extraction without changes
        output_dir: Output directory for extracted content

    Returns:
        Extraction results with details of extracted sections
    """
    from .tools.extract import ExtractContentRequest

    server = await get_server()

    with MetricsContext(server.metrics, "extract_content") as ctx:
        try:
            request = ExtractContentRequest(
                file_path=file_path,
                section_ids=section_ids,
                patterns=patterns,
                categories=categories,
                preserve_context=preserve_context,
                update_references=update_references,
                dry_run=dry_run,
                output_dir=output_dir
            )

            response = await server.extract_tool.execute(request)

            # Update metrics
            if response.success and not dry_run:
                server.metrics.add_extracted_contents(response.total_extracted)

            if not response.success:
                ctx.set_error(response.errors[0] if response.errors else "Unknown error")

            return response.dict()
        except Exception as e:
            ctx.set_error(str(e))
            raise


@mcp.tool()
async def create_reference(
    source_file: str,
    extracted_files: List[str],
    reference_format: str = "markdown",
    index_file: Optional[str] = None,
    create_backlinks: bool = True,
    update_source: bool = True
) -> Dict[str, Any]:
    """Create reference links between source and extracted content.

    Generates links in multiple formats:
    - markdown: Standard markdown links with context
    - link-list: Simple bulleted list of links
    - index: Table format for index files

    Args:
        source_file: Path to source file that was extracted from
        extracted_files: List of extracted content files
        reference_format: Format for references (markdown, link-list, index)
        index_file: Path to index file to update
        create_backlinks: Add backlinks in extracted files
        update_source: Update source file with references

    Returns:
        Details of created references and links
    """
    from .tools.reference import CreateReferenceRequest

    server = await get_server()

    with MetricsContext(server.metrics, "create_reference") as ctx:
        try:
            request = CreateReferenceRequest(
                source_file=source_file,
                extracted_files=extracted_files,
                reference_format=reference_format,
                index_file=index_file,
                create_backlinks=create_backlinks,
                update_source=update_source
            )

            response = await server.reference_tool.execute(request)

            if not response.success:
                ctx.set_error(response.errors[0] if response.errors else "Unknown error")

            return response.dict()
        except Exception as e:
            ctx.set_error(str(e))
            raise


@mcp.tool()
async def validate_structure(
    root_dir: str,
    source_files: Optional[List[str]] = None,
    check_references: bool = True,
    check_orphans: bool = True,
    check_structure: bool = True,
    patterns: List[str] = None
) -> Dict[str, Any]:
    """Validate documentation structure and integrity.

    Checks for:
    - Broken references
    - Orphaned documents
    - Missing categories
    - Invalid structure

    Args:
        root_dir: Root directory to validate
        source_files: Specific files to check (all by default)
        check_references: Validate all references are valid
        check_orphans: Find orphaned documents
        check_structure: Verify directory structure
        patterns: File patterns to validate (*.md, *.txt by default)

    Returns:
        Validation report with issues found
    """
    from .tools.validate import ValidateStructureRequest

    server = await get_server()

    with MetricsContext(server.metrics, "validate_structure") as ctx:
        try:
            request = ValidateStructureRequest(
                root_dir=root_dir,
                source_files=source_files,
                check_references=check_references,
                check_orphans=check_orphans,
                check_structure=check_structure,
                patterns=patterns or ["*.md", "*.txt"]
            )

            response = await server.validate_tool.execute(request)

            if not response.success:
                ctx.set_error(response.errors[0] if response.errors else "Unknown error")

            return response.dict()
        except Exception as e:
            ctx.set_error(str(e))
            raise


@mcp.tool()
async def get_server_metrics() -> Dict[str, Any]:
    """Get server performance metrics and statistics.

    Returns:
        Comprehensive metrics including server status and tool performance
    """
    server = await get_server()

    # Update watcher count
    server.metrics.update_watcher_count(len(server.watchers))

    metrics = server.metrics.get_metrics_summary()
    metrics["formatted_report"] = format_metrics_report(metrics)

    return metrics


@mcp.tool()
async def analyze_document(
    file_path: str,
    include_statistics: bool = True,
    include_growth: bool = True,
    include_recommendations: bool = True,
    days_for_growth: int = 30
) -> Dict[str, Any]:
    """Analyze a document and provide insights.

    Provides:
    - Document statistics (size, sections, complexity)
    - Category distribution
    - Growth patterns
    - Extraction recommendations
    - Actionable insights

    Args:
        file_path: Path to document to analyze
        include_statistics: Include detailed statistics
        include_growth: Analyze growth patterns
        include_recommendations: Provide extraction recommendations
        days_for_growth: Number of days to analyze for growth

    Returns:
        Comprehensive analysis with insights and recommendations
    """
    from .tools.analyze import AnalyzeDocumentRequest

    server = await get_server()

    with MetricsContext(server.metrics, "analyze_document") as ctx:
        try:
            request = AnalyzeDocumentRequest(
                file_path=file_path,
                include_statistics=include_statistics,
                include_growth=include_growth,
                include_recommendations=include_recommendations,
                days_for_growth=days_for_growth
            )

            response = await server.analyze_tool.execute(request)

            if not response.success:
                ctx.set_error(response.errors[0] if response.errors else "Unknown error")

            return response.dict()
        except Exception as e:
            ctx.set_error(str(e))
            raise


# Main entry point
def main():
    """Run the MCP server."""
    import uvicorn

    # Get config
    config = get_config()

    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Run server
    uvicorn.run(
        mcp,
        host=config.mcp_host,
        port=config.mcp_port,
        log_level=config.log_level.lower()
    )


if __name__ == "__main__":
    main()
