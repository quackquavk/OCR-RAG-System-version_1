
"""
Rate Limiter Service Facade.
"""

import asyncio
import logging
import re
from typing import Callable, Any

from app.core.exceptions import RateLimitExceededError, ExternalServiceError
from app.infrastructure.rate_limiter.types import APIProvider, LimitConfig
from app.infrastructure.rate_limiter.bucket import TokenBucket
from app.infrastructure.rate_limiter.breaker import CircuitBreaker
from app.infrastructure.rate_limiter.scheduler import PriorityScheduler

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Public Facade. Coordinates Retry and Rate Limiting logic.
    """
    def __init__(self, provider: APIProvider):
        self.provider = provider
        self.config = LimitConfig.default_for(provider)
        
        # Composition
        self._bucket = TokenBucket(self.config.max_tokens, self.config.refill_rate)
        self._breaker = CircuitBreaker(self.config.cooldown_after_429)
        self._scheduler = PriorityScheduler(self._bucket, self._breaker)

    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        priority: int = 10,
        **kwargs: Any,
    ) -> Any:
        """
        Executes a function with rate limiting, retries, and backoff.
        """
        attempt = 0
        backoff = self.config.initial_backoff

        while attempt <= self.config.max_retries:
            try:
                # 1. Wait for permission (Rate Limit)
                await self._scheduler.wait_for_slot(priority)

                # 2. Execute
                result = await func(*args, **kwargs)
                
                # 3. Success
                self._breaker.reset()
                return result

            except Exception as e:
                attempt += 1
                if not self._should_retry(e, attempt):
                    raise
                
                # 4. Handle Failure & Backoff
                wait_time = self._calculate_wait_time(e, backoff)
                logger.warning(f"[{self.provider.value}] Failed (Attempt {attempt}). Retrying in {wait_time:.1f}s. Error: {e}")
                
                if isinstance(e, RateLimitExceededError) or "429" in str(e):
                    self._breaker.trip(wait_time)
                
                await asyncio.sleep(wait_time)
                backoff = min(backoff * 2, self.config.max_backoff)
        
        raise RateLimitExceededError(f"Max retries exceeded for {self.provider.value}", self.provider.value)

    def _should_retry(self, e: Exception, attempt: int) -> bool:
        """Determines if the error is retryable."""
        if attempt > self.config.max_retries:
            return False
            
        err = str(e).lower()
        if "402" in err or "insufficient balance" in err:
            raise ExternalServiceError(f"Insufficient quota/balance for {self.provider.value}", self.provider.value, e)
            
        return any(x in err for x in ["429", "rate limit", "quota", "timeout", "500", "503", "exhausted"])

    def _calculate_wait_time(self, e: Exception, current_backoff: float) -> float:
        """Parses 'retry-after' or uses exponential backoff."""
        try:
            # Simple regex for "5s", "10m", etc.
            err = str(e).lower()
            if match := re.search(r"(\d+)(\s?s|m)", err):
                val = float(match.group(1))
                if "m" in match.group(2): val *= 60
                return val + 1.0
        except Exception:
            pass
        return current_backoff
