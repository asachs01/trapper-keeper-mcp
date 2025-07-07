"""Core components for Trapper Keeper."""

from .base import Component, Plugin, EventBus, PluginRegistry
from .config import ConfigManager, get_config, get_config_manager
from .types import (
    Document,
    ExtractedContent,
    ProcessingResult,
    ExtractionCategory,
    EventType,
    TrapperKeeperConfig,
)

__all__ = [
    "Component",
    "Plugin",
    "EventBus",
    "PluginRegistry",
    "ConfigManager",
    "get_config",
    "get_config_manager",
    "Document",
    "ExtractedContent",
    "ProcessingResult",
    "ExtractionCategory",
    "EventType",
    "TrapperKeeperConfig",
]