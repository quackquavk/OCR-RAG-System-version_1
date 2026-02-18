"""Groq API status and model info routes."""

import os
import logging
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Groq"])
logger = logging.getLogger(__name__)


@router.get("/groq/status")
async def groq_status():
    """Check if Groq API key is configured."""
    api_key = os.getenv("GROQ_API_KEY", "")
    return {
        "configured": bool(api_key),
        "model": os.getenv("RAG_LLM_MODEL", "llama-3.3-70b-versatile"),
    }
