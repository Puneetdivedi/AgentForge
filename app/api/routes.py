"""FastAPI routes and endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from app.schemas.response import (
    ChatRequest, ChatResponse, AgentResponse, HealthCheck, ErrorResponse
)
from app.core import get_settings, get_logger
from app.core.security import SecurityValidator, OutputFilter

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agents"])

# Global state (in production, use dependency injection)
settings = get_settings()
orchestrator = None
agent_registry = None
memory_manager = None


@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow()
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for agent interaction
    
    Args:
        request: Chat request
        
    Returns:
        Chat response
    """
    try:
        # Validate input
        if SecurityValidator.validate_prompt_injection(request.message):
            logger.warning(f"Potential prompt injection detected from user {request.user_id}")
            raise HTTPException(status_code=400, detail="Invalid input detected")
        
        # Sanitize input
        message = SecurityValidator.sanitize_input(request.message)
        
        # Store in short-term memory
        if memory_manager:
            memory_manager.add_message(request.session_id, "user", message)
        
        # Route and execute
        if orchestrator and agent_registry:
            response_text = await orchestrator.orchestrate(
                query=message,
                agent_registry=agent_registry,
                context={
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "agent_type": request.agent_type.value
                }
            )
            
            # Filter output for sensitive data
            response_text = OutputFilter.filter_sensitive_data(response_text)
            
            # Store response in memory
            if memory_manager:
                memory_manager.add_message(request.session_id, "assistant", response_text)
        else:
            response_text = "System not fully initialized"
        
        return ChatResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            message=response_text,
            agent_type=request.agent_type,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-agent", response_model=AgentResponse)
async def run_agent(agent_id: str, input_data: Dict[str, Any] = {}) -> AgentResponse:
    """
    Run specific agent directly
    
    Args:
        agent_id: Agent identifier
        input_data: Input data for agent
        
    Returns:
        Agent response
    """
    try:
        if not agent_registry:
            raise HTTPException(status_code=503, detail="Agent registry not initialized")
        
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        # Execute agent
        from app.agents.base import AgentContext
        context = AgentContext(
            user_id=input_data.get("user_id", "unknown"),
            session_id=str(uuid.uuid4())
        )
        
        response = await agent.process(
            input_data.get("query", ""),
            context
        )
        
        return AgentResponse(
            agent_id=agent_id,
            output={"response": response},
            status="success",
            execution_time=0.0
        )
    
    except Exception as e:
        logger.error(f"Run agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List all available agents"""
    if not agent_registry:
        return {"agents": []}
    
    agents = agent_registry.get_all_agents()
    return {"agents": list(agents.keys())}


@router.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str) -> Dict[str, Any]:
    """Get agent information"""
    if not agent_registry:
        raise HTTPException(status_code=503, detail="Agent registry not initialized")
    
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    return {
        "agent_id": agent_id,
        "config": agent.config.dict()
    }
