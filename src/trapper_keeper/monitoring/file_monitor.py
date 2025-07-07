"""File monitoring implementation using watchdog."""

import asyncio
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirModifiedEvent,
    DirDeletedEvent,
    DirMovedEvent,
)
import structlog

from ..core.base import Monitor, EventBus
from ..core.types import EventType, WatchConfig

logger = structlog.get_logger()


@dataclass
class FileStatistics:
    """File statistics for monitoring."""
    
    size: int
    line_count: int
    last_modified: datetime
    growth_rate: float = 0.0  # Lines per hour
    
    
@dataclass
class FileEvent:
    """Represents a file system event."""
    
    type: str  # created, modified, deleted, moved
    path: Path
    is_directory: bool
    timestamp: datetime = None
    old_path: Optional[Path] = None  # For move events
    statistics: Optional[FileStatistics] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AsyncFileEventHandler(FileSystemEventHandler):
    """Async wrapper for watchdog event handler."""
    
    def __init__(self, loop: asyncio.AbstractEventLoop, callback: Callable):
        self.loop = loop
        self.callback = callback
        self._debounce_tasks: Dict[str, asyncio.Task] = {}
        self._debounce_seconds = 0.5
        
    async def _debounced_callback(self, event: FileEvent, delay: float):
        """Debounce rapid file events."""
        await asyncio.sleep(delay)
        await self.callback(event)
        
    def _schedule_callback(self, event: FileEvent):
        """Schedule a debounced callback."""
        path_str = str(event.path)
        
        # Cancel existing task for this path
        if path_str in self._debounce_tasks:
            self._debounce_tasks[path_str].cancel()
            
        # Schedule new task
        task = asyncio.run_coroutine_threadsafe(
            self._debounced_callback(event, self._debounce_seconds),
            self.loop
        )
        self._debounce_tasks[path_str] = task
        
    def on_created(self, event):
        """Handle file/directory creation."""
        if isinstance(event, (FileCreatedEvent, DirCreatedEvent)):
            file_event = FileEvent(
                type="created",
                path=Path(event.src_path),
                is_directory=event.is_directory
            )
            self._schedule_callback(file_event)
            
    def on_modified(self, event):
        """Handle file/directory modification."""
        if isinstance(event, (FileModifiedEvent, DirModifiedEvent)):
            file_event = FileEvent(
                type="modified",
                path=Path(event.src_path),
                is_directory=event.is_directory
            )
            self._schedule_callback(file_event)
            
    def on_deleted(self, event):
        """Handle file/directory deletion."""
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            file_event = FileEvent(
                type="deleted",
                path=Path(event.src_path),
                is_directory=event.is_directory
            )
            self._schedule_callback(file_event)
            
    def on_moved(self, event):
        """Handle file/directory move."""
        if isinstance(event, (FileMovedEvent, DirMovedEvent)):
            file_event = FileEvent(
                type="moved",
                path=Path(event.dest_path),
                is_directory=event.is_directory,
                old_path=Path(event.src_path)
            )
            self._schedule_callback(file_event)


