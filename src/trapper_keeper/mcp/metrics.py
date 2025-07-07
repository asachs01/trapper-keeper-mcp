"""Metrics and monitoring for MCP server."""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import structlog

logger = structlog.get_logger()


@dataclass
class ToolMetrics:
    """Metrics for a specific tool."""
    
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    last_call_time: Optional[datetime] = None
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_call(self, success: bool, duration: float, error: Optional[str] = None):
        """Record a tool call."""
        self.total_calls += 1
        self.total_duration += duration
        self.last_call_time = datetime.utcnow()
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if error:
                self.error_counts[error] += 1
                
        # Update min/max durations
        if self.min_duration is None or duration < self.min_duration:
            self.min_duration = duration
        if self.max_duration is None or duration > self.max_duration:
            self.max_duration = duration
            
    @property
    def average_duration(self) -> float:
        """Get average call duration."""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration / self.total_calls
        
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "tool_name": self.tool_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": f"{self.success_rate:.2f}%",
            "average_duration": f"{self.average_duration:.3f}s",
            "min_duration": f"{self.min_duration:.3f}s" if self.min_duration else "N/A",
            "max_duration": f"{self.max_duration:.3f}s" if self.max_duration else "N/A",
            "last_call_time": self.last_call_time.isoformat() if self.last_call_time else None,
            "top_errors": dict(self.error_counts.most_common(5)) if self.error_counts else {}
        }


@dataclass
class ServerMetrics:
    """Overall server metrics."""
    
    start_time: datetime = field(default_factory=datetime.utcnow)
    total_requests: int = 0
    active_watchers: int = 0
    processed_files: int = 0
    extracted_contents: int = 0
    
    def uptime_seconds(self) -> float:
        """Get server uptime in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        uptime = self.uptime_seconds()
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        return {
            "start_time": self.start_time.isoformat(),
            "uptime": f"{hours}h {minutes}m",
            "total_requests": self.total_requests,
            "active_watchers": self.active_watchers,
            "processed_files": self.processed_files,
            "extracted_contents": self.extracted_contents,
            "requests_per_minute": self.total_requests / (uptime / 60) if uptime > 0 else 0
        }


class MCPMetricsCollector:
    """Collects and manages metrics for the MCP server."""
    
    def __init__(self):
        self.server_metrics = ServerMetrics()
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        self._logger = logger.bind(component="MCPMetricsCollector")
        
    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration: float,
        error: Optional[str] = None
    ):
        """Record a tool call."""
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolMetrics(tool_name)
            
        self.tool_metrics[tool_name].record_call(success, duration, error)
        self.server_metrics.total_requests += 1
        
        self._logger.info(
            "tool_call_recorded",
            tool=tool_name,
            success=success,
            duration=duration,
            error=error
        )
        
    def update_watcher_count(self, count: int):
        """Update active watcher count."""
        self.server_metrics.active_watchers = count
        
    def increment_processed_files(self):
        """Increment processed files counter."""
        self.server_metrics.processed_files += 1
        
    def add_extracted_contents(self, count: int):
        """Add to extracted contents counter."""
        self.server_metrics.extracted_contents += count
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            "server": self.server_metrics.to_dict(),
            "tools": {
                name: metrics.to_dict()
                for name, metrics in self.tool_metrics.items()
            }
        }
        
    def get_tool_metrics(self, tool_name: str) -> Optional[ToolMetrics]:
        """Get metrics for a specific tool."""
        return self.tool_metrics.get(tool_name)
        
    def reset_tool_metrics(self, tool_name: Optional[str] = None):
        """Reset metrics for a tool or all tools."""
        if tool_name:
            if tool_name in self.tool_metrics:
                self.tool_metrics[tool_name] = ToolMetrics(tool_name)
        else:
            # Reset all tool metrics
            for name in list(self.tool_metrics.keys()):
                self.tool_metrics[name] = ToolMetrics(name)
                
        self._logger.info("metrics_reset", tool=tool_name or "all")


class MetricsContext:
    """Context manager for recording tool metrics."""
    
    def __init__(self, collector: MCPMetricsCollector, tool_name: str):
        self.collector = collector
        self.tool_name = tool_name
        self.start_time = None
        self.success = True
        self.error = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.success = False
            self.error = str(exc_val)
            
        self.collector.record_tool_call(
            self.tool_name,
            self.success,
            duration,
            self.error
        )
        
        # Don't suppress exceptions
        return False
        
    def set_error(self, error: str):
        """Manually set an error."""
        self.success = False
        self.error = error


def format_metrics_report(metrics: Dict[str, Any]) -> str:
    """Format metrics as a human-readable report."""
    lines = [
        "=== Trapper Keeper MCP Server Metrics ===",
        "",
        "Server Status:",
        f"  Uptime: {metrics['server']['uptime']}",
        f"  Total Requests: {metrics['server']['total_requests']}",
        f"  Requests/min: {metrics['server']['requests_per_minute']:.2f}",
        f"  Active Watchers: {metrics['server']['active_watchers']}",
        f"  Processed Files: {metrics['server']['processed_files']}",
        f"  Extracted Contents: {metrics['server']['extracted_contents']}",
        "",
        "Tool Performance:",
    ]
    
    for tool_name, tool_data in metrics['tools'].items():
        lines.extend([
            f"  {tool_name}:",
            f"    Total Calls: {tool_data['total_calls']}",
            f"    Success Rate: {tool_data['success_rate']}",
            f"    Avg Duration: {tool_data['average_duration']}",
            f"    Min/Max: {tool_data['min_duration']} / {tool_data['max_duration']}",
        ])
        
        if tool_data['top_errors']:
            lines.append("    Top Errors:")
            for error, count in tool_data['top_errors'].items():
                lines.append(f"      - {error}: {count}")
                
        lines.append("")
        
    return "\n".join(lines)