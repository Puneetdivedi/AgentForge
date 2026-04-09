"""Request and response schemas"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration"""
    GENERAL = "general"
    RAG = "rag"
    SQL = "sql"
    CUSTOM = "custom"


class ChatRequest(BaseModel):
    """Chat request schema"""
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    agent_type: Optional[AgentType] = Field(default=AgentType.GENERAL, description="Agent type to use")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    use_rag: bool = Field(default=True, description="Enable RAG")
    stream: bool = Field(default=False, description="Enable streaming")
    
    @validator("message")
    def message_not_empty(cls, v: str) -> str:
        """Validate non-empty message"""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class RunAgentRequest(BaseModel):
    """Run agent request schema"""
    agent_id: str = Field(..., description="Agent ID")
    input_data: Dict[str, Any] = Field(default={}, description="Agent input")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout")


class ChatResponse(BaseModel):
    """Chat response schema"""
    user_id: str
    session_id: str
    message: str
    agent_type: AgentType
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response schema"""
    agent_id: str
    output: Dict[str, Any]
    status: str
    execution_time: float
    tokens_used: Optional[Dict[str, int]] = None


class TokenUsage(BaseModel):
    """Token usage schema"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
