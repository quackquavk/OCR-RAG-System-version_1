
"""
Circuit Breaker Pattern for Rate Limiting.
"""

import time
from typing import Optional

class CircuitBreaker:
    """
    Manages the 'Cooldown' state when an external API returns a 429.
    """
    def __init__(self, default_cooldown: float):
        self._default_cooldown = default_cooldown
        self._retry_after_ts: float = 0.0

    def trip(self, wait_seconds: Optional[float] = None):
        """Activates the circuit breaker."""
        wait = wait_seconds if wait_seconds is not None else self._default_cooldown
        self._retry_after_ts = time.monotonic() + wait

    def reset(self):
        """Resets the circuit breaker (on success)."""
        self._retry_after_ts = 0.0

    def is_open(self) -> bool:
        """Returns True if we are mostly likely still blocked."""
        return time.monotonic() < self._retry_after_ts

    def time_remaining(self) -> float:
        return max(0.0, self._retry_after_ts - time.monotonic())
