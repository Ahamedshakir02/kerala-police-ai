"""
Kerala Police AI Investigation Assistant — FastAPI Entry Point
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, firs, analysis, legal, patterns, dashboard, bhashini

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables and warm up ML models on startup."""
    logger.info("🚀 Starting Kerala Police AI system…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables ready")

    # Warm up embedding model (downloads on first run)
    from app.services.embedding_service import get_embedding_service
    svc = get_embedding_service()
    svc.warmup()
    logger.info("✅ Embedding model loaded")

    # Init ChromaDB collection
    from app.services.chroma_service import get_chroma_service
    get_chroma_service()
    logger.info("✅ ChromaDB ready")

    yield
    logger.info("👋 Shutting down Kerala Police AI system")


app = FastAPI(
    title="Kerala Police AI Investigation Assistant",
    description="Production-grade AI system for FIR analysis, case intelligence, and legal guidance.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(firs.router,      prefix="/api/firs",      tags=["FIR Management"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["AI Analysis"])
app.include_router(legal.router,     prefix="/api/legal",     tags=["Legal Guidance"])
app.include_router(patterns.router,  prefix="/api/patterns",  tags=["MO Patterns"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(bhashini.router,  prefix="/api/bhashini",  tags=["Bhashini / Malayalam"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Kerala Police AI Investigation Assistant"}
