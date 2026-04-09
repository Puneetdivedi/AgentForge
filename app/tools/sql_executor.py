"""SQL execution tool"""
from typing import List, Dict, Any
from app.tools.registry import BaseTool
import logging

logger = logging.getLogger(__name__)


class SQLExecutionTool(BaseTool):
    """Tool for executing SQL queries"""
    
    def __init__(self, database_connection):
        super().__init__(
            name="execute_sql",
            description="Execute SQL queries against the database"
        )
        self.db = database_connection
    
    async def execute(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute SQL query
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results
        """
        logger.info(f"Executing SQL query")
        
        # Validate query
        if not self._is_safe_query(query):
            raise ValueError("Query contains potentially dangerous SQL")
        
        results = await self.db.execute(query)
        
        return results
    
    @staticmethod
    def _is_safe_query(query: str) -> bool:
        """
        Validate SQL query for safety
        
        Args:
            query: SQL query
            
        Returns:
            True if query is safe
        """
        dangerous_keywords = ["drop", "delete", "truncate", "alter"]
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True
