"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.settings import settings
from src.infrastructure.logging import configure_logging, get_logger
from src.infrastructure.database.neo4j_client import neo4j_client
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.queue.rabbitmq_client import rabbitmq_client
from src.infrastructure.search.elasticsearch_client import elasticsearch_client
from src.infrastructure.audit import audit_logger
from src.infrastructure.audit.middleware import AuditMiddleware
from src.api.routes import auth, deduplication, ingestion
from src.auth.service import ensure_users_table
from src.deduplication.merge_history import ensure_merge_history_table
from src.ingestion.pipeline.job_store import ensure_ingestion_jobs_table
from src.security.abac.middleware import PermissionContextMiddleware

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info("Starting AfricGraph application")
    try:
        neo4j_client.connect()
        postgres_client.connect()
        redis_client.connect()
        rabbitmq_client.connect()
        elasticsearch_client.connect()
        audit_logger.ensure_audit_table()
        ensure_users_table()
        ensure_ingestion_jobs_table()
        ensure_merge_history_table()
        logger.info("All services connected successfully")
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AfricGraph application")
    neo4j_client.close()
    postgres_client.close()
    redis_client.close()
    rabbitmq_client.close()
    elasticsearch_client.close()
    logger.info("All services disconnected")


# Create FastAPI app
app = FastAPI(
    title="AfricGraph API",
    description="Ontology-Driven Decision Platform for SMEs",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PermissionContextMiddleware)
app.add_middleware(AuditMiddleware)

app.include_router(auth.router)
app.include_router(ingestion.router)
app.include_router(deduplication.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AfricGraph API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for all services."""
    return {
        "status": "healthy",
        "services": {
            "neo4j": neo4j_client.health_check(),
            "postgres": postgres_client.health_check(),
            "redis": redis_client.health_check(),
            "rabbitmq": rabbitmq_client.health_check(),
            "elasticsearch": elasticsearch_client.health_check(),
        }
    }
