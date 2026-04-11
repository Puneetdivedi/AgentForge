# Integration Guide - Implementing Industry-Level Improvements

## 📋 Overview

This guide shows step-by-step how to integrate the new industry-level code into your existing AgentForge codebase.

---

## Phase 1: Error Handling & Exceptions (30 minutes)

### Step 1: Replace Global Exception Handler

**File: app/main.py**

OLD:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

NEW:
```python
from app.core.middleware import register_middleware

# Remove the old global exception handler
# Add middleware to app initialization
register_middleware(app)

# Middleware handles all exceptions with standardized responses
```

### Step 2: Update Error Imports

In any API route file:

```python
# Add import at top
from app.core.exceptions import (
    ValidationError, AuthenticationError, 
    ResourceNotFoundError, AgentNotFoundError
)

# Replace manual error handling
# OLD:
if not agent_id:
    return JSONResponse(status_code=400, 
        content={"error": "Invalid agent_id"})

# NEW:
if not agent_id:
    raise ValidationError(
        "Invalid agent_id",
        details={"field": "agent_id"}
    )
# Middleware automatically returns proper response
```

### Step 3: Verify Exception Responses

Test with:
```bash
# Will return 400 with structured error
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "", "agent_id": "inv@lid"}'

# Response:
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid agent_id",
  "details": {"field": "agent_id"}
}
```

---

## Phase 2: Configuration Management (20 minutes)

### Step 1: Update Config Import

**File: app/core/config.py**

Option A: Minimal change (keep existing, add new)
```python
# Keep existing Settings class for backward compatibility
# Add new EnhancedSettings for new code
```

Option B: Replace entirely
```python
# Replace entire app/core/config.py with enhanced_config.py content
# Update all imports from:
from app.core.config import get_settings
# (stays the same, returns EnhancedSettings instead)
```

### Step 2: Update Environment Variables

**.env file:**
```env
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=<generate-32-char-random-key>

# Production config validation enabled
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

Test validation:
```python
from app.core.enhanced_config import EnhancedSettings

# This will raise ValueError if config is invalid
settings = EnhancedSettings()
```

---

## Phase 3: Request/Response Validation (30 minutes)

### Step 1: Update Schema Imports

**File: app/schemas/response.py**

```python
# Keep existing response.py for backward compatibility

# New file: app/schemas/enhanced_schemas.py 
# Contains all enhanced models with full validation
```

### Step 2: Update API Route Models

**Before (in app/api/routes.py):**
```python
from app.schemas.response import ChatRequest, ChatResponse

@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # Minimal validation
```

**After:**
```python
from app.schemas.enhanced_schemas import ChatRequest, ChatResponse

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Full validation automatically
    # Invalid requests return 422 with details
```

### Step 3: Test Validation

```bash
# Too short message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "", "agent_id": "agent"}'

# Returns 422 (Validation Error)

# Invalid agent_id format
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "agent_id": "Invalid@Agent"}'

# Returns 422 with regex violation error
```

---

## Phase 4: Integrate Middleware (30 minutes)

### Step 1: Update app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add import
from app.core.middleware import register_middleware

app = FastAPI(...)

# NEW: Register middleware before adding routes
register_middleware(app)

# Keep existing CORS (or let middleware handle it)
# If keeping CORS, put this AFTER register_middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# ... rest of app setup
```

### Step 2: Register Enhanced Routes

```python
# In app/main.py, after creating app

from app.api.enhanced_routes import register_routers

# Register all enhanced routes
register_routers(app)

# Keep existing routes or migrate gradually
app.include_router(old_router)  # Temporary
```

### Step 3: Verify Middleware

```bash
# Check security headers
curl -i http://localhost:8000/health
# Should see: X-Content-Type-Options, X-Frame-Options, etc.

# Check rate limiting
for i in {1..102}; do curl -s http://localhost:8000/api/v1/chat; done
# 101-102 should return 429 (Too Many Requests)

# Check request IDs
curl -i http://localhost:8000/health
# Should see: X-Request-ID header in response
```

