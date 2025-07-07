"""Factory for creating document parsers."""

from pathlib import Path
from typing import Dict, Optional, Type

from ..core.base import Parser, EventBus
from ..core.types import DocumentType
from .markdown_parser import MarkdownParser

# Registry of available parsers
PARSER_REGISTRY: Dict[DocumentType, Type[Parser]] = {
    DocumentType.MARKDOWN: MarkdownParser,
}

# File extension to document type mapping
EXTENSION_MAP = {
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
    ".mdown": DocumentType.MARKDOWN,
    ".mkd": DocumentType.MARKDOWN,
    ".txt": DocumentType.TEXT,
    ".json": DocumentType.JSON,
    ".yaml": DocumentType.YAML,
    ".yml": DocumentType.YAML,
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
}


class ParserFactory:
    """Factory for creating document parsers."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._parsers: Dict[DocumentType, Parser] = {}
        
    def get_parser(self, doc_type: DocumentType) -> Optional[Parser]:
        """Get or create a parser for the document type."""
        if doc_type not in PARSER_REGISTRY:
            return None
            
        if doc_type not in self._parsers:
            parser_class = PARSER_REGISTRY[doc_type]
            self._parsers[doc_type] = parser_class(self.event_bus)
            
        return self._parsers[doc_type]
        
    def get_parser_for_file(self, path: Path) -> Optional[Parser]:
        """Get a parser that can handle the file."""
        # Try to determine document type from extension
        ext = path.suffix.lower()
        doc_type = EXTENSION_MAP.get(ext, DocumentType.UNKNOWN)
        
        if doc_type == DocumentType.UNKNOWN:
            # Try each parser to see if it can handle the file
            for parser in self._parsers.values():
                if parser.can_parse(path):
                    return parser
                    
            # Create parsers we haven't tried yet
            for doc_type, parser_class in PARSER_REGISTRY.items():
                if doc_type not in self._parsers:
                    parser = parser_class(self.event_bus)
                    self._parsers[doc_type] = parser
                    if parser.can_parse(path):
                        return parser
                        
            return None
            
        return self.get_parser(doc_type)
        
    async def initialize_all(self) -> None:
        """Initialize all created parsers."""
        for parser in self._parsers.values():
            await parser.initialize()
            
    async def stop_all(self) -> None:
        """Stop all created parsers."""
        for parser in self._parsers.values():
            await parser.stop()


# Global parser factory instance
_parser_factory: Optional[ParserFactory] = None


def get_parser_factory(event_bus: Optional[EventBus] = None) -> ParserFactory:
    """Get or create the global parser factory."""
    global _parser_factory
    
    if _parser_factory is None:
        _parser_factory = ParserFactory(event_bus)
        
    return _parser_factory


def get_parser(path: Path, event_bus: Optional[EventBus] = None) -> Optional[Parser]:
    """Get a parser for a file path."""
    factory = get_parser_factory(event_bus)
    return factory.get_parser_for_file(path)