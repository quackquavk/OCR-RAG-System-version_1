
"""
Token Bucket Algorithm Implementation.
"""

import time

class TokenBucket:
    """
    Pure logic component. Handles token math.
    Not aware of async, threads, or retries.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._refill_rate = refill_rate
        self._last_refill = time.monotonic()

    def try_consume(self, cost: float = 1.0) -> bool:
        """Attempts to consume tokens. Returns True if successful."""
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    def get_wait_time(self, cost: float) -> float:
        """Returns seconds to wait until enough tokens are available."""
        self._refill()
        needed = cost - self._tokens
        if needed <= 0:
            return 0.0
        return needed / self._refill_rate

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            added = elapsed * self._refill_rate
            self._tokens = min(self._capacity, self._tokens + added)
            self._last_refill = now
