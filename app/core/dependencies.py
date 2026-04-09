"""Dependency injection and initialization"""
import logging
from typing import Optional, AsyncGenerator
import redis.asyncio as redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Global instances
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Get Redis connection"""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        _redis_client = await redis.from_url(
            f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            encoding="utf8",
            decode_responses=True
        )
    
    try:
        yield _redis_client
    finally:
        pass


async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def init_dependencies() -> None:
    """Initialize all dependencies"""
    logger.info("Initializing dependencies...")
    # Initialize Redis
    settings = get_settings()
    try:
        client = await redis.from_url(
            f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            encoding="utf8",
            decode_responses=True
        )
        await client.ping()
        await client.close()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
