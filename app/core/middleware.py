"""Middleware and request/response handling"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging
from typing import Callable, Optional
from contextlib import asynccontextmanager
import uuid

from app.core.logging import get_logger
from app.core.monitoring import RequestContext, PerformanceMonitor
from app.core.exceptions import AppException


logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """Middleware for structured request/response logging"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        # Generate unique request ID
        request_id = request.headers.get(
            "X-Request-ID",
            f"req_{uuid.uuid4().hex[:12]}"
        )
        
        # Create request context
        request_context = RequestContext(
            request_id=request_id,
            user_id=request.headers.get("X-User-ID"),
            session_id=request.headers.get("X-Session-ID"),
            source=request.headers.get("X-Source", "api")
        )
        
        # Store in request state for later use
        request.state.request_context = request_context
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params),
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": elapsed,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        elapsed = (time.time() - start_time) * 1000
        
        # Log response
        self.logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed
            }
        )
        
        return response


class ErrorHandlingMiddleware:
    """Middleware for standardized error handling"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Handle errors and return standardized responses"""
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            # Handle application exceptions
            request_id = getattr(
                request.state,
                "request_id",
                f"req_{uuid.uuid4().hex[:12]}"
            )
            
            self.logger.warning(
                f"Application error: {e.error_code}",
                extra={
                    "request_id": request_id,
                    "error_code": e.error_code.value,
                    "status_code": e.status_code,
                    "message": e.message
                }
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error_code": e.error_code.value,
                    "message": e.message,
                    "request_id": request_id,
                    "details": e.details
                }
            )
        
        except Exception as e:
            # Handle unexpected errors
            request_id = getattr(
                request.state,
                "request_id",
                f"req_{uuid.uuid4().hex[:12]}"
            )
            
            self.logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "request_id": request_id
                }
            )


class RateLimitMiddleware:
    """Middleware for rate limiting"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count)]}
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Initialize or get request history
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old entries
        self.requests[client_ip] = [
            (timestamp, count)
            for timestamp, count in self.requests[client_ip]
            if current_time - timestamp < self.window_seconds
        ]
        
        # Check rate limit
        total_requests = sum(count for _, count in self.requests[client_ip])
        
        if total_requests >= self.max_requests:
            self.logger.warning(
                f"Rate limit exceeded: {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "requests": total_requests,
                    "limit": self.max_requests
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds} seconds"
                }
            )
        
        # Record request
        self.requests[client_ip].append((current_time, 1))
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.max_requests - total_requests - 1
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )
        
        return response


class CompressionMiddleware:
    """Middleware for response compression"""
    
    def __init__(self, app, min_size: int = 1000):
        self.app = app
        self.min_size = min_size
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Compress response if needed"""
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response
        
        # Note: Real compression would be handled by uvicorn
        # This is just a placeholder for the middleware pattern
        
        return response


class SecurityHeadersMiddleware:
    """Middleware for adding security headers"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class CorrelationIdMiddleware:
    """Middleware for correlation ID tracking"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to requests"""
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            f"cor_{uuid.uuid4().hex[:12]}"
        )
        
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


def register_middleware(app):
    """Register all middleware with the FastAPI app"""
    # Note: Middleware is applied in reverse order (last added is first executed)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CompressionMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
