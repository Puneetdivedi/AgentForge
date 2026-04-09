"""API calling tool"""
from typing import Dict, Any, Optional
from app.tools.registry import BaseTool
import httpx
import logging

logger = logging.getLogger(__name__)


class APICallerTool(BaseTool):
    """Tool for calling external APIs"""
    
    def __init__(self):
        super().__init__(
            name="call_api",
            description="Call external APIs and retrieve data"
        )
    
    async def execute(self, 
                      url: str, 
                      method: str = "GET", 
                      headers: Optional[Dict[str, str]] = None,
                      payload: Optional[Dict[str, Any]] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Call external API
        
        Args:
            url: API endpoint URL
            method: HTTP method
            headers: Request headers
            payload: Request payload
            
        Returns:
            API response
        """
        logger.info(f"Calling API: {url}")
        
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL")
        
        headers = headers or {}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=payload, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
