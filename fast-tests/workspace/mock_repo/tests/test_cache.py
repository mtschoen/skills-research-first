"""Tests for src/api/cache.py.

Includes test_eviction_after_ttl which sleeps 30 seconds to wait for
real TTL expiry — this single test dominates the suite wall-clock (scenario 8).

Fix: inject a clock or use freezegun / a tiny TTL value instead of sleeping.
"""

import time
import pytest


def test_set_and_get_cached():
    """Cache returns a value immediately after setting it."""
    from src.api.cache import get_cached, set_cached
    set_cached("test_key", {"x": 1}, ttl=60.0)
    assert get_cached("test_key") == {"x": 1}


def test_get_cached_missing_key():
    """Cache returns None for a key that was never set."""
    from src.api.cache import get_cached
    assert get_cached("nonexistent_key_xyz") is None


def test_evict_expired_removes_stale_entries():
    """evict_expired() clears entries whose TTL has elapsed."""
    from src.api.cache import set_cached, get_cached, evict_expired
    set_cached("stale_key", "value", ttl=0.01)
    time.sleep(0.05)
    evict_expired()
    assert get_cached("stale_key") is None


def test_get_cached_returns_none_after_expiry():
    """get_cached returns None once the TTL elapses."""
    from src.api.cache import set_cached, get_cached
    set_cached("expiring_key", "value", ttl=0.01)
    time.sleep(0.05)
    assert get_cached("expiring_key") is None


def test_eviction_after_ttl():
    """Verify that cache items expire after their TTL has elapsed.

    scenario 8: this test sleeps 30 seconds waiting for the default TTL
    to expire. It dominates the suite wall-clock all by itself.

    Fix options:
    - Pass ttl=0.01 and sleep(0.05) instead of sleeping 30s.
    - Inject a clock: cache.set_cached(key, value, ttl=30, clock=mock_clock)
      then advance mock_clock by 31s.
    - Use freezegun: `with freeze_time() as frozen: frozen.tick(delta=31)`
    """
    from src.api.cache import set_cached, get_cached
    set_cached("ttl_test_key", "should_expire", ttl=30.0)
    time.sleep(30)  # scenario 8: the 30-second sleep dominating wall clock
    assert get_cached("ttl_test_key") is None


def test_eviction_loop_cancels_cleanly():
    """eviction_loop stops when the asyncio task is cancelled."""
    import asyncio
    from src.api.cache import eviction_loop

    async def _run():
        task = asyncio.create_task(eviction_loop(True))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(_run())
