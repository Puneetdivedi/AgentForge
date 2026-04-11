"""Enhanced agent base classes with industry-level practices"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncGenerator
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

from app.core.logging import get_logger
from app.core.monitoring import PerformanceMonitor
from app.core.exceptions import AgentInitializationError, AgentError


class AgentStatus(str, Enum):
    """Agent lifecycle status"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    ERROR = "error"


class AgentConfig(BaseModel):
    """Enhanced agent configuration with validation"""
    
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        regex="^[a-z0-9_-]+$",
        description="Unique agent identifier"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable agent name"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Agent description"
    )
    model: str = Field(
        default="gpt-4",
        description="LLM model to use"
    )
    persona: Optional[str] = Field(
        default=None,
        description="Persona configuration"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Available tools for agent"
    )
    memory_enabled: bool = Field(
        default=True,
        description="Enable conversation memory"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=10000,
        description="Max tokens per response"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Processing timeout"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Max retry attempts"
    )
    version: str = Field(
        default="1.0.0",
        description="Agent version"
    )
    enabled: bool = Field(
        default=True,
        description="Agent enabled status"
    )
    
    class Config:
        validate_assignment = True
        use_enum_values = True


class Message(BaseModel):
    """Enhanced message structure"""
    
    role: str = Field(
        ...,
        regex="^(user|assistant|system)$",
        description="Message role"
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "role": "user",
                "content": "What is the capital of France?",
                "timestamp": "2026-04-11T10:30:00Z"
            }
        }


