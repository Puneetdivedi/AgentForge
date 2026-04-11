"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
import os
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.dependencies import init_dependencies, close_redis
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
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

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



@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
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
