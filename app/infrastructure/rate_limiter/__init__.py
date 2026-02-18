
"""
Rate Limiter Package.
Exposes the public API for rate limiting using the new modular structure.
"""

from typing import Dict, Optional

from app.infrastructure.rate_limiter.types import APIProvider
from app.infrastructure.rate_limiter.service import RateLimiter

__all__ = ["get_rate_limiter", "RateLimiter", "APIProvider"]

_registry: Dict[str, RateLimiter] = {}

def get_rate_limiter(
    name: str = "default",
    provider: APIProvider = APIProvider.GEMINI_FREE,
    **kwargs
) -> RateLimiter:
    """Singleton Registry access."""
    if name not in _registry:
        _registry[name] = RateLimiter(provider)
    return _registry[name]
