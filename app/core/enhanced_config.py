"""Enhanced application configuration with validation"""
import os
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from enum import Enum


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogFormat(str, Enum):
    """Log format options"""
    JSON = "json"
    TEXT = "text"
    PRETTY = "pretty"


class EnhancedSettings(BaseSettings):
    """Enhanced application settings with validation and documentation"""
    
    # ==================== Core Application ====================
    app_name: str = Field(
        default="AgentForge",
        description="Application name"
    )
    app_env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    app_debug: bool = Field(
        default=False,
        description="Debug mode enabled"
    )
    
    # ==================== API Configuration ====================
    api_title: str = Field(
        default="AgentForge API",
        description="API title"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_description: str = Field(
        default="Multi-agent framework for industry use cases",
        description="API description"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="API port"
    )
    api_root_path: str = Field(
        default="",
        description="API root path"
    )
    api_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Number of API workers"
    )
    
    # ==================== LLM Configuration ====================
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4",
        regex="^gpt-[0-9].*$",
        description="OpenAI model"
    )
    openai_timeout: int = Field(
        default=60,
        ge=10,
        description="OpenAI timeout in seconds"
    )
    openai_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="OpenAI max retries"
    )
    
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Anthropic model"
    )
    
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key"
    )
    google_model: str = Field(
        default="gemini-pro",
        description="Google model"
    )
    
    # ==================== Vector Database ====================
    chroma_enabled: bool = Field(
        default=True,
        description="Chroma database enabled"
    )
    chroma_mode: str = Field(
        default="local",
        regex="^(local|http|persistent)$",
        description="Chroma mode"
    )
    chroma_host: str = Field(
        default="localhost",
        description="Chroma host"
    )
    chroma_port: int = Field(
        default=8001,
        ge=1024,
        le=65535,
        description="Chroma port"
    )
    chroma_path: str = Field(
        default="./storage/chroma",
        description="Local Chroma DB path"
    )
    
    # ==================== Redis Configuration ====================
    redis_enabled: bool = Field(
        default=True,
        description="Redis enabled"
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL"
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host"
    )
    redis_port: int = Field(
        default=6379,
        ge=1024,
        le=65535,
        description="Redis port"
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    redis_ssl: bool = Field(
        default=False,
        description="Redis SSL"
    )
    redis_max_connections: int = Field(
        default=10,
        ge=1,
        description="Redis max connections"
    )
    
    # ==================== Database Configuration ====================
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    database_echo_sql: bool = Field(
        default=False,
        description="Echo SQL queries"
    )
    database_pool_size: int = Field(
        default=10,
        ge=1,
        description="Database pool size"
    )
    
    # ==================== Logging Configuration ====================
    log_level: str = Field(
        default="INFO",
        regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Log format"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path"
    )
    log_file_rotation: str = Field(
        default="100 MB",
        description="Log file rotation size"
    )
    log_file_backup_count: int = Field(
        default=5,
        ge=0,
        description="Log file backup count"
    )
    
    # ==================== Security Configuration ====================
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        min_length=32,
        description="Secret key for signing"
    )
    algorithm: str = Field(
        default="HS256",
        regex="^(HS256|HS512|RS256|RS512)$",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        description="Access token expiration in minutes"
    )
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="CORS allow credentials"
    )
    cors_methods: List[str] = Field(
        default=["*"],
        description="CORS allowed methods"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="CORS allowed headers"
    )
    
    # ==================== Embedding Configuration ====================
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model"
    )
    embedding_dimension: int = Field(
        default=1536,
        ge=1,
        description="Embedding dimension"
    )
    
    # ==================== Performance Configuration ====================
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds"
    )
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Rate limit requests per window"
    )
    rate_limit_window: int = Field(
        default=60,
        ge=1,
        description="Rate limit window in seconds"
    )
    
    # ==================== Monitoring Configuration ====================
    monitoring_enabled: bool = Field(
        default=True,
        description="Monitoring enabled"
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Metrics collection enabled"
    )
    tracing_enabled: bool = Field(
        default=False,
        description="Distributed tracing enabled"
    )
    tracing_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Tracing sample rate"
    )
    
    # ==================== Agent Configuration ====================
    agent_config_dir: str = Field(
        default="config/agents",
        description="Agent configuration directory"
    )
    agent_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Agent max retries"
    )
    agent_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Agent timeout in seconds"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_default = True
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @model_validator(mode="after")
    def validate_redis_config(self) -> "EnhancedSettings":
        """Validate Redis configuration"""
        if self.redis_enabled and not self.redis_url:
            self.redis_url = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}" if self.redis_password else f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return self
    
    @model_validator(mode="after")
    def validate_production_config(self) -> "EnhancedSettings":
        """Validate production configuration"""
        if self.app_env == Environment.PRODUCTION:
            if self.app_debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("Secret key must be changed in production")
            if self.cors_origins == ["*"]:
                raise ValueError("CORS origins must be restricted in production")
        return self
    
    def is_production(self) -> bool:
        """Check if production environment"""
        return self.app_env == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if development environment"""
        return self.app_env == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if testing environment"""
        return self.app_env == Environment.TESTING


def get_settings() -> EnhancedSettings:
    """Get application settings (singleton)"""
    return EnhancedSettings()


def get_settings_dict() -> Dict[str, Any]:
    """Get settings as dictionary"""
    settings = get_settings()
    return settings.model_dump()
