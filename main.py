import logging
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import setup_logging
from app.config.config import config

from app.presentation.api.v1.upload_routes import router as upload_router
from app.presentation.api.v1.csv_routes import router as csv_router
from app.presentation.api.v1.search_routes import router as search_router
from app.presentation.api.v1.chat_routes import router as chat_router
from app.presentation.api.v1.sheet_routes import router as sheet_router
from app.presentation.api.v1.company_delete import router as company_router
from app.presentation.api.v1.privacy_policy import router as privacy_policy_router
from app.presentation.api.v1.terms_and_conditions import router as terms_and_conditions_router
from app.presentation.api.v1.groq_routes import router as groq_router

setup_logging()
logger = logging.getLogger(__name__)

# def run_preflight_checks():
#     """Ensure required directories and configurations exist."""
#     required_dirs = ["static", "data/vector_db"]
#     for dir_path in required_dirs:
#         Path(dir_path).mkdir(parents=True, exist_ok=True)
    
#     logger.info("Pre-flight checks completed: Required directories are present.")
#     config.print_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Logic here runs exactly once when the worker starts.
    """
    # Startup Logic
    # run_preflight_checks()
    logger.info("Receipt AI System starting up")
    
    yield
    
    # Shutdown Logic
    logger.info("Receipt AI System shutting down")

def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    app = FastAPI(
        title="Receipt AI System",
        description="Modular system for OCR processing and RAG-based analysis.",
        version="1.1.1",
        lifespan=lifespan
    )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(sheet_router)
    app.include_router(upload_router)
    app.include_router(csv_router)
    app.include_router(search_router)
    app.include_router(chat_router)
    app.include_router(company_router)
    app.include_router(privacy_policy_router)
    app.include_router(terms_and_conditions_router)
    app.include_router(groq_router)

    app.mount("/media", StaticFiles(directory="media"), name="media")
    app.mount("/static", StaticFiles(directory="static", html=True), name="static")

    @app.get("/", tags=["Status"])
    async def root():
        return {
            "app": "Receipt AI System",
            "status": "Online"
        }
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
    