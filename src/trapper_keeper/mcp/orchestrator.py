"""Processing orchestrator for coordinating document processing pipeline."""

import asyncio
import time
from pathlib import Path
from typing import List, Optional
import structlog

from ..core.base import Component, EventBus
from ..core.types import (
    Document,
    ProcessingResult,
    TrapperKeeperConfig,
    EventType,
)
from ..parser import get_parser
from ..extractor import ContentExtractor
from ..organizer import DocumentOrganizer

logger = structlog.get_logger()


class ProcessingOrchestrator(Component):
    """Orchestrates the document processing pipeline."""
    
    def __init__(self, config: TrapperKeeperConfig, event_bus: Optional[EventBus] = None):
        super().__init__("ProcessingOrchestrator", event_bus)
        self.config = config
        self.extractor: Optional[ContentExtractor] = None
        self.organizer: Optional[DocumentOrganizer] = None
        self._processing_semaphore: Optional[asyncio.Semaphore] = None
        
    async def _initialize(self) -> None:
        """Initialize the orchestrator."""
        # Create components
        self.extractor = ContentExtractor(self.config.processing, self.event_bus)
        self.organizer = DocumentOrganizer(self.config.organization, self.event_bus)
        
        # Initialize components
        await self.extractor.initialize()
        await self.organizer.initialize()
        
        # Create semaphore for concurrent processing
        self._processing_semaphore = asyncio.Semaphore(self.config.max_concurrent_processing)
        
        # Subscribe to processing events
        self._processing_queue = self.subscribe_to_event(EventType.PROCESSING_STARTED)
        
    async def _start(self) -> None:
        """Start the orchestrator."""
        # Start components
        await self.extractor.start()
        await self.organizer.start()
        
        # Start processing task
        self._processing_task = asyncio.create_task(self._process_events())
        
    async def _stop(self) -> None:
        """Stop the orchestrator."""
        # Stop processing task
        if hasattr(self, '_processing_task'):
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
        # Stop components
        if self.extractor:
            await self.extractor.stop()
        if self.organizer:
            await self.organizer.stop()
            
    async def _process_events(self) -> None:
        """Process events from the event queue."""
        while True:
            try:
                event = await self._processing_queue.get()
                
                if event.type == EventType.PROCESSING_STARTED:
                    # Process file asynchronously with semaphore
                    path = Path(event.data["path"])
                    asyncio.create_task(self._process_file_with_semaphore(path))
                    
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.error("error_processing_event", error=str(e))
                
    async def _process_file_with_semaphore(self, path: Path) -> None:
        """Process a file with concurrency control."""
        async with self._processing_semaphore:
            try:
                await self.process_file(path)
            except Exception as e:
                self._logger.error("error_processing_file", path=str(path), error=str(e))
                
    async def process_file(self, path: Path) -> ProcessingResult:
        """Process a single file through the pipeline."""
        start_time = time.time()
        self._logger.info("processing_file", path=str(path))
        
        result = ProcessingResult(
            document_id="",
            success=False
        )
        
        try:
            # Get parser
            parser = get_parser(path, self.event_bus)
            if not parser:
                result.errors.append(f"No parser available for {path}")
                return result
                
            # Parse document
            await parser.initialize()
            content = path.read_text(encoding='utf-8')
            document = await parser.parse(content, path)
            result.document_id = document.id
            
            # Extract content
            extracted_contents = await self.extractor.extract(document)
            result.extracted_contents = extracted_contents
            
            # Organize and save if configured
            if extracted_contents and self.config.organization.output_dir:
                organized = await self.organizer.organize(extracted_contents)
                
                # Create document-specific output dir
                doc_output_dir = self.config.organization.output_dir / document.id
                await self.organizer.save(organized, doc_output_dir)
                
            result.success = True
            result.processing_time = time.time() - start_time
            
            self._logger.info(
                "file_processed",
                path=str(path),
                document_id=document.id,
                extracted_count=len(extracted_contents),
                processing_time=result.processing_time
            )
            
            # Publish completion event
            await self.publish_event(
                EventType.PROCESSING_COMPLETED,
                {
                    "path": str(path),
                    "document_id": document.id,
                    "extracted_count": len(extracted_contents),
                    "processing_time": result.processing_time
                }
            )
            
        except Exception as e:
            result.errors.append(str(e))
            result.processing_time = time.time() - start_time
            
            self._logger.error(
                "file_processing_failed",
                path=str(path),
                error=str(e)
            )
            
            # Publish failure event
            await self.publish_event(
                EventType.PROCESSING_FAILED,
                {
                    "path": str(path),
                    "error": str(e)
                }
            )
            
        return result
        
    async def process_files(self, paths: List[Path]) -> List[ProcessingResult]:
        """Process multiple files concurrently."""
        tasks = [self.process_file(path) for path in paths]
        return await asyncio.gather(*tasks)
        
    async def process_directory(
        self,
        directory: Path,
        patterns: List[str] = None,
        recursive: bool = True
    ) -> List[ProcessingResult]:
        """Process all matching files in a directory."""
        if not directory.exists() or not directory.is_dir():
            self._logger.error("invalid_directory", path=str(directory))
            return []
            
        patterns = patterns or ["*.md", "*.txt"]
        files = []
        
        for pattern in patterns:
            if recursive:
                files.extend(directory.rglob(pattern))
            else:
                files.extend(directory.glob(pattern))
                
        # Filter to only files
        files = [f for f in files if f.is_file()]
        
        self._logger.info(
            "processing_directory",
            directory=str(directory),
            file_count=len(files),
            patterns=patterns,
            recursive=recursive
        )
        
        return await self.process_files(files)