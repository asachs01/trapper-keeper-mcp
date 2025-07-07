"""Trapper Keeper MCP - Intelligent document extraction and organization."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.base import Component, Plugin
from .core.types import Document, ExtractedContent, ProcessingResult

__all__ = [
    "Component",
    "Plugin", 
    "Document",
    "ExtractedContent",
    "ProcessingResult",
]