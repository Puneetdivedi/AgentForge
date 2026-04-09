"""Tool registry and base classes"""
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional, Callable
import logging
import json

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        pass
    
    def to_dict(self) -> Dict[str, str]:
        """Convert tool to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description
        }


class ToolRegistry:
    """Registry for all available tools"""
    
    _tools: Dict[str, BaseTool] = {}
    
    @classmethod
    def register_tool(cls, tool: BaseTool) -> None:
        """
        Register a tool
        
        Args:
            tool: Tool instance
        """
        cls._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    @classmethod
    def get_tool(cls, tool_name: str) -> Optional[BaseTool]:
        """
        Get tool by name
        
        Args:
            tool_name: Tool name
            
        Returns:
            Tool instance or None
        """
        return cls._tools.get(tool_name)
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, BaseTool]:
        """Get all registered tools"""
        return cls._tools.copy()
    
    @classmethod
    def get_available_tools(cls) -> list:
        """Get list of available tools for LLM"""
        tools = []
        for tool_name, tool in cls._tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            })
        return tools
    
    @classmethod
    async def execute_tool(cls, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool
        
        Args:
            tool_name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        tool = cls.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        logger.info(f"Executing tool: {tool_name}")
        result = await tool.execute(**kwargs)
        return result
