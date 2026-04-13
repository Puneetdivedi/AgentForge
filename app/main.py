"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import asyncio
import os
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.dependencies import init_dependencies, close_redis
from app.core.middleware import register_middleware
from app.core.exceptions import AppException, ErrorCode
from app.api.routes import router
from app.agents import AgentRegistry
from app.services.orchestrator_service import Orchestrator, OrchestratorConfig
from app.memory import ConversationMemoryManager

# Setup logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AgentForge application")
    
    try:
        # Initialize dependencies
        await init_dependencies()
        
        # Initialize orchestrator and load agents
        from app.api.routes import orchestrator as global_orchestrator
        from app.api.routes import agent_registry as global_registry
        from app.api.routes import memory_manager as global_memory
        
        global orchestrator, agent_registry, memory_manager
        
        # Setup orchestrator
        app.state.orchestrator = Orchestrator(OrchestratorConfig())
        app.state.memory_manager = ConversationMemoryManager()
        
        logger.info("Application startup complete")
    
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgentForge application")
    
    try:
        await AgentRegistry.shutdown_all()
        await close_redis()
        logger.info("Application shutdown complete")
    
    except Exception as e:
        logger.error(f"Application shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Register industry-level middleware (security, logging, monitoring, rate limiting, error handling)
register_middleware(app)

# Add CORS middleware (positioned after register_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.example\.com" if hasattr(settings, 'cors_origin_regex') else None
)

# Include routers
app.include_router(router)

# Health Check Endpoints (Kubernetes probes)
@app.get("/health", tags=["health"], include_in_schema=True)
async def health_check():
    """Liveness probe - basic health check"""
    return {"status": "ok", "service": "agentforge"}


@app.get("/health/ready", tags=["health"], include_in_schema=True)
async def readiness_check():
    """Readiness probe - checks if service is ready to handle traffic"""
    try:
        # Check dependencies
        await init_dependencies()
        return {
            "status": "ready",
            "service": "agentforge",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


@app.get("/health/live", tags=["health"], include_in_schema=True)
async def liveness_check():
    """Startup probe - checks if service is alive"""
    try:
        # Basic connectivity check
        return {
            "status": "alive",
            "service": "agentforge",
            "version": settings.api_version,
            "environment": getattr(settings, 'app_env', 'unknown')
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "dead", "error": str(e)}
        )


@app.get("/api/version", tags=["info"], include_in_schema=True)
async def version():
    """Get API version"""
    return {
        "version": settings.api_version,
        "service": settings.api_title,
        "environment": getattr(settings, 'app_env', 'unknown')
    }

# Serve dashboard from root
@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the dashboard"""
    from fastapi.responses import FileResponse
    public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
    dashboard_path = os.path.join(public_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"message": "AgentForge Dashboard"}

# Mount static files (public folder)
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/static", StaticFiles(directory=public_dir), name="static")



@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions with standardized response"""
    request_id = getattr(request.state, "request_id", f"req_{os.urandom(6).hex()}")
    logger.warning(
        f"Application error: {exc.error_code.value}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code.value,
            "status_code": exc.status_code,
            "message": exc.message
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code.value,
            "message": exc.message,
            "request_id": request_id,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
    request_id = getattr(request.state, "request_id", f"req_{os.urandom(6).hex()}")
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "Internal server error",
            "request_id": request_id
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        workers=1
    )
