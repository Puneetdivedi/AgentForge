"""Enhanced API schemas with request/response validation"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, conlist
from enum import Enum


class RequestSource(str, Enum):
    """Request source enumeration"""
    API = "api"
    WEB = "web"
    CLI = "cli"


class ChatRequest(BaseModel):
    """Enhanced chat request with validation"""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message"
    )
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex="^[a-z0-9_-]+$",
        description="Target agent ID"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation tracking"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for context"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        max_items=50,
        description="Additional context"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation"
    )
    max_tokens: Optional[int] = Field(
        default=2000,
        ge=1,
        le=10000,
        description="Maximum tokens in response"
    )
    timeout_seconds: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    @validator("message")
    def validate_message(cls, v: str) -> str:
        """Validate message content"""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What is the capital of France?",
                "agent_id": "general_agent",
                "session_id": "sess_123",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
        }


class ChatResponse(BaseModel):
    """Enhanced chat response with metadata"""
    
    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )
    message: str = Field(
        ...,
        description="Response message"
    )
    agent_id: str = Field(
        ...,
        description="Agent that processed the request"
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to process request in milliseconds"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Tokens used by LLM"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the response"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the response (e.g., 'knowledge_base', 'gpt-4')"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_abc123def456",
                "message": "The capital of France is Paris.",
                "agent_id": "general_agent",
                "processing_time_ms": 245,
                "tokens_used": 15,
                "confidence": 0.98,
                "source": "gpt-4",
                "timestamp": "2026-04-11T10:30:00Z"
            }
        }


class AgentResponse(BaseModel):
    """Agent execution response"""
    
    status: str = Field(
        ...,
        description="Execution status (success, error, timeout)"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Execution result"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "request_id": "req_xyz789",
                "details": {"field": "message", "reason": "too short"},
                "timestamp": "2026-04-11T10:30:00Z"
            }
        }


class HealthCheck(BaseModel):
    """Health check response"""
    
    status: str = Field(
        ...,
        description="Service status (healthy, degraded, unhealthy)"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp"
    )
    services: Optional[Dict[str, str]] = Field(
        default=None,
        description="Individual service statuses"
    )
    uptime_seconds: Optional[int] = Field(
        default=None,
        description="Service uptime in seconds"
    )


class AgentListResponse(BaseModel):
    """Agent list response"""
    
    agents: List[Dict[str, Any]] = Field(
        ...,
        description="List of agents",
        min_items=0,
        max_items=100
    )
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of agents"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class PaginationParams(BaseModel):
    """Pagination parameters"""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page"
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Field to sort by"
    )
    sort_order: Optional[str] = Field(
        default="asc",
        regex="^(asc|desc)$",
        description="Sort order"
    )


class ConversationMetadataResponse(BaseModel):
    """Conversation metadata response"""
    
    conversation_id: str = Field(
        ...,
        description="Unique conversation identifier"
    )
    user_id: str = Field(
        ...,
        description="User identifier"
    )
    agent_id: str = Field(
        ...,
        description="Agent identifier"
    )
    message_count: int = Field(
        ...,
        ge=0,
        description="Total messages in conversation"
    )
    created_at: datetime = Field(
        ...,
        description="Conversation creation time"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update time"
    )
    duration_seconds: int = Field(
        ...,
        ge=0,
        description="Conversation duration in seconds"
    )
    status: str = Field(
        ...,
        description="Conversation status (active, archived, closed)"
    )