---

## Phase 5: Update Agent Base Classes (45 minutes)

### Step 1: Minimal Change (Recommended)

Keep existing agents working, add new enhanced ones:

```python
# In app/agents/base.py: Keep existing BaseAgent

# In app/agents/enhanced_base.py: New enhanced version

# Gradually migrate agents:
# 1. GeneralAgent extends enhanced BaseAgent
# 2. RAGAgent extends enhanced BaseAgent  
# 3. SQLAgent extends enhanced BaseAgent
```

### Step 2: Add Status Tracking

```python
# Update existing agents to track status
from app.agents.enhanced_base import AgentStatus

class GeneralAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.status = AgentStatus.UNINITIALIZED
    
    async def initialize(self):
        self.status = AgentStatus.INITIALIZING
        # ... init code
        self.status = AgentStatus.READY
    
    def get_status(self):
        return {
            "agent_id": self.config.agent_id,
            "status": self.status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
```

### Step 3: Add Retry Logic

```python
# In your agent's process method
import asyncio

async def process(self, message, context, retry_count=0):
    try:
        response = await self._process(message, context)
        return response
    except Exception as e:
        if retry_count < self.max_retries:
            await asyncio.sleep(2 ** retry_count)
            return await self.process(message, context, retry_count + 1)
        raise
```

---

## Phase 6: Add Monitoring (30 minutes)

### Step 1: Initialize Metrics

**In app/main.py startup:**

```python
from app.core.monitoring import MetricsCollector, MetricType

@asynccontextmanager
async def lifespan(app):
    # Startup
    metrics = MetricsCollector()
    
    # Initialize default metrics
    metrics.register_metric(
        "chat_requests_total",
        MetricType.COUNTER,
        "Total chat requests"
    )
    metrics.register_metric(
        "chat_processing_time_ms",
        MetricType.HISTOGRAM,
        "Chat processing time"
    )
    
    yield
    
    # Shutdown
    logger.info(f"Final metrics: {metrics.get_all_metrics()}")
```

### Step 2: Record Metrics in Endpoints

```python
from app.core.monitoring import MetricsCollector, PerformanceMonitor

@router.post("/chat")
async def chat(request: ChatRequest):
    metrics = MetricsCollector()
    
    with PerformanceMonitor.track_operation("chat_request"):
        response = await process_message(...)
    
    # Record metric
    chat_counter = metrics.register_metric(
        "chat_requests_total",
        MetricType.COUNTER
    )
    chat_counter.increment()
    
    return response
```

### Step 3: Expose Metrics

```python
# In app/api/enhanced_routes.py (already done)
# Or add to your routes.py:

@admin_router.get("/metrics")
async def get_metrics():
    from app.core.monitoring import MetricsCollector
    metrics = MetricsCollector()
    return metrics.get_all_metrics()
```

---

## Phase 7: Add Request Tracing (30 minutes)

### Step 1: Create Request Context

```python
# In your endpoints
from app.core.monitoring import RequestContext

@router.post("/chat")
async def chat(request: ChatRequest, http_request: Request):
    # Create context
    ctx = RequestContext(
        user_id=request.user_id,
        session_id=request.session_id,
        source="api"
    )
    
    # Use in logging
    logger.info(
        "Chat request received",
        extra={
            "request_id": ctx.request_id,
            "user_id": ctx.user_id,
            "session_id": ctx.session_id
        }
    )
    
    # Include in response
    return ChatResponse(
        request_id=ctx.request_id,
        ...
    )
```

### Step 2: Add to Response Headers

```python
@router.post("/chat")
async def chat(request: ChatRequest, response: Response):
    ctx = RequestContext()
    
    # Also return in headers for client tracking
    response.headers["X-Request-ID"] = ctx.request_id
    
    return ChatResponse(
        request_id=ctx.request_id,
        ...
    )
```

---

## Phase 8: Update Logging (30 minutes)

