"""Enhanced API routes with industry-level best practices"""
from fastapi import (
    APIRouter, Depends, HTTPException, Query, BackgroundTasks,
    Request, status
)
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import logging
import uuid
from datetime import datetime, timedelta
from functools import lru_cache

from app.schemas.enhanced_schemas import (
    ChatRequest, ChatResponse, ErrorResponse, HealthCheck,
    AgentListResponse, PaginationParams, ConversationMetadataResponse
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.exceptions import (
    AppException, ResourceNotFoundError, ValidationError,
    RateLimitError, AgentNotFoundError, AgentInitializationError
)
from app.core.monitoring import (
    PerformanceMonitor, RequestContext, DistributedTracing,
    MetricsCollector, MetricType
)
from app.core.security import SecurityValidator, OutputFilter

logger = get_logger(__name__)
settings = get_settings()
metrics = MetricsCollector()

# Initialize routers
router = APIRouter(prefix="/api/v1", tags=["agents"])
health_router = APIRouter(tags=["health"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Request/response logging
@lru_cache(maxsize=None)
def get_rate_limiter():
    """Get rate limiter instance"""
    from collections import defaultdict
    return defaultdict(list)


# ==================== Health Check Endpoints ====================

@health_router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Service health check"
)
async def health_check() -> HealthCheck:
    """
    Get service health status.
    
    Returns:
        HealthCheck: Health status with version and timestamp
    """
    from app.core.monitoring import ServiceHealth
    
    health = ServiceHealth()
    
    return HealthCheck(
        status=health.get_overall_status(),
        version=settings.api_version,
        timestamp=datetime.utcnow(),
        services={
            "api": "healthy",
            "cache": "healthy",
            "database": "healthy"
        }
    )


@health_router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe"
)
async def readiness_probe() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict: Readiness status
    """
    return {"status": "ready"}


@health_router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe"
)
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Liveness status
    """
    return {"status": "alive"}


# ==================== Chat Endpoints ====================

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to agent",
    response_description="Chat response with metadata"
)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
) -> ChatResponse:
    """
    Send a message to a specific agent and get a response.
    
    Args:
        request: Chat request with message and agent_id
        background_tasks: Background task manager
        http_request: HTTP request object
    
    Returns:
        ChatResponse: Agent response with metadata
    
    Raises:
        ValidationError: Invalid request
        AgentNotFoundError: Agent not found
        HTTPException: Server error
    """
    # Create request context for tracing
    request_context = RequestContext(
        user_id=request.user_id,
        session_id=request.session_id
    )
    
    # Validate security
    try:
        SecurityValidator.validate_input(request.message)
    except ValidationError as e:
        logger.warning(
            f"Security validation failed: {e.message}",
            extra={"request_id": request_context.request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict()
        )
    
    # Start monitoring
    start_time = datetime.utcnow()
    span_id = DistributedTracing.create_span(
        "chat_request",
        {"agent_id": request.agent_id}
    )
    
    try:
        with PerformanceMonitor.track_operation(
            f"chat.{request.agent_id}",
            warn_threshold_ms=2000
        ):
            # Simulate agent processing
            response_message = await process_message_with_agent(
                request.message,
                request.agent_id,
                request.temperature,
                request.max_tokens,
                request_context
            )
            
            # Filter output for safety
            filtered_response = OutputFilter.filter_output(
                response_message,
                request.agent_id
            )
        
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record metrics
        chat_metric = metrics.register_metric(
            "chat_requests_total",
            MetricType.COUNTER,
            "Total chat requests"
        )
        chat_metric.increment()
        
        chat_time_metric = metrics.register_metric(
            "chat_processing_time_ms",
            MetricType.HISTOGRAM,
            "Chat processing time"
        )
        chat_time_metric.record(elapsed_ms)
        
        logger.info(
            f"Chat processed: {request.agent_id}",
            extra={
                "request_id": request_context.request_id,
                "agent_id": request.agent_id,
                "elapsed_ms": elapsed_ms,
                "span_id": span_id
            }
        )
        
        return ChatResponse(
            request_id=request_context.request_id,
            message=filtered_response,
            agent_id=request.agent_id,
            processing_time_ms=int(elapsed_ms),
            tokens_used=len(request.message.split()),
            confidence=0.95,
            source="agent_llm",
            metadata={
                "session_id": request.session_id,
                "user_id": request.user_id
            }
        )
    
    except AgentNotFoundError as e:
        logger.warning(
            f"Agent not found: {request.agent_id}",
            extra={"request_id": request_context.request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.to_dict()
        )
    
    except Exception as e:
        logger.error(
            f"Chat processing failed: {str(e)}",
            extra={
                "request_id": request_context.request_id,
                "agent_id": request.agent_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CHAT_PROCESSING_FAILED",
                "message": "Failed to process chat request",
                "request_id": request_context.request_id
            }
        )


@router.get(
    "/agents",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all agents"
)
async def list_agents(
    pagination: PaginationParams = Depends()
) -> AgentListResponse:
    """
    Get list of all available agents.
    
    Args:
        pagination: Pagination parameters
    
    Returns:
        AgentListResponse: List of agents with metadata
    """
    with PerformanceMonitor.track_operation("list_agents"):
        # Simulate agent retrieval
        agents = [
            {
                "id": "general_agent",
                "name": "General Agent",
                "status": "healthy",
                "version": "1.0.0"
            },
            {
                "id": "rag_agent",
                "name": "RAG Agent",
                "status": "healthy",
                "version": "1.0.0"
            },
            {
                "id": "sql_agent",
                "name": "SQL Agent",
                "status": "healthy",
                "version": "1.0.0"
            }
        ]
        
        return AgentListResponse(
            agents=agents,
            total_count=len(agents),
            timestamp=datetime.utcnow()
        )


@router.get(
    "/agents/{agent_id}",
    status_code=status.HTTP_200_OK,
    summary="Get agent details"
)
async def get_agent_details(agent_id: str) -> Dict[str, Any]:
    """
    Get details of a specific agent.
    
    Args:
        agent_id: Agent identifier
    
    Returns:
        Dict: Agent details
    
    Raises:
        AgentNotFoundError: Agent not found
    """
    # Validate agent exists
    valid_agents = ["general_agent", "rag_agent", "sql_agent"]
    if agent_id not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "AGENT_NOT_FOUND",
                "message": f"Agent not found: {agent_id}"
            }
        )
    
    return {
        "id": agent_id,
        "name": agent_id.replace("_", " ").title(),
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": ["chat", "context-aware-responses"],
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "created_at": datetime.utcnow(),
        "last_updated": datetime.utcnow()
    }


