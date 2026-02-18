
"""
Configuration types and Enums for Rate Limiting.
"""

from enum import Enum
from dataclasses import dataclass

class APIProvider(Enum):
    """Supported API providers."""
    GEMINI_FREE = "gemini_free"
    GROQ = "groq"
    HUGGINGFACE = "huggingface"

@dataclass
class LimitConfig:
    """Rate limit parameter configuration."""
    max_tokens: int
    refill_rate: float  # tokens per second
    cooldown_after_429: float
    max_retries: int
    initial_backoff: float
    max_backoff: float

    @classmethod
    def default_for(cls, provider: APIProvider) -> "LimitConfig":
        """Returns optimized defaults for each provider."""
        defaults = {
            APIProvider.GEMINI_FREE: cls(10, 10.0 / 60.0, 60.0, 5, 5.0, 120.0), # 10 RPM
            APIProvider.GROQ: cls(25, 25.0 / 60.0, 15.0, 3, 2.0, 30.0),         # 25 RPM
            APIProvider.HUGGINGFACE: cls(10, 10.0 / 60.0, 20.0, 3, 5.0, 60.0),  # 10 RPM
        }
        return defaults.get(provider, defaults[APIProvider.GEMINI_FREE])
