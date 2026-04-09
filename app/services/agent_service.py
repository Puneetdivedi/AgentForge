"""Agent service for managing agent lifecycle"""
import yaml
import os
from typing import Dict, List, Optional
import logging
from app.agents import AgentRegistry, AgentConfig

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agent lifecycle and configuration"""
    
    def __init__(self, config_dir: str = "config/agents"):
        self.config_dir = config_dir
        self.registry = AgentRegistry
    
    async def load_agents_from_yaml(self) -> Dict[str, AgentConfig]:
        """Load all agents from YAML configuration files"""
        agents = {}
        
        if not os.path.exists(self.config_dir):
            logger.warning(f"Config directory not found: {self.config_dir}")
            return agents
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.config_dir, filename)
                
                try:
                    with open(filepath, "r") as f:
                        config_dict = yaml.safe_load(f)
                    
                    agent_config = AgentConfig(**config_dict)
                    agents[agent_config.agent_id] = agent_config
                    logger.info(f"Loaded agent config: {agent_config.agent_id}")
                
                except Exception as e:
                    logger.error(f"Failed to load agent config from {filepath}: {e}")
        
        return agents
    
    async def initialize_agents(self) -> None:
        """Initialize all agents from configuration"""
        logger.info("Initializing agents")
        
        agent_configs = await self.load_agents_from_yaml()
        
        for agent_id, config in agent_configs.items():
            try:
                await self.registry.register_agent(config)
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_id}: {e}")
    
    async def get_agent_status(self) -> Dict[str, str]:
        """Get status of all agents"""
        agents = self.registry.get_all_agents()
        status = {agent_id: "running" for agent_id in agents.keys()}
        return status