class FileMonitor(Monitor):
    """Monitors files and directories for changes."""
    
    def __init__(self, config: WatchConfig, event_bus: Optional[EventBus] = None):
        super().__init__("FileMonitor", event_bus)
        self.config = config
        self._observer: Optional[Observer] = None
        self._watched_paths: Set[Path] = set()
        self._event_handlers: Dict[Path, AsyncFileEventHandler] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # File statistics tracking
        self._file_stats: Dict[Path, FileStatistics] = {}
        self._growth_history: Dict[Path, List[Tuple[datetime, int]]] = {}
        
        # Thresholds
        self.size_threshold_lines = getattr(config, 'size_threshold_lines', 200)
        self.size_threshold_bytes = getattr(config, 'size_threshold_bytes', 1024 * 1024)  # 1MB
        self.growth_rate_threshold = getattr(config, 'growth_rate_threshold', 50.0)  # lines/hour
        
    async def _initialize(self) -> None:
        """Initialize the file monitor."""
        self._loop = asyncio.get_event_loop()
        self._observer = Observer()
        
    async def _start(self) -> None:
        """Start the file monitor."""
        if self._observer is None:
            raise RuntimeError("FileMonitor not initialized")
            
        # Start watching configured paths
        for path in self.config.paths:
            await self.watch(path)
            
        # Start the observer
        self._observer.start()
        self._logger.info("file_monitor_started", paths=len(self._watched_paths))
        
    async def _stop(self) -> None:
        """Stop the file monitor."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None
            
        self._watched_paths.clear()
        self._event_handlers.clear()
        self._logger.info("file_monitor_stopped")
        
    async def watch(self, path: Path) -> None:
        """Start watching a path for changes."""
        if not path.exists():
            self._logger.warning("path_does_not_exist", path=str(path))
            return
            
        if path in self._watched_paths:
            self._logger.debug("path_already_watched", path=str(path))
            return
            
        # Create event handler
        handler = AsyncFileEventHandler(self._loop, self._handle_file_event)
        handler._debounce_seconds = self.config.debounce_seconds
        
        # Schedule observer
        self._observer.schedule(
            handler,
            str(path),
            recursive=self.config.recursive
        )
        
        self._watched_paths.add(path)
        self._event_handlers[path] = handler
        self._logger.info("watching_path", path=str(path), recursive=self.config.recursive)
        
    async def unwatch(self, path: Path) -> None:
        """Stop watching a path."""
        if path not in self._watched_paths:
            return
            
        # Remove from observer
        self._observer.unschedule_all()
        
        # Remove from tracking
        self._watched_paths.remove(path)
        del self._event_handlers[path]
        
        # Re-schedule remaining paths
        for watched_path, handler in self._event_handlers.items():
            self._observer.schedule(
                handler,
                str(watched_path),
                recursive=self.config.recursive
            )
            
        self._logger.info("unwatched_path", path=str(path))
        
    def get_watched_paths(self) -> List[Path]:
        """Get list of currently watched paths."""
        return list(self._watched_paths)
        
    async def _handle_file_event(self, event: FileEvent) -> None:
        """Handle a file system event."""
        # Check if we should ignore this event
        if self._should_ignore(event.path):
            return
            
        # Check if it matches our patterns
        if not self._matches_patterns(event.path):
            return
            
        # Calculate file statistics for non-directory events
        if not event.is_directory and event.type in ["created", "modified"]:
            stats = await self._calculate_file_statistics(event.path)
            if stats:
                event.statistics = stats
                
                # Check thresholds
                threshold_violations = await self._check_thresholds(event.path, stats)
                if threshold_violations:
                    await self._handle_threshold_violations(event.path, stats, threshold_violations)
                    
        self._logger.debug(
            "file_event",
            type=event.type,
            path=str(event.path),
            is_directory=event.is_directory,
            statistics=event.statistics
        )
        
        # Publish event to event bus
        event_type_map = {
            "created": EventType.FILE_CREATED,
            "modified": EventType.FILE_MODIFIED,
            "deleted": EventType.FILE_DELETED,
            "moved": EventType.FILE_MOVED,
        }
        
        event_type = event_type_map.get(event.type)
        if event_type:
            event_data = {
                "path": str(event.path),
                "is_directory": event.is_directory,
                "timestamp": event.timestamp.isoformat(),
            }
            
            if event.old_path:
                event_data["old_path"] = str(event.old_path)
                
            if event.statistics:
                event_data["statistics"] = {
                    "size": event.statistics.size,
                    "line_count": event.statistics.line_count,
                    "growth_rate": event.statistics.growth_rate,
                }
                
            await self.publish_event(event_type, event_data)
            
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
        
    def _matches_patterns(self, path: Path) -> bool:
        """Check if a path matches watch patterns."""
        if path.is_dir():
            return True  # Always process directories
            
        # Check against patterns
        for pattern in self.config.patterns:
            if path.match(pattern):
                return True
                
        return False
        
    async def _calculate_file_statistics(self, path: Path) -> Optional[FileStatistics]:
        """Calculate statistics for a file."""
        try:
            if not path.exists() or not path.is_file():
                return None
                
            stat = path.stat()
            size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Count lines
            line_count = 0
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = sum(1 for _ in f)
            except Exception as e:
                self._logger.warning("error_counting_lines", path=str(path), error=str(e))
                
            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(path, line_count)
            
            stats = FileStatistics(
                size=size,
                line_count=line_count,
                last_modified=modified_time,
                growth_rate=growth_rate
            )
            
            # Update tracking
            self._file_stats[path] = stats
            self._update_growth_history(path, line_count)
            
            return stats
            
        except Exception as e:
            self._logger.error("error_calculating_statistics", path=str(path), error=str(e))
            return None
            
    def _calculate_growth_rate(self, path: Path, current_lines: int) -> float:
        """Calculate file growth rate in lines per hour."""
        if path not in self._growth_history or len(self._growth_history[path]) < 2:
            return 0.0
            
        history = self._growth_history[path]
        
        # Get the oldest and newest records
        oldest_time, oldest_lines = history[0]
        newest_time = datetime.utcnow()
        
        # Calculate time difference in hours
        time_diff = (newest_time - oldest_time).total_seconds() / 3600.0
        
        if time_diff == 0:
            return 0.0
            
        # Calculate growth rate
        lines_added = current_lines - oldest_lines
        growth_rate = lines_added / time_diff
        
        return max(0.0, growth_rate)
        
    def _update_growth_history(self, path: Path, line_count: int) -> None:
        """Update growth history for a file."""
        if path not in self._growth_history:
            self._growth_history[path] = []
            
        history = self._growth_history[path]
        current_time = datetime.utcnow()
        
        # Add new record
        history.append((current_time, line_count))
        
        # Keep only records from last 24 hours
        cutoff_time = current_time - timedelta(hours=24)
        self._growth_history[path] = [
            (t, l) for t, l in history if t > cutoff_time
        ]
        
    async def _check_thresholds(self, path: Path, stats: FileStatistics) -> List[str]:
        """Check if file exceeds any thresholds."""
        violations = []
        
        if stats.line_count > self.size_threshold_lines:
            violations.append(f"line_count_exceeded:{stats.line_count}>{self.size_threshold_lines}")
            
        if stats.size > self.size_threshold_bytes:
            violations.append(f"size_exceeded:{stats.size}>{self.size_threshold_bytes}")
            
        if stats.growth_rate > self.growth_rate_threshold:
            violations.append(f"growth_rate_exceeded:{stats.growth_rate:.2f}>{self.growth_rate_threshold}")
            
        return violations
        
    async def _handle_threshold_violations(
        self,
        path: Path,
        stats: FileStatistics,
        violations: List[str]
    ) -> None:
        """Handle threshold violations."""
        self._logger.warning(
            "threshold_violations",
            path=str(path),
            violations=violations,
            statistics={
                "size": stats.size,
                "line_count": stats.line_count,
                "growth_rate": stats.growth_rate,
            }
        )
        
        # Publish threshold event
        await self.publish_event(
            EventType.FILE_THRESHOLD_EXCEEDED,
            {
                "path": str(path),
                "violations": violations,
                "statistics": {
                    "size": stats.size,
                    "line_count": stats.line_count,
                    "growth_rate": stats.growth_rate,
                    "last_modified": stats.last_modified.isoformat(),
                }
            }
        )
        
    async def watch_batch(self, paths: List[Path]) -> None:
        """Start watching multiple paths in batch."""
        for path in paths:
            await self.watch(path)
            
        self._logger.info("batch_watch_started", count=len(paths))
        
    def get_file_statistics(self, path: Path) -> Optional[FileStatistics]:
        """Get current statistics for a monitored file."""
        return self._file_stats.get(path)
        
    def get_all_statistics(self) -> Dict[Path, FileStatistics]:
        """Get statistics for all monitored files."""
        return self._file_stats.copy()