"""Custom exception classes for AgentForge application"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API responses"""
    # Validation errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    CONFLICT = "CONFLICT"
    
    # Agent errors (4xx)
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_NOT_INITIALIZED = "AGENT_NOT_INITIALIZED"
    INVALID_AGENT_CONFIG = "INVALID_AGENT_CONFIG"
    AGENT_EXECUTION_FAILED = "AGENT_EXECUTION_FAILED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    
    # External service errors (5xx)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    
    # Server errors (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class AppException(Exception):
    """Base application exception"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize AppException
        
        Args:
            message: Human-readable error message
            error_code: Standardized error code
            status_code: HTTP status code
            details: Additional error details
            cause: Original exception that caused this error
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AppException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
        )


class AuthenticationError(AppException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=401,
        )


class AuthorizationError(AppException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHORIZATION_FAILED,
            status_code=403,
        )


class ResourceNotFoundError(AppException):
    """Resource not found exception"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
        )


class RateLimitError(AppException):
    """Rate limit exceeded exception"""
    
    def __init__(
        self,
        limit: int,
        window_seconds: int,
    ):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds} seconds",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={
                "limit": limit,
                "window_seconds": window_seconds,
            },
        )


class AgentError(AppException):
    """Agent-related error exception"""
    
    def __init__(
        self,
        message: str,
        agent_id: str,
        error_code: ErrorCode = ErrorCode.AGENT_EXECUTION_FAILED,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["agent_id"] = agent_id
        
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class AgentNotFoundError(AgentError):
    """Agent not found exception"""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            agent_id=agent_id,
            error_code=ErrorCode.AGENT_NOT_FOUND,
            status_code=404,
        )


class AgentInitializationError(AgentError):
    """Agent initialization error exception"""
    
    def __init__(
        self,
        agent_id: str,
        reason: str,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Failed to initialize agent {agent_id}: {reason}",
            agent_id=agent_id,
            error_code=ErrorCode.AGENT_NOT_INITIALIZED,
            status_code=500,
            details={"reason": reason},
        )
        self.cause = cause


class ExternalServiceError(AppException):
    """External service error exception"""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 502,
    ):
        super().__init__(
            message=f"{service_name} error: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status_code,
            details={"service": service_name},
        )


class DatabaseError(AppException):
    """Database error exception"""
    
    def __init__(
        self,
        message: str,
        operation: str,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=f"Database error during {operation}: {message}",
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=503,
            details={"operation": operation},
            cause=cause,
        )
