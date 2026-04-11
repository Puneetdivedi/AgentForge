"""Monitoring, observability, and metrics utilities"""
import time
import uuid
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
from contextlib import contextmanager
import logging
from enum import Enum

from app.core.logging import get_logger


class MetricType(str, Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class Metric:
    """Simple metric tracking"""
    
    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = ""
    ):
        self.name = name
        self.metric_type = metric_type
        self.description = description
        self.unit = unit
        self.value = 0
        self.values: list[float] = []
    
    def increment(self, amount: float = 1):
        """Increment counter"""
        self.value += amount
    
    def set(self, value: float):
        """Set gauge value"""
        self.value = value
    
    def record(self, value: float):
        """Record histogram value"""
        self.values.append(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "timestamp": datetime.utcnow().isoformat()
        }


class MetricsCollector:
    """Centralized metrics collection"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics: Dict[str, Metric] = {}
        return cls._instance
    
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = ""
    ) -> Metric:
        """Register a new metric"""
        if name in self.metrics:
            return self.metrics[name]
        
        metric = Metric(name, metric_type, description, unit)
        self.metrics[name] = metric
        return metric
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name"""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics"""
        return {
            name: metric.to_dict()
            for name, metric in self.metrics.items()
        }
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    logger = get_logger(__name__)
    metrics = MetricsCollector()
    
    @staticmethod
    @contextmanager
    def track_operation(
        operation_name: str,
        log_details: bool = True,
        warn_threshold_ms: int = 1000
    ):
        """Context manager for tracking operation performance"""
        start_time = time.time()
        start_ms = time.perf_counter() * 1000
        
        try:
            yield
        except Exception as e:
            elapsed_ms = (time.perf_counter() * 1000) - start_ms
            PerformanceMonitor.logger.error(
                f"Operation failed after {elapsed_ms:.2f}ms",
                extra={
                    "operation": operation_name,
                    "elapsed_ms": elapsed_ms,
                    "error": str(e),
                }
            )
            raise
        else:
            elapsed_ms = (time.perf_counter() * 1000) - start_ms
            
            if log_details:
                log_level = logging.WARNING if elapsed_ms > warn_threshold_ms else logging.INFO
                PerformanceMonitor.logger.log(
                    log_level,
                    f"Operation completed: {operation_name}",
                    extra={
                        "operation": operation_name,
                        "elapsed_ms": elapsed_ms,
                        "slow": elapsed_ms > warn_threshold_ms,
                    }
                )
            
            # Record metric
            metric = PerformanceMonitor.metrics.register_metric(
                f"operation.{operation_name}",
                MetricType.HISTOGRAM,
                f"Duration of {operation_name}",
                "ms"
            )
            metric.record(elapsed_ms)
    
    @staticmethod
    def track_function(warn_threshold_ms: int = 1000):
        """Decorator for tracking function performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_name = f"{func.__module__}.{func.__name__}"
                with PerformanceMonitor.track_operation(
                    operation_name,
                    warn_threshold_ms=warn_threshold_ms
                ):
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                operation_name = f"{func.__module__}.{func.__name__}"
                with PerformanceMonitor.track_operation(
                    operation_name,
                    warn_threshold_ms=warn_threshold_ms
                ):
                    return func(*args, **kwargs)
            
            # Return appropriate wrapper
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator


class RequestContext:
    """Request context for tracing and logging"""
    
    def __init__(
        self,
        request_id: str = None,
        user_id: str = None,
        session_id: str = None,
        source: str = "api"
    ):
        self.request_id = request_id or self._generate_id()
        self.user_id = user_id
        self.session_id = session_id
        self.source = source
        self.start_time = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique request ID"""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    def get_duration_ms(self) -> float:
        """Get duration since request start in milliseconds"""
        elapsed = datetime.utcnow() - self.start_time
        return elapsed.total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "source": self.source,
            "duration_ms": self.get_duration_ms(),
            "metadata": self.metadata
        }


class DistributedTracing:
    """Distributed tracing utilities"""
    
    logger = get_logger(__name__)
    
    @staticmethod
    def create_span(
        operation_name: str,
        attributes: Dict[str, Any] = None
    ):
        """Create a span for distributed tracing"""
        span_id = f"span_{uuid.uuid4().hex[:12]}"
        
        DistributedTracing.logger.info(
            f"Span started: {operation_name}",
            extra={
                "span_id": span_id,
                "operation": operation_name,
                "attributes": attributes or {}
            }
        )
        
        return span_id
    
    @staticmethod
    def record_event(
        span_id: str,
        event_name: str,
        attributes: Dict[str, Any] = None
    ):
        """Record an event in a span"""
        DistributedTracing.logger.debug(
            f"Event in span: {event_name}",
            extra={
                "span_id": span_id,
                "event": event_name,
                "attributes": attributes or {}
            }
        )


class ServiceHealth:
    """Service health status tracking"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.services_status: Dict[str, Dict[str, Any]] = {}
        self.logger = get_logger(__name__)
    
    def update_service_status(
        self,
        service_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Update service status"""
        self.services_status[service_name] = {
            "status": status,
            "details": details or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"Service status updated: {service_name}",
            extra={
                "service": service_name,
                "status": status
            }
        )
    
    def get_overall_status(self) -> str:
        """Get overall system status"""
        if not self.services_status:
            return "healthy"
        
        statuses = [s["status"] for s in self.services_status.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        return "healthy"
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "status": self.get_overall_status(),
            "uptime_seconds": int(uptime_seconds),
            "services": self.services_status,
            "timestamp": datetime.utcnow().isoformat()
        }
