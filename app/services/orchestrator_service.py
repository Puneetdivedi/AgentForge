"""Multi-agent orchestrator"""
from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Agent routing strategies"""
    INTENT = "intent"  # Route based on intent detection
    RULE_BASED = "rule_based"  # Route based on rules
    ML_BASED = "ml_based"  # Route based on ML model
    DIRECT = "direct"  # Direct agent selection


class OrchestratorConfig:
    """Orchestrator configuration"""
    
    def __init__(self, 
                 routing_strategy: RoutingStrategy = RoutingStrategy.RULE_BASED,
                 default_agent: str = "general",
                 timeout: int = 30):
        self.routing_strategy = routing_strategy
        self.default_agent = default_agent
        self.timeout = timeout


class Orchestrator:
    """Multi-agent orchestrator for routing and coordination"""
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
    
    async def route_query(self, 
                         query: str, 
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Route query to appropriate agent
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Agent ID to handle the query
        """
        context = context or {}
        
        if self.config.routing_strategy == RoutingStrategy.DIRECT:
            return context.get("agent_id", self.config.default_agent)
        
        if self.config.routing_strategy == RoutingStrategy.RULE_BASED:
            return self._route_by_rules(query, context)
        
        if self.config.routing_strategy == RoutingStrategy.INTENT:
            return await self._route_by_intent(query, context)
        
        return self.config.default_agent
    
    def _route_by_rules(self, query: str, context: Dict[str, Any]) -> str:
        """Route based on predefined rules"""
        query_lower = query.lower()
        
        # SQL queries
        if any(keyword in query_lower for keyword in ["select", "where", "group by", "join"]):
            return "sql"
        
        # RAG queries
        if any(keyword in query_lower for keyword in ["search", "find", "retrieve", "lookup"]):
            return "rag"
        
        # Default to general agent
        return "general"
    
    async def _route_by_intent(self, query: str, context: Dict[str, Any]) -> str:
        """Route based on intent detection"""
        # This would use an intent detection model
        # For now, fall back to rule-based
        return self._route_by_rules(query, context)
    
    async def orchestrate(self, 
                         query: str,
                         agent_registry,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Orchestrate query execution across agents
        
        Args:
            query: User query
            agent_registry: Registry of available agents
            context: Additional context
            
        Returns:
            Response from the appropriate agent
        """
        # Route to appropriate agent
        agent_id = await self.route_query(query, context)
        
        logger.info(f"Routing query to agent: {agent_id}")
        
        # Get agent instance
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent not found: {agent_id}, using default")
            agent = agent_registry.get_agent(self.config.default_agent)
        
        # Create agent context
        from app.agents.base import AgentContext, Message
        agent_context = AgentContext(
            user_id=context.get("user_id", "unknown") if context else "unknown",
            session_id=context.get("session_id", "unknown") if context else "unknown",
            memory=context.get("memory", {}) if context else {}
        )
        
        # Execute agent
        try:
            response = await agent.process(query, agent_context)
            return response
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise
