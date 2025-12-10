from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from .config import RATE_LIMIT_PER_HOUR


class RateLimiter:
    """Simple sliding-window rate limiter keyed by sender address."""

    def __init__(self, max_events: int = RATE_LIMIT_PER_HOUR, window_seconds: int = 3600):
        self.max_events = max_events
        self.window = window_seconds
        self.events: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, sender: str) -> bool:
        now = time.time()
        bucket = self.events[sender]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.max_events:
            return False
        bucket.append(now)
        return True
