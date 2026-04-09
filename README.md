# AgentForge: Production-Grade Multi-Agent AI System

A scalable, enterprise-level AI platform built with FastAPI and AgentForge framework for orchestrating multiple specialized AI agents.

## Features

### Architecture
- **Modular Design**: Clean separation of concerns with specialized modules
- **Async-First**: Full async support for high performance
- **Type-Safe**: Complete type hints throughout the codebase
- **Production-Ready**: Logging, security, and error handling

### Agents & Orchestration
- **Dynamic Agent Loading**: Load agents from YAML configuration
- **Multi-Agent Coordination**: Intelligent routing and orchestration
- **Agent Types**:
  - **General Agent**: Conversational AI for general tasks
  - **RAG Agent**: Retrieval-Augmented Generation for document QA
  - **SQL Agent**: Database query execution and analysis

### Tool Integration
- **Tool Registry**: Extensible tool system for agents
- **Built-in Tools**:
  - Document Retrieval (RAG)
  - SQL Query Execution
  - External API Calling
- **Custom Tools**: Easy to add custom tools

### RAG Pipeline
- **Vector Embeddings**: OpenAI, Local (sentence-transformers)
- **Vector Store**: ChromaDB integration
- **Context Injection**: Automatic context augmentation
- **Low-Latency**: Optimized retrieval performance

### Memory Systems
- **Short-term**: Conversation history per session
- **Long-term**: Persistent vector memory per user
- **Session Management**: Automatic expiry and cleanup

### API Layer
- **FastAPI**: Modern async web framework
- **REST Endpoints**: 
  - `POST /api/v1/chat` - Chat with agents
  - `POST /api/v1/run-agent` - Direct agent execution
  - `GET /api/v1/agents` - List available agents
  - `GET /api/v1/health` - Health check

### Security & Guardrails
- **Input Validation**: Pydantic schemas for all inputs
- **Prompt Injection Detection**: Pattern-based detection
- **SQL Injection Prevention**: Query validation
- **Output Filtering**: Sensitive data removal
- **Rate Limiting**: Built-in support
- **CORS Configuration**: Customizable cross-origin policies

### Observability
- **Structured Logging**: JSON-formatted logs
- **Request Tracing**: Full request lifecycle logging
- **Performance Metrics**: Execution time tracking
- **Error Tracking**: Comprehensive error logging

### Performance Optimization
- **Async Execution**: Non-blocking operations
- **Redis Caching**: Response caching layer
- **Batch Processing**: Support for batch requests
- **Connection Pooling**: Efficient resource management

### Testing
- **Unit Tests**: Agent and service tests
- **Integration Tests**: API endpoint tests
- **API Tests**: Full endpoint coverage
- **Pytest Configuration**: Pre-configured test setup

### Deployment
- **Docker Support**: Multi-stage builds
- **Docker Compose**: Complete service orchestration
- **Environment Configuration**: .env file support
- **Health Checks**: Service health monitoring

## Project Structure

```
agentforge-system/
├── app/
│   ├── api/              # FastAPI routes and endpoints
│   ├── agents/           # Agent definitions and registry
│   ├── services/         # Business logic (orchestrator, agent service)
│   ├── tools/            # Tool implementations and registry
│   ├── rag/              # RAG pipeline (embedder, retriever)
│   ├── memory/           # Memory systems (short-term, long-term)
│   ├── schemas/          # Request/response Pydantic models
│   ├── core/             # Configuration, logging, security, dependencies
│   ├── workflows/        # Workflow/cog orchestration
│   └── main.py           # FastAPI application entry point
├── config/
│   ├── agents/           # Agent YAML configurations
│   ├── personas/         # Persona definitions
│   └── workflows/        # Workflow definitions
├── tests/                # Unit and integration tests
├── docker/               # Docker configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```

## Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for containerized setup)
- API keys for LLM providers (OpenAI, Anthropic, or Google)

### Local Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/AgentForge.git
cd AgentForge
```

2. **Create and activate virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Start services locally** (Redis and ChromaDB required):
```bash
# Run Redis
redis-server

# In another terminal, run ChromaDB
chroma run --path ./storage/chroma

# In another terminal, run the API
python -m uvicorn app.main:app --reload
```

### Docker Setup

1. **Build and run with Docker Compose**:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

2. **Check services are running**:
```bash
docker-compose -f docker/docker-compose.yml ps
```

3. **View logs**:
```bash
docker-compose -f docker/docker-compose.yml logs -f api
```

4. **Stop services**:
```bash
docker-compose -f docker/docker-compose.yml down
```

## Configuration

### Environment Variables
See `.env.example` for all available configuration options. Key settings:

```env
# LLM Selection
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4

