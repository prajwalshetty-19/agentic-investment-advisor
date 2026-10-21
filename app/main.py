"""FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.db.init_db import init_db
from app.api.auth_routes import router as auth_router
from app.api.wallet_routes import router as wallet_router
from app.api.asset_routes import router as asset_router
from app.api.order_routes import router as order_router
from app.api.portfolio_routes import router as portfolio_router
from app.api.settings_routes import router as settings_router
from app.api.agent_routes import router as agent_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and seed assets on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Agentic AI-Powered Virtual Investment and Portfolio Management Platform",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(asset_router)
app.include_router(order_router)
app.include_router(portfolio_router)
app.include_router(settings_router)
app.include_router(agent_router)


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "is_simulation_mode": True
    }