### Step 1: Enhance Existing Logs

**Before:**
```python
logger.info(f"Processing message: {message}")
```

**After:**
```python
logger.info(
    "Processing message",
    extra={
        "request_id": ctx.request_id,
        "agent_id": agent_id,
        "message_length": len(message),
        "user_id": ctx.user_id
    }
)
```

### Step 2: Configure JSON Logging

**In app/core/logging.py:**
```python
import pythonjsonlogger.jsonlogger

# Format logs as JSON
json_format = "%(timestamp)s %(level)s %(name)s %(message)s"
json_handler = logging.StreamHandler()
json_handler.setFormatter(
    pythonjsonlogger.jsonlogger.JsonFormatter(json_format)
)

# Or use:
from app.core.enhanced_config import get_settings
settings = get_settings()
if settings.log_format == "json":
    # Use JSON formatter
```

---

## Phase 9: Add Health Probes (20 minutes)

### Step 1: Register Health Endpoints

```python
# In app/main.py
from app.api.enhanced_routes import health_router

app.include_router(health_router)

# Creates 3 endpoints:
# GET /health - Full health check
# GET /health/ready - Kubernetes readiness probe
# GET /health/live - Kubernetes liveness probe
```

### Step 2: Update Dockerfile

```dockerfile
# For Kubernetes liveness probe
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1
```

### Step 3: Update Kubernetes Manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: agentforge
spec:
  containers:
  - name: agentforge
    image: agentforge:latest
    ports:
    - containerPort: 8000
    
    # Readiness probe
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
    
    # Liveness probe
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 20
      periodSeconds: 10
```

---

## Implementation Timeline

| Phase | Time | Priority |
|-------|------|----------|
| 1. Exception Handling | 30 min | 🔴 Critical |
| 2. Configuration | 20 min | 🔴 Critical |
| 3. Validation | 30 min | 🟡 High |
| 4. Middleware | 30 min | 🟡 High |
| 5. Agent Lifecycle | 45 min | 🟡 High |
| 6. Monitoring | 30 min | 🟡 High |
| 7. Request Tracing | 30 min | 🟢 Medium |
| 8. Logging | 30 min | 🟢 Medium |
| 9. Health Probes | 20 min | 🟢 Medium |
| **Total** | **4.5 hours** | |

---

## Rollback Plan

If something breaks:

```bash
# 1. Stop the service
docker stop agentforge

# 2. Revert to previous version
git revert <commit-hash>
# OR
docker run agentforge:prev-version

# 3. Restart
docker start agentforge

# 4. Verify health
curl http://localhost:8000/health
```

---

## Success Criteria

After integration, your system should:

✅ Return specific error codes (not all 500)
✅ Have metrics accessible at `/api/v1/admin/metrics`
✅ Log structured JSON with request IDs
✅ Have security headers in responses
✅ Rate limit at 100 req/min per IP
✅ Support Kubernetes health probes
✅ Track request processing time
✅ Include request IDs in responses
✅ Handle agent state transitions
✅ Retry failed operations automatically

---

## Testing Checklist

- [ ] Test error responses (return correct status codes)
- [ ] Test rate limiting (429 on excess)
- [ ] Test health endpoints (all respond OK)
- [ ] Test security headers (present in responses)
- [ ] Test request IDs (consistent in logs and responses)
- [ ] Test metrics endpoint (returns data)
- [ ] Test agent lifecycle (8 states work)
- [ ] Test retry logic (automatic retries on failure)
- [ ] Test validation (rejects invalid input)
- [ ] Test configuration (production config enforced)
- [ ] Load test (check performance impact)
- [ ] Monitor logs (structured output)

---

## Questions & Support

Refer to:
- **INDUSTRY_IMPROVEMENTS.md** - Detailed explanations
- **INDUSTRY_QUICK_REFERENCE.md** - Visual guides
- **TRANSFORMATION_SUMMARY.md** - Overview
- New source files - Full implementation

