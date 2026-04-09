"""Test configuration and fixtures"""
import pytest
import asyncio
from app.agents import AgentRegistry, AgentConfig
from app.memory import ConversationMemoryManager
from app.services.orchestrator_service import Orchestrator, OrchestratorConfig


@pytest.fixture
def event_loop():
    """Event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def agent_registry():
    """Agent registry fixture"""
    yield AgentRegistry
    # Cleanup
    await AgentRegistry.shutdown_all()


@pytest.fixture
def memory_manager():
    """Memory manager fixture"""
    return ConversationMemoryManager()


@pytest.fixture
def orchestrator():
    """Orchestrator fixture"""
    return Orchestrator(OrchestratorConfig())


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration"""
    return AgentConfig(
        agent_id="test_agent",
        name="Test Agent",
        description="Test agent for unit tests",
        model="gpt-4",
        persona="default",
        tools=[]
    )