# Vector DB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Agent Configuration
Agents are defined in YAML files in `config/agents/`:

```yaml
name: General Agent
agent_id: general
description: General conversational agent
model: gpt-4
persona: default
tools:
  - retrieve
  - call_api
memory_enabled: true
temperature: 0.7
```

### Workflow Configuration
Workflows orchestrate multiple agents in `config/workflows/`:

```yaml
name: Example Workflow
id: example_workflow
steps:
  - agent: general
    input: user_input
  - agent: rag
    input: previous_output
```

## Usage

### API Examples

**Chat Endpoint**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "message": "What is machine learning?",
    "agent_type": "general",
    "use_rag": true
  }'
```

**Run Agent Directly**:
```bash
curl -X POST http://localhost:8000/api/v1/run-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "general",
    "input_data": {
      "query": "Hello!",
      "user_id": "user123"
    }
  }'
```

**List Agents**:
```bash
curl http://localhost:8000/api/v1/agents
```

**Health Check**:
```bash
curl http://localhost:8000/api/v1/health
```

### Python Usage

```python
import asyncio
from app.agents import AgentRegistry, AgentConfig
from app.agents.base import AgentContext

async def main():
    # Load and register agents
    config = AgentConfig(
        agent_id="general",
        name="General Agent",
        description="Test agent",
        model="gpt-4",
        persona="default"
    )
    
    agent = await AgentRegistry.register_agent(config)
    
    # Create context and process message
    context = AgentContext(
        user_id="user123",
        session_id="session456"
    )
    
    response = await agent.process("Hello!", context)
    print(response)

asyncio.run(main())
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_agents.py -v
```

### Run with Coverage
```bash
pytest --cov=app tests/
```

### Run Async Tests
```bash
pytest -m asyncio
```

## Development

### Code Quality
- **Format Code**: `black app tests`
- **Lint**: `flake8 app tests`
- **Type Check**: `mypy app`
- **Sort Imports**: `isort app tests`

### Add New Agent
1. Create agent class extending `BaseAgent`
2. Implement `process()` method
3. Register in `AgentRegistry`
4. Add YAML config in `config/agents/`

### Add New Tool
1. Create tool class extending `BaseTool`
2. Implement `execute()` method
3. Register in `ToolRegistry`
4. Update agent tools list

### Add New Endpoint
1. Create route in `app/api/routes.py`
2. Define request/response schemas
3. Implement endpoint logic
4. Add tests in `tests/test_api.py`

## Performance Tuning

### Memory Optimization
- Adjust `max_messages` in `ConversationMemory`
- Use `CHROMA_PATH` for local storage
- Configure Redis eviction policies

### Throughput Optimization
- Increase `MAX_WORKERS` in `.env`
- Use batch API calls
- Enable response caching
- Parallel agent execution

### Latency Optimization
- Use local embedders (sentence-transformers)
- Cache common queries
- Reduce context window size
- Use smaller models for preprocessing

## Deployment

### AWS ECS
```bash
# Build image
docker build -f docker/Dockerfile -t agentforge:latest .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag agentforge:latest <account>.dkr.ecr.<region>.amazonaws.com/agentforge:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/agentforge:latest
```

### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name agentforge \
  --image agentforge:latest \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

### GCP Cloud Run
```bash
gcloud run deploy agentforge \
  --image gcr.io/PROJECT/agentforge:latest \
  --platform managed \
  --region us-central1
```

## Troubleshooting

### Connection Issues
- Check Redis/ChromaDB services are running
- Verify `.env` configuration
- Check firewall and port availability

### API Key Errors
- Verify API keys in `.env`
- Check API key has required permissions
- Ensure API quotas not exceeded

### Memory Issues
- Reduce `max_messages` in short-term memory
- Limit RAG context size
- Enable Redis persistence

### Performance Issues
- Check system resource utilization
- Profile with `cProfile`
- Monitor database query performance
- Consider horizontal scaling

## License

This project is licensed under the GNU General Public License v3.0. See LICENSE for details.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Documentation**: See full docs in `/docs`
- **Issues**: Report issues on GitHub
- **Discussions**: Join our Discord community
- **Email**: contact@agentforge.net

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Google](https://ai.google/)
- Vector storage with [ChromaDB](https://docs.trychroma.com/)
- Caching with [Redis](https://redis.io/)

---

**Made with ❤️ for the AI/ML community**