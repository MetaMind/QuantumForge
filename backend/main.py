import uvicorn
from fastapi import FastAPI

from backend.api.routes import app
from backend.core.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Application factory"""
    return app


if __name__ == "__main__":
    logger.info("Starting QuantumForge AI")
    uvicorn.run(
        "backend.main:create_app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    )
