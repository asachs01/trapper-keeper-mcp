"""Unit tests for file monitoring functionality."""

import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
import pytest_asyncio
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)

from trapper_keeper.monitoring.file_monitor import (
    FileMonitor,
    FileStatistics,
    FileEvent,
    FileEventHandler,
    ChangeThreshold,
)
from trapper_keeper.core.types import EventType, WatchConfig


class TestFileStatistics:
    """Test FileStatistics dataclass."""
    
    def test_statistics_creation(self):
        """Test creating file statistics."""
        stats = FileStatistics(
            size=1024,
            line_count=50,
            last_modified=datetime.now(),
            growth_rate=10.5,
        )
        
        assert stats.size == 1024
        assert stats.line_count == 50
        assert stats.growth_rate == 10.5
        assert isinstance(stats.last_modified, datetime)
    
    def test_statistics_defaults(self):
        """Test default values for statistics."""
        now = datetime.now()
        stats = FileStatistics(
            size=100,
            line_count=10,
            last_modified=now,
        )
        
        assert stats.growth_rate == 0.0


class TestFileEvent:
    """Test FileEvent dataclass."""
    
    def test_file_event_creation(self):
        """Test creating a file event."""
        event = FileEvent(
            type="created",
            path=Path("/test/file.md"),
            is_directory=False,
        )
        
        assert event.type == "created"
        assert event.path == Path("/test/file.md")
        assert event.is_directory is False
        assert event.timestamp is not None
        assert event.old_path is None
        assert event.statistics is None
    
    def test_file_event_with_timestamp(self):
        """Test file event with explicit timestamp."""
        timestamp = datetime.now()
        event = FileEvent(
            type="modified",
            path=Path("/test/file.md"),
            is_directory=False,
            timestamp=timestamp,
        )
        
        assert event.timestamp == timestamp
    
    def test_move_event(self):
        """Test file move event."""
        event = FileEvent(
            type="moved",
            path=Path("/test/new.md"),
            is_directory=False,
            old_path=Path("/test/old.md"),
        )
        
        assert event.type == "moved"
        assert event.path == Path("/test/new.md")
        assert event.old_path == Path("/test/old.md")


class TestFileEventHandler:
    """Test FileEventHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create a file event handler."""
        monitor = Mock()
        monitor._debounce_seconds = 0.1
        monitor._handle_file_event = AsyncMock()
        
        handler = FileEventHandler(monitor)
        return handler
    
    def test_on_created(self, handler):
        """Test handling file creation."""
        event = FileCreatedEvent("/test/new.md")
        handler.on_created(event)
        
        # Should be debounced
        assert "/test/new.md" in handler._pending_events
        assert handler._pending_events["/test/new.md"]["type"] == "created"
    
    def test_on_modified(self, handler):
        """Test handling file modification."""
        event = FileModifiedEvent("/test/file.md")
        handler.on_modified(event)
        
        assert "/test/file.md" in handler._pending_events
        assert handler._pending_events["/test/file.md"]["type"] == "modified"
    
    def test_on_deleted(self, handler):
        """Test handling file deletion."""
        event = FileDeletedEvent("/test/old.md")
        handler.on_deleted(event)
        
        assert "/test/old.md" in handler._pending_events
        assert handler._pending_events["/test/old.md"]["type"] == "deleted"
    
    def test_on_moved(self, handler):
        """Test handling file move."""
        event = FileMovedEvent("/test/old.md", "/test/new.md")
        handler.on_moved(event)
        
        assert "/test/new.md" in handler._pending_events
        assert handler._pending_events["/test/new.md"]["type"] == "moved"
        assert handler._pending_events["/test/new.md"]["old_path"] == "/test/old.md"
    
    @pytest.mark.asyncio
    async def test_debouncing(self, handler):
        """Test event debouncing."""
        # Create multiple events for the same file
        event1 = FileModifiedEvent("/test/file.md")
        event2 = FileModifiedEvent("/test/file.md")
        event3 = FileModifiedEvent("/test/file.md")
        
        handler.on_modified(event1)
        await asyncio.sleep(0.05)
        handler.on_modified(event2)
        await asyncio.sleep(0.05)
        handler.on_modified(event3)
        
        # Should still be pending
        assert "/test/file.md" in handler._pending_events
        
        # Wait for debounce
        await asyncio.sleep(0.2)
        
        # Should have been processed
        assert "/test/file.md" not in handler._pending_events


