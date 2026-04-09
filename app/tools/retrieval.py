"""Retrieval tool for RAG implementation"""
from typing import List, Dict, Any
from app.tools.registry import BaseTool
import logging

logger = logging.getLogger(__name__)


class RetrievalTool(BaseTool):
    """Tool for retrieving documents from vector database"""
    
    def __init__(self, retriever):
        super().__init__(
            name="retrieve",
            description="Retrieve relevant documents from the knowledge base"
        )
        self.retriever = retriever
    
    async def execute(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve documents
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents
        """
        logger.info(f"Retrieving documents for query: {query}")
        
        results = await self.retriever.search(query, top_k=top_k)
        
        return [
            {
                "content": doc.content,
                "similarity": score,
                "metadata": doc.metadata
            }
            for doc, score in results
        ]
