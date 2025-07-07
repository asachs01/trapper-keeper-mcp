"""Base class for MCP tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import structlog
from pydantic import BaseModel

from ...core.base import EventBus
from ...core.types import TrapperKeeperConfig


class BaseTool(ABC):
    """Base class for MCP tools."""
    
    def __init__(
        self,
        name: str,
        config: TrapperKeeperConfig,
        event_bus: Optional[EventBus] = None
    ):
        self.name = name
        self.config = config
        self.event_bus = event_bus
        self._logger = structlog.get_logger().bind(tool=name)
        
    @abstractmethod
    async def execute(self, request: BaseModel) -> Dict[str, Any]:
        """Execute the tool with the given request.
        
        Args:
            request: The request model containing tool parameters
            
        Returns:
            Dictionary containing the tool response
        """
        pass
        
    async def validate_request(self, request: BaseModel) -> None:
        """Validate the request before execution.
        
        Args:
            request: The request to validate
            
        Raises:
            ValueError: If the request is invalid
        """
        # Base validation - subclasses can override
        pass
        
    def log_execution(self, request: BaseModel, response: Dict[str, Any], duration: float) -> None:
        """Log tool execution details.
        
        Args:
            request: The request that was executed
            response: The response from execution
            duration: Time taken in seconds
        """
        self._logger.info(
            "tool_executed",
            request=request.dict(),
            response_keys=list(response.keys()),
            duration=duration,
            success=response.get("success", True)
        )