"""High-level directory watcher that coordinates file monitoring and processing."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import structlog

from ..core.base import Component, EventBus
from ..core.types import EventType, WatchConfig, Document
from .file_monitor import FileMonitor

logger = structlog.get_logger()


class DirectoryWatcher(Component):
    """Watches directories and coordinates file processing."""
    
    def __init__(
        self,
        config: WatchConfig,
        event_bus: Optional[EventBus] = None,
        process_existing: bool = True
    ):
        super().__init__("DirectoryWatcher", event_bus)
        self.config = config
        self.process_existing = process_existing
        self._file_monitor: Optional[FileMonitor] = None
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._processed_files: Set[Path] = set()
        self._file_timestamps: Dict[Path, datetime] = {}
        self._processing_task: Optional[asyncio.Task] = None
        
    async def _initialize(self) -> None:
        """Initialize the directory watcher."""
        # Create file monitor
        self._file_monitor = FileMonitor(self.config, self.event_bus)
        await self._file_monitor.initialize()
        
        # Subscribe to file events
        self._file_created_queue = self.subscribe_to_event(EventType.FILE_CREATED)
        self._file_modified_queue = self.subscribe_to_event(EventType.FILE_MODIFIED)
        self._file_deleted_queue = self.subscribe_to_event(EventType.FILE_DELETED)
        
    async def _start(self) -> None:
        """Start watching directories."""
        # Start file monitor
        await self._file_monitor.start()
        
        # Process existing files if requested
        if self.process_existing:
            await self._process_existing_files()
            
        # Start event processing
        self._processing_task = asyncio.create_task(self._process_events())
        
    async def _stop(self) -> None:
        """Stop watching directories."""
        # Stop event processing
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
                
        # Stop file monitor
        if self._file_monitor:
            await self._file_monitor.stop()
            
    async def _process_existing_files(self) -> None:
        """Process existing files in watched directories."""
        self._logger.info("processing_existing_files")
        
        for watch_path in self.config.paths:
            if not watch_path.exists():
                continue
                
            # Find all matching files
            if watch_path.is_file():
                files = [watch_path]
            else:
                files = []
                for pattern in self.config.patterns:
                    if self.config.recursive:
                        files.extend(watch_path.rglob(pattern))
                    else:
                        files.extend(watch_path.glob(pattern))
                        
            # Queue files for processing
            for file_path in files:
                if file_path.is_file() and not self._should_ignore(file_path):
                    await self._queue_file_for_processing(file_path)
                    
        self._logger.info("queued_existing_files", count=self._processing_queue.qsize())
        
    async def _process_events(self) -> None:
        """Process file events from the monitor."""
        tasks = [
            asyncio.create_task(self._process_event_queue(self._file_created_queue, "created")),
            asyncio.create_task(self._process_event_queue(self._file_modified_queue, "modified")),
            asyncio.create_task(self._process_event_queue(self._file_deleted_queue, "deleted")),
            asyncio.create_task(self._process_file_queue()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()
            raise
            
    async def _process_event_queue(self, queue: asyncio.Queue, event_type: str) -> None:
        """Process events from a specific queue."""
        while True:
            try:
                event = await queue.get()
                path = Path(event.data["path"])
                
                if event_type == "created" or event_type == "modified":
                    if not event.data.get("is_directory", False):
                        await self._queue_file_for_processing(path)
                elif event_type == "deleted":
                    await self._handle_file_deleted(path)
                    
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.error(
                    "error_processing_event",
                    event_type=event_type,
                    error=str(e)
                )
                
    async def _process_file_queue(self) -> None:
        """Process files from the processing queue."""
        while True:
            try:
                file_path = await self._processing_queue.get()
                
                # Check if file still exists
                if not file_path.exists():
                    continue
                    
                # Check if file was recently processed
                if self._was_recently_processed(file_path):
                    continue
                    
                # Process the file
                await self._process_file(file_path)
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._logger.error(
                    "error_processing_file",
                    file=str(file_path),
                    error=str(e)
                )
                
    async def _queue_file_for_processing(self, path: Path) -> None:
        """Queue a file for processing."""
        if path not in self._processed_files:
            await self._processing_queue.put(path)
            self._logger.debug("file_queued", path=str(path))
            
    async def _process_file(self, path: Path) -> None:
        """Process a single file."""
        self._logger.info("processing_file", path=str(path))
        
        # Mark as processed
        self._processed_files.add(path)
        self._file_timestamps[path] = datetime.utcnow()
        
        # Publish processing started event
        await self.publish_event(
            EventType.PROCESSING_STARTED,
            {"path": str(path), "timestamp": datetime.utcnow().isoformat()}
        )
        
        # The actual processing will be handled by other components
        # listening to the PROCESSING_STARTED event
        
    async def _handle_file_deleted(self, path: Path) -> None:
        """Handle file deletion."""
        if path in self._processed_files:
            self._processed_files.remove(path)
            
        if path in self._file_timestamps:
            del self._file_timestamps[path]
            
        self._logger.info("file_deleted", path=str(path))
        
    def _was_recently_processed(self, path: Path) -> bool:
        """Check if a file was recently processed."""
        if path not in self._file_timestamps:
            return False
            
        # Consider a file recently processed if it was processed
        # within the debounce period
        last_processed = self._file_timestamps[path]
        debounce_delta = timedelta(seconds=self.config.debounce_seconds * 2)
        
        return datetime.utcnow() - last_processed < debounce_delta
        
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path)
        
        for pattern in self.config.ignore_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if path_str.startswith(pattern[:-1]):
                    return True
            elif pattern in path_str:
                return True
                
        return False
        
    def get_processed_files(self) -> List[Path]:
        """Get list of processed files."""
        return list(self._processed_files)
        
    def get_queue_size(self) -> int:
        """Get the size of the processing queue."""
        return self._processing_queue.qsize()