"""Embedder for converting text to embeddings"""
from typing import List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbedderConfig:
    """Embedder configuration"""
    
    def __init__(self, 
                 model: str = "text-embedding-3-small",
                 api_key: Optional[str] = None,
                 dimension: int = 1536):
        self.model = model
        self.api_key = api_key
        self.dimension = dimension


class BaseEmbedder:
    """Base class for embedders"""
    
    def __init__(self, config: EmbedderConfig):
        self.config = config
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        raise NotImplementedError
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Embed multiple text strings"""
        raise NotImplementedError


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedder using their API"""
    
    def __init__(self, config: EmbedderConfig):
        super().__init__(config)
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=config.api_key)
        except ImportError:
            logger.error("OpenAI library not installed")
            raise
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        logger.debug(f"Embedding text of length {len(text)}")
        
        response = await self.client.embeddings.create(
            input=text,
            model=self.config.model
        )
        
        embedding = response.data[0].embedding
        return np.array(embedding)
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Embed multiple text strings"""
        logger.debug(f"Embedding {len(texts)} texts")
        
        response = await self.client.embeddings.create(
            input=texts,
            model=self.config.model
        )
        
        embeddings = [np.array(item.embedding) for item in response.data]
        return embeddings


class LocalEmbedder(BaseEmbedder):
    """Local embedder using sentence-transformers"""
    
    def __init__(self, config: EmbedderConfig):
        super().__init__(config)
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(config.model)
        except ImportError:
            logger.error("sentence-transformers library not installed")
            raise
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        logger.debug(f"Embedding text of length {len(text)}")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Embed multiple text strings"""
        logger.debug(f"Embedding {len(texts)} texts")
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [np.array(e) for e in embeddings]
