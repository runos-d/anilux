"""Bound client command frames before JSON parsing and database work."""
import time


class SocketFrameBudget:
    def __init__(self, clock=time.monotonic, maximum_bytes=65536, rate=10, burst=30):
        self.clock, self.maximum_bytes, self.rate, self.burst = clock, maximum_bytes, rate, burst
        self.tokens = burst
        self.updated = clock()

    def reject_code(self, text):
        if not isinstance(text, str):
            return 1003
        if len(text) > self.maximum_bytes or len(text.encode('utf-8')) > self.maximum_bytes:
            return 1009
        now = self.clock()
        self.tokens = min(self.burst, self.tokens + max(0, now - self.updated) * self.rate)
        self.updated = now
        if self.tokens < 1:
            return 4008
        self.tokens -= 1
        return None
