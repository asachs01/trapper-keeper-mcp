"""Base classes and protocols for Trapper Keeper MCP components."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import structlog

from .types import Document, ExtractedContent, ProcessingResult, EventType, Event

logger = structlog.get_logger()

T = TypeVar("T", bound="Component")


class EventBus:
    """Async event bus for component communication."""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[asyncio.Queue]] = {}
        self._logger = logger.bind(component="EventBus")
        
    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if event.type in self._subscribers:
            self._logger.debug("publishing_event", event_type=event.type, data=event.data)
            for queue in self._subscribers[event.type]:
                await queue.put(event)
                
    def subscribe(self, event_type: EventType) -> asyncio.Queue:
        """Subscribe to events of a specific type."""
        queue = asyncio.Queue()
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(queue)
        self._logger.debug("subscribed_to_event", event_type=event_type)
        return queue
        
    def unsubscribe(self, event_type: EventType, queue: asyncio.Queue) -> None:
        """Unsubscribe from events."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(queue)
            

class Component(ABC):
    """Base class for all Trapper Keeper components."""
    
    def __init__(self, name: str, event_bus: Optional[EventBus] = None):
        self.name = name
        self.event_bus = event_bus or EventBus()
        self._logger = logger.bind(component=name)
        self._initialized = False
        self._running = False
        
    async def initialize(self) -> None:
        """Initialize the component."""
        if self._initialized:
            return
            
        self._logger.info("initializing_component")
        await self._initialize()
        self._initialized = True
        self._logger.info("component_initialized")
        
    async def start(self) -> None:
        """Start the component."""
        if not self._initialized:
            await self.initialize()
            
        if self._running:
            return
            
        self._logger.info("starting_component")
        self._running = True
        await self._start()
        self._logger.info("component_started")
        
    async def stop(self) -> None:
        """Stop the component."""
        if not self._running:
            return
            
        self._logger.info("stopping_component")
        self._running = False
        await self._stop()
        self._logger.info("component_stopped")
        
    async def publish_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Publish an event to the event bus."""
        event = Event(
            type=event_type,
            source=self.name,
            data=data,
            timestamp=datetime.utcnow()
        )
        await self.event_bus.publish(event)
        
    def subscribe_to_event(self, event_type: EventType) -> asyncio.Queue:
        """Subscribe to events of a specific type."""
        return self.event_bus.subscribe(event_type)
        
    @abstractmethod
    async def _initialize(self) -> None:
        """Component-specific initialization logic."""
        pass
        
    @abstractmethod
    async def _start(self) -> None:
        """Component-specific start logic."""
        pass
        
    @abstractmethod
    async def _stop(self) -> None:
        """Component-specific stop logic."""
        pass


class Plugin(Protocol):
    """Protocol for Trapper Keeper plugins."""
    
    name: str
    version: str
    description: str
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        ...
        
    async def process(self, document: Document) -> ProcessingResult:
        """Process a document and return results."""
        ...
        
    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        ...


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._logger = logger.bind(component="PluginRegistry")
        
    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin {plugin.name} already registered")
            
        self._plugins[plugin.name] = plugin
        self._logger.info("plugin_registered", name=plugin.name, version=plugin.version)
        
    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            self._logger.info("plugin_unregistered", name=name)
            
    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
        
    def list_plugins(self) -> List[Plugin]:
        """List all registered plugins."""
        return list(self._plugins.values())


class Processor(Component):
    """Base class for document processors."""
    
    @abstractmethod
    async def process(self, document: Document) -> ProcessingResult:
        """Process a document and return results."""
        pass
        
    async def process_batch(self, documents: List[Document]) -> List[ProcessingResult]:
        """Process multiple documents concurrently."""
        tasks = [self.process(doc) for doc in documents]
        return await asyncio.gather(*tasks)


class Monitor(Component):
    """Base class for file/directory monitors."""
    
    @abstractmethod
    async def watch(self, path: Path) -> None:
        """Start watching a path for changes."""
        pass
        
    @abstractmethod
    async def unwatch(self, path: Path) -> None:
        """Stop watching a path."""
        pass
        
    @abstractmethod
    def get_watched_paths(self) -> List[Path]:
        """Get list of currently watched paths."""
        pass


class Parser(Component):
    """Base class for document parsers."""
    
    @abstractmethod
    async def parse(self, content: str, path: Optional[Path] = None) -> Document:
        """Parse content into a Document."""
        pass
        
    @abstractmethod
    def can_parse(self, path: Path) -> bool:
        """Check if the parser can handle a file."""
        pass


class Extractor(Component):
    """Base class for content extractors."""
    
    @abstractmethod
    async def extract(self, document: Document) -> List[ExtractedContent]:
        """Extract content from a document."""
        pass
        
    @abstractmethod
    def get_supported_categories(self) -> List[str]:
        """Get list of supported extraction categories."""
        pass


class Organizer(Component):
    """Base class for document organizers."""
    
    @abstractmethod
    async def organize(self, contents: List[ExtractedContent]) -> Dict[str, List[ExtractedContent]]:
        """Organize extracted contents into categories."""
        pass
        
    @abstractmethod
    async def save(self, organized_content: Dict[str, List[ExtractedContent]], output_dir: Path) -> None:
        """Save organized content to output directory."""
        pass