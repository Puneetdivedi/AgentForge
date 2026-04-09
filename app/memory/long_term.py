"""Long-term vector memory"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryEntry:
    """Long-term memory entry"""
    
    def __init__(self, 
                 user_id: str,
                 content: str,
                 metadata: Dict[str, Any] = None):
        self.user_id = user_id
        self.content = content
        self.metadata = metadata or {}
        self.embedding: Optional[List[float]] = None
        self.created_at = datetime.utcnow()
        self.access_count = 0
        self.last_accessed = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class VectorMemoryStore:
    """Long-term vector memory store"""
    
    def __init__(self, embedder=None, retriever=None):
        self.embedder = embedder
        self.retriever = retriever
        self.local_index: Dict[str, MemoryEntry] = {}
    
    async def store_memory(self, 
                          user_id: str, 
                          content: str, 
                          metadata: Dict[str, Any] = None) -> str:
        """Store a memory entry"""
        logger.info(f"Storing memory for user {user_id}")
        
        entry = MemoryEntry(user_id, content, metadata)
        
        # Embed the content
        if self.embedder:
            entry.embedding = (await self.embedder.embed_text(content)).tolist()
        
        # Store in vector database
        if self.retriever:
            from app.rag.retriever import Document
            doc = Document(
                content=content,
                metadata={
                    "user_id": user_id,
                    "type": "memory",
                    **metadata
                }
            )
            await self.retriever.add_document(doc, doc_id=user_id)
        
        # Store locally
        entry_id = f"{user_id}_{len(self.local_index)}"
        self.local_index[entry_id] = entry
        
        return entry_id
    
    async def retrieve_user_memories(self, 
                                     user_id: str, 
                                     query: str = None,
                                     top_k: int = 5) -> List[MemoryEntry]:
        """Retrieve user's memories"""
        logger.debug(f"Retrieving memories for user {user_id}")
        
        results = []
        
        # Search in vector store
        if self.retriever and query:
            search_results = await self.retriever.search(query, top_k=top_k)
            for doc, similarity in search_results:
                if doc.metadata.get("user_id") == user_id:
                    entry = MemoryEntry(user_id, doc.content, doc.metadata)
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    results.append(entry)
        
        return results
    
    def get_local_memories(self, user_id: str) -> List[MemoryEntry]:
        """Get local memories for user"""
        return [
            entry for entry in self.local_index.values()
            if entry.user_id == user_id
        ]
    
    async def clear_user_memories(self, user_id: str) -> None:
        """Clear all memories for a user"""
        logger.info(f"Clearing memories for user {user_id}")
        
        self.local_index = {
            k: v for k, v in self.local_index.items()
            if v.user_id != user_id
        }
