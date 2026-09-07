"""
AstraFlare Backend API Main FastAPI Application Entry Point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.utils.logging import setup_logging, logger
from backend.app.utils.errors import global_exception_handler
from backend.app.api.health import router as health_router
from backend.app.api.hotspots import router as hotspots_router
from backend.app.api.events import router as events_router
from backend.app.api.industrial_sites import router as industrial_sites_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.investigations import router as investigations_router
from backend.app.api.ingestion import router as ingestion_router

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}] Mode: {settings.ASTRAFLARE_MODE}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "AstraFlare Backend REST API exposes real NASA FIRMS satellite thermal observations, "
        "physical event clusters, OSM industrial infrastructure context, ESA WorldCover features, "
        "deterministic operational risk engine scores, and human-in-the-loop analyst review workflows."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Explicit CORS configuration for local React development
cors_origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
if settings.CORS_ORIGINS and settings.CORS_ORIGINS != "*":
    cors_origins.extend(settings.cors_origins_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Include API Routers
app.include_router(health_router)
app.include_router(hotspots_router)
app.include_router(events_router)
app.include_router(industrial_sites_router)
app.include_router(analytics_router)
app.include_router(investigations_router)
app.include_router(ingestion_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
