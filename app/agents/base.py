"""Agent base classes and abstractions"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Agent configuration"""
    agent_id: str
    name: str
    description: str
    model: str
    persona: str
    tools: List[str] = []
    memory_enabled: bool = True
    temperature: float = 0.7


class Message(BaseModel):
    """Message structure"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class AgentContext:
    """Context passed to agents"""
    
    def __init__(self, 
                 user_id: str, 
                 session_id: str, 
                 conversation_history: List[Message] = None,
                 memory: Dict[str, Any] = None,
                 tools_available: List[str] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_history = conversation_history or []
        self.memory = memory or {}
        self.tools_available = tools_available or []
        self.metadata = {}


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = logging.getLogger(f"agent.{config.agent_id}")
    
    @abstractmethod
    async def process(self, 
                      message: str, 
                      context: AgentContext) -> str:
        """
        Process a message and return response
        
        Args:
            message: User message
            context: Agent context
            
        Returns:
            Agent response
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown agent"""
        pass
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from persona"""
        # This would load persona from YAML
        return f"You are {self.config.name}. {self.config.description}"


class GeneralAgent(BaseAgent):
    """General purpose conversational agent"""
    
    async def initialize(self) -> None:
        """Initialize general agent"""
        self.logger.info(f"Initializing General Agent: {self.config.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown general agent"""
        self.logger.info(f"Shutting down General Agent: {self.config.agent_id}")
    
    async def process(self, message: str, context: AgentContext) -> str:
        """Process message with general agent"""
        # This will be implemented in the service layer
        self.logger.debug(f"Processing message from user {context.user_id}")
        return "Response from general agent"


class RAGAgent(BaseAgent):
    """Retrieval Augmented Generation agent"""
    
    async def initialize(self) -> None:
        """Initialize RAG agent"""
        self.logger.info(f"Initializing RAG Agent: {self.config.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown RAG agent"""
        self.logger.info(f"Shutting down RAG Agent: {self.config.agent_id}")
    
    async def process(self, message: str, context: AgentContext) -> str:
        """Process message with RAG agent"""
        self.logger.debug(f"Processing message with RAG from user {context.user_id}")
        return "Response from RAG agent"


class SQLAgent(BaseAgent):
    """SQL query execution agent"""
    
    async def initialize(self) -> None:
        """Initialize SQL agent"""
        self.logger.info(f"Initializing SQL Agent: {self.config.agent_id}")
    
    async def shutdown(self) -> None:
        """Shutdown SQL agent"""
        self.logger.info(f"Shutting down SQL Agent: {self.config.agent_id}")
    
    async def process(self, message: str, context: AgentContext) -> str:
        """Process message with SQL agent"""
        self.logger.debug(f"Processing SQL query from user {context.user_id}")
        return "Response from SQL agent"
