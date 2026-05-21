"""In-process LRU cache with TTL eviction."""

import asyncio
import time

_store: dict = {}


def get_cached(key: str):
    """Return cached value for key, or None if missing/expired."""
    entry = _store.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        del _store[key]
        return None
    return value


def set_cached(key: str, value, ttl: float = 60.0):
    """Store value under key with a TTL in seconds."""
    _store[key] = (value, time.time() + ttl)


def evict_expired():
    """Remove all expired entries from the cache."""
    now = time.time()
    expired = [k for k, (_, expires_at) in _store.items() if now > expires_at]
    for key in expired:
        del _store[key]


async def eviction_loop(running):
    """Background loop that periodically evicts expired cache entries.

    scenario 7: the `while running == False` branch is uncovered because
    cancellation arrives via task.cancel() raising CancelledError inside
    asyncio.sleep, not by setting running=False. Restructure to `while True:`
    to eliminate the unreachable branch rather than adding a coverage exclusion.
    """
    while running:  # scenario 7: this branch is uncovered
        await asyncio.sleep(1)
        evict_expired()
