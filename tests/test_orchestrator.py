"""Tests for orchestrator"""
import pytest
from app.services.orchestrator_service import Orchestrator, OrchestratorConfig, RoutingStrategy


@pytest.mark.asyncio
async def test_routing_rule_based():
    """Test rule-based routing"""
    orchestrator = Orchestrator(
        OrchestratorConfig(routing_strategy=RoutingStrategy.RULE_BASED)
    )
    
    # SQL query
    agent_id = await orchestrator.route_query("SELECT * FROM users")
    assert agent_id == "sql"
    
    # RAG query
    agent_id = await orchestrator.route_query("Search for information")
    assert agent_id == "rag"
    
    # General query
    agent_id = await orchestrator.route_query("Hello, how are you?")
    assert agent_id == "general"


@pytest.mark.asyncio
async def test_direct_routing():
    """Test direct agent selection"""
    orchestrator = Orchestrator(
        OrchestratorConfig(routing_strategy=RoutingStrategy.DIRECT)
    )
    
    agent_id = await orchestrator.route_query(
        "Test query",
        context={"agent_id": "custom_agent"}
    )
    
    assert agent_id == "custom_agent"