class TestFileMonitor:
    """Test FileMonitor class."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus."""
        bus = Mock()
        bus.publish = AsyncMock()
        return bus
    
    @pytest.fixture
    def config(self, temp_dir):
        """Create a watch configuration."""
        return WatchConfig(
            paths=[temp_dir],
            patterns=["*.md", "*.txt"],
            ignore_patterns=[".*", "__pycache__"],
            recursive=True,
            follow_symlinks=False,
            debounce_seconds=0.1,
        )
    
    @pytest.fixture
    def monitor(self, mock_event_bus, config):
        """Create a file monitor."""
        return FileMonitor(config, mock_event_bus)
    
    @pytest.mark.asyncio
    async def test_initialization(self, monitor):
        """Test monitor initialization."""
        await monitor.initialize()
        
        assert monitor.is_initialized
        assert monitor._observer is not None
        assert monitor._handler is not None
    
    @pytest.mark.asyncio
    async def test_start_stop(self, monitor):
        """Test starting and stopping monitor."""
        await monitor.initialize()
        
        with patch.object(monitor._observer, 'start') as mock_start:
            with patch.object(monitor._observer, 'stop') as mock_stop:
                with patch.object(monitor._observer, 'join') as mock_join:
                    # Start
                    await monitor.start()
                    assert monitor.is_running
                    mock_start.assert_called_once()
                    
                    # Stop
                    await monitor.stop()
                    assert not monitor.is_running
                    mock_stop.assert_called_once()
                    mock_join.assert_called_once()
    
    def test_should_process_file(self, monitor):
        """Test file pattern matching."""
        # Should process
        assert monitor._should_process_file(Path("test.md"))
        assert monitor._should_process_file(Path("doc.txt"))
        assert monitor._should_process_file(Path("path/to/file.md"))
        
        # Should ignore
        assert not monitor._should_process_file(Path(".hidden.md"))
        assert not monitor._should_process_file(Path("__pycache__/file.md"))
        assert not monitor._should_process_file(Path("test.py"))
        assert not monitor._should_process_file(Path("test"))
    
    @pytest.mark.asyncio
    async def test_handle_file_event_created(self, monitor, mock_event_bus):
        """Test handling file creation event."""
        event = FileEvent(
            type="created",
            path=Path("test.md"),
            is_directory=False,
        )
        
        await monitor._handle_file_event(event)
        
        mock_event_bus.publish.assert_called_once()
        published_event = mock_event_bus.publish.call_args[0][0]
        assert published_event.type == EventType.FILE_CREATED
        assert published_event.data["path"] == "test.md"
    
    @pytest.mark.asyncio
    async def test_handle_file_event_modified(self, monitor, mock_event_bus):
        """Test handling file modification event."""
        event = FileEvent(
            type="modified",
            path=Path("test.md"),
            is_directory=False,
        )
        
        await monitor._handle_file_event(event)
        
        published_event = mock_event_bus.publish.call_args[0][0]
        assert published_event.type == EventType.FILE_MODIFIED
    
    @pytest.mark.asyncio
    async def test_handle_file_event_deleted(self, monitor, mock_event_bus):
        """Test handling file deletion event."""
        event = FileEvent(
            type="deleted",
            path=Path("test.md"),
            is_directory=False,
        )
        
        await monitor._handle_file_event(event)
        
        published_event = mock_event_bus.publish.call_args[0][0]
        assert published_event.type == EventType.FILE_DELETED
    
    @pytest.mark.asyncio
    async def test_handle_file_event_moved(self, monitor, mock_event_bus):
        """Test handling file move event."""
        event = FileEvent(
            type="moved",
            path=Path("new.md"),
            is_directory=False,
            old_path=Path("old.md"),
        )
        
        await monitor._handle_file_event(event)
        
        published_event = mock_event_bus.publish.call_args[0][0]
        assert published_event.type == EventType.FILE_MOVED
        assert published_event.data["old_path"] == "old.md"
        assert published_event.data["new_path"] == "new.md"
    
    @pytest.mark.asyncio
    async def test_threshold_detection(self, monitor, mock_event_bus, temp_dir):
        """Test file growth threshold detection."""
        # Create a test file
        test_file = temp_dir / "growing.md"
        test_file.write_text("Initial content\n")
        
        # Set threshold
        monitor.set_threshold(
            ChangeThreshold(
                lines_per_hour=10,
                check_interval=timedelta(seconds=0.1),
            )
        )
        
        # Simulate rapid file growth
        with patch.object(monitor, '_calculate_growth_rate', return_value=50.0):
            event = FileEvent(
                type="modified",
                path=test_file,
                is_directory=False,
                statistics=FileStatistics(
                    size=1000,
                    line_count=100,
                    last_modified=datetime.now(),
                    growth_rate=50.0,
                ),
            )
            
            await monitor._handle_file_event(event)
            
            # Should publish threshold exceeded event
            calls = mock_event_bus.publish.call_args_list
            assert len(calls) == 2  # Modified + threshold exceeded
            
            threshold_event = calls[1][0][0]
            assert threshold_event.type == EventType.FILE_THRESHOLD_EXCEEDED
            assert threshold_event.data["growth_rate"] == 50.0
    
    def test_get_file_statistics(self, monitor, temp_dir):
        """Test getting file statistics."""
        # Create test file
        test_file = temp_dir / "test.md"
        content = "Line 1\nLine 2\nLine 3\n"
        test_file.write_text(content)
        
        stats = monitor._get_file_statistics(test_file)
        
        assert stats.size == len(content)
        assert stats.line_count == 3
        assert isinstance(stats.last_modified, datetime)
    
    def test_calculate_growth_rate(self, monitor):
        """Test growth rate calculation."""
        now = datetime.now()
        
        # Previous stats
        old_stats = FileStatistics(
            size=100,
            line_count=10,
            last_modified=now - timedelta(hours=1),
        )
        
        # Current stats
        new_stats = FileStatistics(
            size=200,
            line_count=20,
            last_modified=now,
        )
        
        # Store old stats
        monitor._file_stats[Path("test.md")] = old_stats
        
        # Calculate growth rate
        rate = monitor._calculate_growth_rate(Path("test.md"), new_stats)
        
        # Should be ~10 lines per hour
        assert abs(rate - 10.0) < 0.1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, monitor, mock_event_bus):
        """Test error handling in file events."""
        # Create event with invalid path
        event = FileEvent(
            type="created",
            path=Path("/nonexistent/path/file.md"),
            is_directory=False,
        )
        
        with patch.object(monitor, '_get_file_statistics', side_effect=Exception("Test error")):
            # Should not raise exception
            await monitor._handle_file_event(event)
            
            # Should still publish event
            mock_event_bus.publish.assert_called_once()
    
    def test_metrics_collection(self, monitor):
        """Test metrics are collected properly."""
        # Get metrics
        metrics = monitor.get_metrics()
        
        assert "files_monitored" in metrics
        assert "events_processed" in metrics
        assert "errors" in metrics
        assert "last_event_time" in metrics
        
        # Initially zero
        assert metrics["files_monitored"] == 0
        assert metrics["events_processed"] == 0
        assert metrics["errors"] == 0


class TestChangeThreshold:
    """Test ChangeThreshold functionality."""
    
    def test_threshold_creation(self):
        """Test creating a change threshold."""
        threshold = ChangeThreshold(
            lines_per_hour=100,
            check_interval=timedelta(minutes=5),
        )
        
        assert threshold.lines_per_hour == 100
        assert threshold.check_interval == timedelta(minutes=5)
    
    def test_threshold_defaults(self):
        """Test default threshold values."""
        threshold = ChangeThreshold(lines_per_hour=50)
        
        assert threshold.lines_per_hour == 50
        assert threshold.check_interval == timedelta(minutes=1)