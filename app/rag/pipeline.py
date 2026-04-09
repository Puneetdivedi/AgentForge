"""RAG pipeline orchestration"""
from typing import List, Optional, Dict, Any
import logging
from app.rag.embedder import BaseEmbedder
from app.rag.retriever import Document

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG (Retrieval Augmented Generation) pipeline"""
    
    def __init__(self, 
                 embedder: BaseEmbedder,
                 retriever,
                 max_context_length: int = 2000):
        self.embedder = embedder
        self.retriever = retriever
        self.max_context_length = max_context_length
    
    async def initialize(self) -> None:
        """Initialize the RAG pipeline"""
        logger.info("Initializing RAG pipeline")
        if hasattr(self.retriever, "initialize"):
            await self.retriever.initialize()
    
    async def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of documents to add
        """
        logger.info(f"Adding {len(documents)} documents to knowledge base")
        for doc in documents:
            await self.retriever.add_document(doc)
    
    async def retrieve_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant context for a query
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Concatenated context from retrieved documents
        """
        logger.info(f"Retrieving context for query: {query}")
        
        search_results = await self.retriever.search(query, top_k=top_k)
        
        context_parts = []
        current_length = 0
        
        for doc, similarity in search_results:
            doc_text = f"[Similarity: {similarity:.2f}] {doc.content}"
            
            if current_length + len(doc_text) > self.max_context_length:
                logger.debug("Max context length reached")
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        context = "\n\n".join(context_parts)
        logger.debug(f"Retrieved context of length {len(context)}")
        
        return context
    
    async def generate_prompt_with_context(self, 
                                          query: str, 
                                          system_prompt: str,
                                          top_k: int = 5) -> str:
        """
        Generate a complete prompt with retrieved context
        
        Args:
            query: User query
            system_prompt: Base system prompt
            top_k: Number of documents to retrieve
            
        Returns:
            Complete prompt with context
        """
        context = await self.retrieve_context(query, top_k=top_k)
        
        prompt = f"""{system_prompt}

Context from knowledge base:
{context}

User query: {query}

Please answer the query based on the provided context."""
        
        return prompt
