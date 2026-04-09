"""Agent registry and factory"""
from typing import Dict, Type, Optional
from app.agents.base import (
    BaseAgent, GeneralAgent, RAGAgent, SQLAgent, AgentConfig
)
import logging

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for all available agents"""
    
    _agents: Dict[str, BaseAgent] = {}
    _agent_classes: Dict[str, Type[BaseAgent]] = {
        "general": GeneralAgent,
        "rag": RAGAgent,
        "sql": SQLAgent,
    }
    
    @classmethod
    async def register_agent(cls, config: AgentConfig) -> BaseAgent:
        """
        Register and initialize an agent
        
        Args:
            config: Agent configuration
            
        Returns:
            Initialized agent instance
        """
        agent_type = config.model.split("-")[0].lower()
        agent_class = cls._agent_classes.get(agent_type, GeneralAgent)
        
        agent = agent_class(config)
        await agent.initialize()
        
        cls._agents[config.agent_id] = agent
        logger.info(f"Registered agent: {config.agent_id}")
        
        return agent
    
    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None
        """
        return cls._agents.get(agent_id)
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, BaseAgent]:
        """Get all registered agents"""
        return cls._agents.copy()
    
    @classmethod
    async def deregister_agent(cls, agent_id: str) -> None:
        """
        Deregister and shutdown an agent
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in cls._agents:
            agent = cls._agents[agent_id]
            await agent.shutdown()
            del cls._agents[agent_id]
            logger.info(f"Deregistered agent: {agent_id}")
    
    @classmethod
    async def shutdown_all(cls) -> None:
        """Shutdown all agents"""
        for agent_id in list(cls._agents.keys()):
            await cls.deregister_agent(agent_id)
