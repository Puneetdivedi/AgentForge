"""Application configuration management"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_title: str = "AgentForge API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    
    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model name")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: Optional[str] = Field(default="claude-3-sonnet-20240229")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    google_model: Optional[str] = Field(default="gemini-pro")
    
    # Vector Database
    chroma_host: str = Field(default="localhost", description="Chroma DB host")
    chroma_port: int = Field(default=8001, description="Chroma DB port")
    chroma_path: str = Field(default="./storage/chroma", description="Local Chroma DB path")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    
    # Embedding Configuration
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")
    embedding_dimension: int = Field(default=1536, description="Embedding dimension")
    
    # Performance
    max_workers: int = Field(default=4, description="Max worker threads")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()
