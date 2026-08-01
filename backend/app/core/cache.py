"""In-memory, thread-safe TTL caching for BookSage-AI API responses."""
import functools
import json
import threading
from typing import Any, Callable

from cachetools import TTLCache
from fastapi import Request

from app.core.config import Config
from app.core.logger import logger

_lock = threading.Lock()
_stores: dict[int, TTLCache] = {}
_hits = 0
_misses = 0


def _get_store(ttl: int) -> TTLCache:
    """Get (or lazily create) the TTLCache backing a given TTL bucket."""
    store = _stores.get(ttl)
    if store is None:
        store = TTLCache(maxsize=Config.CACHE_MAXSIZE, ttl=ttl)
        _stores[ttl] = store
    return store


def _normalize(value: Any) -> Any:
    """Normalize a value for deterministic key generation."""
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _make_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Build a deterministic cache key from a function call's arguments."""
    cacheable_args = [
        _normalize(arg) for arg in args if not isinstance(arg, Request)
    ]
    cacheable_kwargs = {
        key: _normalize(value)
        for key, value in sorted(kwargs.items())
        if not isinstance(value, Request)
    }
    payload = {
        "prefix": prefix,
        "args": cacheable_args,
        "kwargs": cacheable_kwargs,
    }
    return json.dumps(payload, sort_keys=True, default=str)


def _is_cacheable(result: Any) -> bool:
    """Only successful, non-empty results are worth caching."""
    if result is None:
        return False
    if isinstance(result, (list, dict, str, tuple, set)) and len(result) == 0:
        return False
    return True


def cached(prefix: str, ttl: int | None = None) -> Callable:
    """Cache a synchronous function's return value, keyed by its normalized arguments."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not Config.CACHE_ENABLED:
                return func(*args, **kwargs)

            global _hits, _misses
            effective_ttl = ttl if ttl is not None else Config.CACHE_TTL_SECONDS
            key = _make_key(prefix, args, kwargs)

            with _lock:
                store = _get_store(effective_ttl)
                if key in store:
                    _hits += 1
                    cached_value = store[key]
                    logger.debug(f"Cache hit for prefix '{prefix}'")
                    return cached_value
                _misses += 1

            result = func(*args, **kwargs)

            if _is_cacheable(result):
                with _lock:
                    _get_store(effective_ttl)[key] = result

            return result

        return wrapper

    return decorator


def clear_cache() -> None:
    """Clear all cached entries and reset hit/miss counters."""
    global _hits, _misses
    with _lock:
        for store in _stores.values():
            store.clear()
        _hits = 0
        _misses = 0


def cache_stats() -> dict[str, int]:
    """Return size, maxsize, ttl, hits, and misses for the cache."""
    with _lock:
        size = sum(len(store) for store in _stores.values())
        return {
            "size": size,
            "maxsize": Config.CACHE_MAXSIZE,
            "ttl": Config.CACHE_TTL_SECONDS,
            "hits": _hits,
            "misses": _misses,
        }
