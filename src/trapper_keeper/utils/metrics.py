"""Metrics collection for monitoring and observability."""

from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Collects and exposes metrics for Trapper Keeper."""
    
    def __init__(self, enabled: bool = True, port: int = 9090):
        self.enabled = enabled
        self.port = port
        self._logger = logger.bind(component="MetricsCollector")
        
        if self.enabled:
            self._initialize_metrics()
            
    def _initialize_metrics(self):
        """Initialize Prometheus metrics."""
        # Counters
        self.files_processed = Counter(
            'trapper_keeper_files_processed_total',
            'Total number of files processed',
            ['status']  # success, failed
        )
        
        self.events_published = Counter(
            'trapper_keeper_events_published_total',
            'Total number of events published',
            ['event_type']
        )
        
        self.contents_extracted = Counter(
            'trapper_keeper_contents_extracted_total',
            'Total number of content items extracted',
            ['category']
        )
        
        # Histograms
        self.processing_duration = Histogram(
            'trapper_keeper_processing_duration_seconds',
            'Time spent processing files',
            ['file_type']
        )
        
        self.extraction_duration = Histogram(
            'trapper_keeper_extraction_duration_seconds',
            'Time spent extracting content'
        )
        
        self.organization_duration = Histogram(
            'trapper_keeper_organization_duration_seconds',
            'Time spent organizing content'
        )
        
        # Gauges
        self.watched_directories = Gauge(
            'trapper_keeper_watched_directories',
            'Number of directories being watched'
        )
        
        self.processing_queue_size = Gauge(
            'trapper_keeper_processing_queue_size',
            'Number of files in processing queue'
        )
        
        self.active_watchers = Gauge(
            'trapper_keeper_active_watchers',
            'Number of active file watchers'
        )
        
    def start_server(self):
        """Start the Prometheus metrics server."""
        if self.enabled:
            start_http_server(self.port)
            self._logger.info("metrics_server_started", port=self.port)
            
    def record_file_processed(self, success: bool):
        """Record a file processing event."""
        if self.enabled:
            status = "success" if success else "failed"
            self.files_processed.labels(status=status).inc()
            
    def record_event_published(self, event_type: str):
        """Record an event publication."""
        if self.enabled:
            self.events_published.labels(event_type=event_type).inc()
            
    def record_content_extracted(self, category: str):
        """Record content extraction."""
        if self.enabled:
            self.contents_extracted.labels(category=category).inc()
            
    def record_processing_time(self, duration: float, file_type: str):
        """Record file processing duration."""
        if self.enabled:
            self.processing_duration.labels(file_type=file_type).observe(duration)
            
    def record_extraction_time(self, duration: float):
        """Record content extraction duration."""
        if self.enabled:
            self.extraction_duration.observe(duration)
            
    def record_organization_time(self, duration: float):
        """Record content organization duration."""
        if self.enabled:
            self.organization_duration.observe(duration)
            
    def set_watched_directories(self, count: int):
        """Set the number of watched directories."""
        if self.enabled:
            self.watched_directories.set(count)
            
    def set_processing_queue_size(self, size: int):
        """Set the processing queue size."""
        if self.enabled:
            self.processing_queue_size.set(size)
            
    def set_active_watchers(self, count: int):
        """Set the number of active watchers."""
        if self.enabled:
            self.active_watchers.set(count)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(enabled: bool = True, port: int = 9090) -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(enabled, port)
        
    return _metrics_collector