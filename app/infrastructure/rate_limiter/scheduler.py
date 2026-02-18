
"""
Priority Queue Scheduler for API Requests.
"""

import asyncio
import time
import heapq
import logging
from typing import List, Optional
from dataclasses import dataclass, field

from app.infrastructure.rate_limiter.bucket import TokenBucket
from app.infrastructure.rate_limiter.breaker import CircuitBreaker

logger = logging.getLogger(__name__)

@dataclass(order=True)
class _QueueItem:
    """Internal item for the priority queue."""
    priority: int
    timestamp: float
    future: asyncio.Future = field(compare=False)

class PriorityScheduler:
    """
    Async Priority Queue Management.
    Ensures high-priority requests (user chat) skip the line before low-priority (parsing).
    """
    def __init__(self, bucket: TokenBucket, breaker: CircuitBreaker):
        self._bucket = bucket
        self._breaker = breaker
        self._queue: List[_QueueItem] = []
        self._lock = asyncio.Lock()
        self._processor_task: Optional[asyncio.Task] = None

    async def wait_for_slot(self, priority: int) -> None:
        """Blocks until a slot is available based on priority."""
        # 1. Optimistic Check: If queue is empty and tokens exist, go!
        async with self._lock:
            if not self._queue and not self._breaker.is_open() and self._bucket.try_consume(1.0):
                return
            
            # 2. Enqueue
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            heapq.heappush(self._queue, _QueueItem(priority, time.monotonic(), future))
            
            # 3. Ensure background processor is running
            if not self._processor_task or self._processor_task.done():
                self._processor_task = loop.create_task(self._process_queue())

        # 4. Wait for our turn
        await future

    async def _process_queue(self):
        """Background loop to process the queue."""
        while True:
            try:
                async with self._lock:
                    if not self._queue:
                        self._processor_task = None
                        return

                    # Check Cooldown
                    if self._breaker.is_open():
                        wait = self._breaker.time_remaining()
                    # Check Tokens
                    elif self._bucket.try_consume(1.0):
                        # SUCCESS: Release top item
                        item = heapq.heappop(self._queue)
                        if not item.future.done():
                            item.future.set_result(True)
                        continue # Check next immediately
                    else:
                        wait = self._bucket.get_wait_time(1.0)
                
                # Sleep without holding lock
                await asyncio.sleep(min(wait, 1.0) if wait > 0 else 0.1)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(1.0)
