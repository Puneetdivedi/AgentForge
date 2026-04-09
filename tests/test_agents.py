"""Unit tests for agents"""
import pytest
from app.agents import AgentRegistry, AgentConfig
from app.agents.base import GeneralAgent, AgentContext


@pytest.mark.asyncio
async def test_agent_registration(sample_agent_config):
    """Test agent registration"""
    agent = await AgentRegistry.register_agent(sample_agent_config)
    assert agent is not None
    assert agent.config.agent_id == "test_agent"
    
    # Cleanup
    await AgentRegistry.deregister_agent("test_agent")


@pytest.mark.asyncio
async def test_get_agent(sample_agent_config):
    """Test getting registered agent"""
    await AgentRegistry.register_agent(sample_agent_config)
    agent = AgentRegistry.get_agent("test_agent")
    
    assert agent is not None
    assert agent.config.name == "Test Agent"
    
    # Cleanup
    await AgentRegistry.deregister_agent("test_agent")


@pytest.mark.asyncio
async def test_agent_process():
    """Test agent message processing"""
    config = AgentConfig(
        agent_id="general_test",
        name="General Test",
        description="Test agent",
        model="gpt-4",
        persona="default"
    )
    
    agent = GeneralAgent(config)
    await agent.initialize()
    
    context = AgentContext(
        user_id="test_user",
        session_id="test_session"
    )
    
    response = await agent.process("Test query", context)
    assert isinstance(response, str)
    
    await agent.shutdown()


def test_agent_context():
    """Test agent context creation"""
    context = AgentContext(
        user_id="user123",
        session_id="session456",
        memory={"key": "value"}
    )
    
    assert context.user_id == "user123"
    assert context.session_id == "session456"
    assert context.memory["key"] == "value"