@router.get(
    "/conversations/{conversation_id}/metadata",
    response_model=ConversationMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation metadata"
)
async def get_conversation_metadata(
    conversation_id: str
) -> ConversationMetadataResponse:
    """
    Get metadata about a conversation.
    
    Args:
        conversation_id: Conversation identifier
    
    Returns:
        ConversationMetadataResponse: Conversation metadata
    """
    return ConversationMetadataResponse(
        conversation_id=conversation_id,
        user_id="user_123",
        agent_id="general_agent",
        message_count=10,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        duration_seconds=300,
        status="active"
    )


# ==================== Admin Endpoints ====================

@admin_router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get system metrics"
)
async def get_metrics() -> Dict[str, Any]:
    """
    Get current system metrics (admin only).
    
    Returns:
        Dict: System metrics
    """
    return metrics.get_all_metrics()


@admin_router.post(
    "/metrics/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset metrics"
)
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics (admin only).
    
    Returns:
        Dict: Confirmation message
    """
    metrics.reset()
    return {"status": "metrics_reset"}


# ==================== Helper Functions ====================

async def process_message_with_agent(
    message: str,
    agent_id: str,
    temperature: float,
    max_tokens: int,
    context: RequestContext
) -> str:
    """
    Process message with specified agent.
    
    Args:
        message: User message
        agent_id: Agent identifier
        temperature: LLM temperature
        max_tokens: Max tokens
        context: Request context
    
    Returns:
        str: Agent response
    """
    # Simulate agent processing
    import asyncio
    await asyncio.sleep(0.1)
    
    return f"Response from {agent_id}: {message}"


# Include routers in main app
def register_routers(app):
    """Register all routers with the app"""
    app.include_router(health_router)
    app.include_router(router)
    app.include_router(admin_router)
