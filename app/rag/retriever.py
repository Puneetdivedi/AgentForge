"""Vector store retriever"""
from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class Document(BaseModel):
    """Document structure for retrieval"""
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class BaseRetriever:
    """Base class for retrievers"""
    
    async def add_document(self, doc: Document) -> None:
        """Add a document to the store"""
        raise NotImplementedError
    
    async def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Search for documents"""
        raise NotImplementedError
    
    async def delete_document(self, doc_id: str) -> None:
        """Delete a document"""
        raise NotImplementedError


class ChromaRetriever(BaseRetriever):
    """Retriever using ChromaDB"""
    
    def __init__(self, 
                 collection_name: str = "documents",
                 embedder=None,
                 host: Optional[str] = None,
                 port: Optional[int] = None):
        self.collection_name = collection_name
        self.embedder = embedder
        self.host = host
        self.port = port
        self.collection = None
        self.client = None
    
    async def initialize(self) -> None:
        """Initialize Chroma client"""
        try:
            import chromadb
            if self.host and self.port:
                self.client = chromadb.HttpClient(host=self.host, port=self.port)
            else:
                self.client = chromadb.Client()
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized Chroma retriever: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            raise
    
    async def add_document(self, doc: Document, doc_id: Optional[str] = None) -> None:
        """Add a document to Chroma"""
        if not self.collection:
            await self.initialize()
        
        doc_id = doc_id or hash(doc.content)
        
        # Embed the document
        if self.embedder:
            embedding = await self.embedder.embed_text(doc.content)
        else:
            embedding = None
        
        self.collection.add(
            documents=[doc.content],
            metadatas=[doc.metadata],
            ids=[str(doc_id)],
            embeddings=[embedding.tolist() if embedding is not None else None]
        )
        
        logger.debug(f"Added document {doc_id} to Chroma")
    
    async def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Search Chroma collection"""
        if not self.collection:
            await self.initialize()
        
        # Embed the query
        if self.embedder:
            query_embedding = await self.embedder.embed_text(query)
        else:
            query_embedding = None
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()] if query_embedding is not None else None,
            query_texts=[query] if query_embedding is None else None,
            n_results=top_k
        )
        
        documents = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0
                similarity = 1 - distance  # Convert distance to similarity
                
                doc_obj = Document(
                    content=doc,
                    metadata=results["metadatas"][0][i] if results.get("metadatas") else {}
                )
                documents.append((doc_obj, similarity))
        
        logger.debug(f"Retrieved {len(documents)} documents for query")
        return documents
