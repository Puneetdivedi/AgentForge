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


def get_demo_response(query: str, agent_type: str) -> str:
    """Generate demo responses based on query and agent type"""
    query_lower = query.lower()
    
    if agent_type == "general":
        if "feature" in query_lower or "what" in query_lower:
            return "Our platform includes 3 specialized AI agents:\n• General Intelligence Agent - for common questions\n• Knowledge Base Agent - for document search\n• Data Analytics Agent - for business queries\n\nWe use advanced RAG pipelines and safety validation to ensure accurate, secure responses."
        elif "troubleshoot" in query_lower or "error" in query_lower:
            return "Here are common troubleshooting steps:\n1. Check your internet connection\n2. Clear browser cache and cookies\n3. Reload the page\n4. Contact support at support@insightforge.com if issues persist"
        elif "policy" in query_lower or "return" in query_lower:
            return "Our return policy allows 30 days for returns in original condition. For details, visit our Help Center or contact support@insightforge.com"
        elif "billing" in query_lower or "charge" in query_lower:
            return "Billing Information:\n• Monthly subscription: $99\n• Annual subscription: $990 (save 17%)\n• Enterprise plans: Custom pricing\n• Free trial: 14 days\n• Cancel anytime"
        else:
            return f"I understand you're asking: '{query}'. This is a demo environment. In production, I'd connect to your knowledge base for accurate information."
    
    elif agent_type == "rag":
        if "password" in query_lower or "reset" in query_lower:
            return "Password Reset Procedure:\n1. Go to login page\n2. Click 'Forgot Password'\n3. Enter your email\n4. Check email for reset link\n5. Create new password\n6. Log in with new password\n\nFor security, reset links expire after 24 hours."
        elif "api" in query_lower or "integration" in query_lower:
            return "API Integration Guide:\n\nBase URL: https://api.insightforge.com/v1\nAuth: Bearer token required\n\nKey Endpoints:\n• POST /chat - Send messages\n• GET /agents - List agents\n• POST /run-agent - Execute agent\n\nDocumentation: https://docs.insightforge.com/api"
        elif "pricing" in query_lower or "price" in query_lower or "cost" in query_lower:
            return "Pricing Plans:\n\nStarter: $99/month\n• 1,000 API calls\n• 5 users\n• Email support\n\nPro: $299/month\n• 50,000 API calls\n• 50 users\n• Priority support\n\nEnterprise: Custom\n• Unlimited API calls\n• Dedicated support\n• SLA guaranteed"
        elif "compliance" in query_lower or "gdpr" in query_lower or "security" in query_lower:
            return "Compliance & Security:\n✓ GDPR Compliant\n✓ SOC 2 Type II Certified\n✓ HIPAA Ready\n✓ End-to-end Encryption\n✓ Regular Security Audits\n✓ Data Centers in US, EU, APAC\n\nFor detailed security documentation, contact our compliance team."
        else:
            return f"Searching knowledge base for: '{query}'. Results would show relevant documents and FAQs in production."
    
    elif agent_type == "sql":
        if "sales" in query_lower or "revenue" in query_lower:
            return "Q2 2026 Sales Report:\n• Total Revenue: $2.487M\n• YoY Growth: 34%\n• Top Region: North America (42%)\n• Top Product: Enterprise Plan (58% of revenue)\n• Customer Acquisition Cost: $234"
        elif "satisfaction" in query_lower or "rating" in query_lower:
            return "Customer Satisfaction by Region:\n• North America: 4.6/5 (892 reviews)\n• Europe: 4.4/5 (734 reviews)\n• APAC: 4.7/5 (567 reviews)\n• Average NPS: 72\n\nTop satisfaction drivers: Speed (93%), Features (88%), Support (85%)"
        elif "product" in query_lower:
            return "Top 10 Products by Revenue:\n1. Enterprise Plan - $1.44M\n2. Professional Plan - $687K\n3. API Access - $234K\n4. Custom Integration - $89K\n5. Premium Support - $34K\n\nEnterprise segment shows 156% growth YoY."
        elif "ticket" in query_lower or "support" in query_lower:
            return "Support Ticket Trends:\n• Total Tickets (Month): 2,847\n• Billing Issues: 34% (971)\n• Technical Support: 42% (1,196)\n• Account Questions: 18% (512)\n• Feature Requests: 6% (168)\n• Resolution Rate: 94%\n• Average Resolution Time: 2.3 hours"
        else:
            return f"Analytics query: '{query}'. Executing SQL on production database would provide real-time insights."
    
    return "Processing your request..."

@router.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow()
    )


@router.get("/examples/{agent_type}")
async def get_examples(agent_type: str) -> Dict[str, Any]:
    """Get example queries for an agent type"""
    examples = {
        "general": [
            "What are the key features of our product?",
            "How do I troubleshoot connection issues?",
            "What's our return policy?",
            "Can you explain how the billing works?"
        ],
        "rag": [
            "Search for password reset procedures",
            "Find information about API integration",
            "Look up pricing information",
            "Search for compliance documentation"
        ],
        "sql": [
            "What are our total sales this quarter?",
            "Show customer satisfaction by region",
            "List top 10 products by revenue",
            "Show support ticket trends by type"
        ]
    }
    
    return {
        "agent_type": agent_type,
        "examples": examples.get(agent_type, [])
    }


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
        
        # Demo responses for better UX
        demo_responses = get_demo_response(message, request.agent_type.value)
        
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
            # Use demo response in development mode
            response_text = demo_responses or "System processing your request..."
        
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