class AgentContext:
    """Enhanced context passed to agents with better state management"""
    
    def __init__(
        self,
        user_id: str,
        session_id: str,
        conversation_history: Optional[List[Message]] = None,
        memory: Optional[Dict[str, Any]] = None,
        tools_available: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_history = conversation_history or []
        self.memory = memory or {}
        self.tools_available = tools_available or []
        self.request_id = request_id
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
    
    def add_message(self, message: Message):
        """Add message to conversation history"""
        self.conversation_history.append(message)
    
    def get_recent_messages(self, count: int = 5) -> List[Message]:
        """Get recent messages"""
        return self.conversation_history[-count:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "conversation_history": [m.dict() for m in self.conversation_history],
            "memory": self.memory,
            "tools_available": self.tools_available,
            "request_id": self.request_id,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    Base class for all agents with lifecycle management and monitoring.
    
    Provides standardized interface for agent implementation with:
    - Lifecycle management (initialize, shutdown)
    - Error handling and retries
    - Performance monitoring
    - Structured logging
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = get_logger(f"agent.{config.agent_id}")
        self.status = AgentStatus.UNINITIALIZED
        self._lock = asyncio.Lock()
        self._initialization_error: Optional[Exception] = None
    
    async def initialize(self) -> None:
        """
        Initialize agent and validate configuration.
        
        Must be called before using the agent.
        
        Raises:
            AgentInitializationError: If initialization fails
        """
        async with self._lock:
            if self.status != AgentStatus.UNINITIALIZED:
                self.logger.warning(
                    f"Agent already initialized: {self.config.agent_id}",
                    extra={"agent_id": self.config.agent_id, "status": self.status}
                )
                return
            
            self.status = AgentStatus.INITIALIZING
            
            try:
                with PerformanceMonitor.track_operation(
                    f"agent_init.{self.config.agent_id}"
                ):
                    self.logger.info(
                        f"Initializing agent: {self.config.agent_id}",
                        extra={"agent_id": self.config.agent_id}
                    )
                    
                    # Validate configuration
                    await self._validate_config()
                    
                    # Call implementation-specific initialization
                    await self._initialize()
                    
                    self.status = AgentStatus.READY
                    self.logger.info(
                        f"Agent initialized successfully: {self.config.agent_id}",
                        extra={"agent_id": self.config.agent_id}
                    )
            
            except Exception as e:
                self.status = AgentStatus.ERROR
                self._initialization_error = e
                self.logger.error(
                    f"Agent initialization failed: {self.config.agent_id}",
                    extra={"agent_id": self.config.agent_id, "error": str(e)},
                    exc_info=True
                )
                raise AgentInitializationError(
                    agent_id=self.config.agent_id,
                    reason=str(e),
                    cause=e
                )
    
    async def shutdown(self) -> None:
        """
        Shutdown agent and cleanup resources.
        
        Safe to call multiple times.
        """
        async with self._lock:
            if self.status == AgentStatus.SHUTDOWN:
                return
            
            self.status = AgentStatus.SHUTTING_DOWN
            
            try:
                self.logger.info(
                    f"Shutting down agent: {self.config.agent_id}",
                    extra={"agent_id": self.config.agent_id}
                )
                
                # Call implementation-specific shutdown
                await self._shutdown()
                
                self.status = AgentStatus.SHUTDOWN
                self.logger.info(
                    f"Agent shutdown successful: {self.config.agent_id}",
                    extra={"agent_id": self.config.agent_id}
                )
            
            except Exception as e:
                self.logger.error(
                    f"Agent shutdown error: {self.config.agent_id}",
                    extra={"agent_id": self.config.agent_id, "error": str(e)},
                    exc_info=True
                )
    
    async def process(
        self,
        message: str,
        context: AgentContext,
        retry_count: int = 0
    ) -> str:
        """
        Process a message and return response with retry logic.
        
        Args:
            message: User message
            context: Agent context
            retry_count: Current retry attempt
        
        Returns:
            str: Agent response
        
        Raises:
            AgentError: If processing fails
        """
        if self.status != AgentStatus.READY:
            raise AgentError(
                message=f"Agent not ready: {self.status}",
                agent_id=self.config.agent_id
            )
        
        self.status = AgentStatus.BUSY
        
        try:
            with PerformanceMonitor.track_operation(
                f"agent_process.{self.config.agent_id}"
            ):
                self.logger.info(
                    f"Processing message: {self.config.agent_id}",
                    extra={
                        "agent_id": self.config.agent_id,
                        "session_id": context.session_id,
                        "request_id": context.request_id
                    }
                )
                
                # Call implementation-specific processing
                response = await self._process(message, context)
                
                self.status = AgentStatus.READY
                return response
        
        except Exception as e:
            # Retry logic
            if retry_count < self.config.max_retries:
                self.logger.warning(
                    f"Processing failed, retrying: {self.config.agent_id}",
                    extra={
                        "agent_id": self.config.agent_id,
                        "retry": retry_count + 1,
                        "error": str(e)
                    }
                )
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.process(message, context, retry_count + 1)
            
            self.status = AgentStatus.DEGRADED
            self.logger.error(
                f"Processing failed after retries: {self.config.agent_id}",
                extra={"agent_id": self.config.agent_id, "error": str(e)},
                exc_info=True
            )
            raise AgentError(
                message=f"Agent processing failed: {str(e)}",
                agent_id=self.config.agent_id
            )
    
    @abstractmethod
    async def _process(self, message: str, context: AgentContext) -> str:
        """
        Implementation-specific message processing.
        
        Args:
            message: User message
            context: Agent context
        
        Returns:
            str: Agent response
        """
        pass
    
    async def _initialize(self) -> None:
        """Implementation-specific initialization (optional override)"""
        pass
    
    async def _shutdown(self) -> None:
        """Implementation-specific shutdown (optional override)"""
        pass
    
    async def _validate_config(self) -> None:
        """Validate agent configuration"""
        if not self.config.enabled:
            raise ValueError("Agent is disabled in configuration")
        
        if not self.config.name:
            raise ValueError("Agent name is required")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.config.agent_id,
            "status": self.status.value,
            "name": self.config.name,
            "version": self.config.version,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager for agent lifecycle"""
        await self.initialize()
        try:
            yield
        finally:
            await self.shutdown()


class GeneralAgent(BaseAgent):
    """General purpose conversational agent implementation"""
    
    async def _initialize(self) -> None:
        """Initialize general agent"""
        self.logger.info(
            f"Initializing General Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _shutdown(self) -> None:
        """Shutdown general agent"""
        self.logger.info(
            f"Shutting down General Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _process(self, message: str, context: AgentContext) -> str:
        """Process message with general agent"""
        # Simulate LLM processing
        await asyncio.sleep(0.1)
        
        return f"General Agent Response: {message}"


class RAGAgent(BaseAgent):
    """RAG (Retrieval Augmented Generation) agent implementation"""
    
    async def _initialize(self) -> None:
        """Initialize RAG agent"""
        self.logger.info(
            f"Initializing RAG Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _shutdown(self) -> None:
        """Shutdown RAG agent"""
        self.logger.info(
            f"Shutting down RAG Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _process(self, message: str, context: AgentContext) -> str:
        """Process message with RAG agent"""
        # Simulate retrieval + generation
        await asyncio.sleep(0.2)
        
        return f"RAG Agent Response (with knowledge base): {message}"


class SQLAgent(BaseAgent):
    """SQL query agent implementation"""
    
    async def _initialize(self) -> None:
        """Initialize SQL agent"""
        self.logger.info(
            f"Initializing SQL Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _shutdown(self) -> None:
        """Shutdown SQL agent"""
        self.logger.info(
            f"Shutting down SQL Agent: {self.config.agent_id}",
            extra={"agent_id": self.config.agent_id}
        )
    
    async def _process(self, message: str, context: AgentContext) -> str:
        """Process message with SQL agent"""
        # Simulate SQL query execution
        await asyncio.sleep(0.15)
        
        return f"SQL Agent Response (database query): {message}"
