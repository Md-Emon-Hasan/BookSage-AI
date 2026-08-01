"""Tests for the in-memory TTL cache module."""
import time

import pytest

from app.core.cache import cache_stats, cached, clear_cache
from app.core.config import Config


class TestCachedDecorator:
    """Test cases for the @cached decorator."""

    def test_cache_hit_does_not_reinvoke_function(self):
        """A second call with the same args should hit the cache."""
        calls = {"count": 0}

        @cached("test-hit")
        def compute(value):
            calls["count"] += 1
            return {"value": value}

        first = compute("abc")
        second = compute("abc")

        assert first == {"value": "abc"}
        assert second == {"value": "abc"}
        assert calls["count"] == 1

    def test_cache_miss_for_different_args(self):
        """Different arguments should not share a cache entry."""
        calls = {"count": 0}

        @cached("test-miss")
        def compute(value):
            calls["count"] += 1
            return {"value": value}

        compute("abc")
        compute("xyz")

        assert calls["count"] == 2

    def test_ttl_expiry_causes_miss(self):
        """Entries older than the TTL should be recomputed."""
        calls = {"count": 0}

        @cached("test-ttl", ttl=1)
        def compute(value):
            calls["count"] += 1
            return {"value": value}

        compute("abc")
        assert calls["count"] == 1

        time.sleep(1.2)

        compute("abc")
        assert calls["count"] == 2

    def test_key_normalization_case_and_whitespace(self):
        """Different casing/whitespace on the same string should collide."""
        calls = {"count": 0}

        @cached("test-normalize")
        def compute(title):
            calls["count"] += 1
            return {"title": title}

        compute("The Great Gatsby")
        compute("  the great gatsby  ")

        assert calls["count"] == 1

    def test_key_normalization_kwarg_order(self):
        """Kwargs passed in a different order should still hit the cache."""
        calls = {"count": 0}

        @cached("test-kwarg-order")
        def compute(**kwargs):
            calls["count"] += 1
            return {"result": True}

        compute(a="1", b="2")
        compute(b="2", a="1")

        assert calls["count"] == 1

    def test_key_normalization_leaves_non_string_args_untouched(self):
        """Non-string arguments (e.g. counts) are used as-is in the key."""
        calls = {"count": 0}

        @cached("test-non-string")
        def compute(count):
            calls["count"] += 1
            return {"count": count}

        compute(10)
        compute(10)
        compute(20)

        assert calls["count"] == 2

    def test_different_prefixes_do_not_collide(self):
        """Same arguments under different prefixes are cached separately."""
        calls = {"a": 0, "b": 0}

        @cached("prefix-a")
        def compute_a(value):
            calls["a"] += 1
            return {"value": value}

        @cached("prefix-b")
        def compute_b(value):
            calls["b"] += 1
            return {"value": value}

        compute_a("same")
        compute_b("same")

        assert calls["a"] == 1
        assert calls["b"] == 1

    def test_empty_list_result_not_cached(self):
        """Empty list results must never be cached."""
        calls = {"count": 0}

        @cached("test-empty-list")
        def compute():
            calls["count"] += 1
            return []

        compute()
        compute()

        assert calls["count"] == 2

    def test_none_result_not_cached(self):
        """None results must never be cached."""
        calls = {"count": 0}

        @cached("test-empty-none")
        def compute():
            calls["count"] += 1
            return None

        compute()
        compute()

        assert calls["count"] == 2

    def test_non_empty_result_is_cached(self):
        """A non-empty result should be reused on the next call."""
        calls = {"count": 0}

        @cached("test-nonempty")
        def compute():
            calls["count"] += 1
            return ["one item"]

        first = compute()
        second = compute()

        assert first == ["one item"]
        assert second == ["one item"]
        assert calls["count"] == 1

    def test_cache_enabled_false_bypasses_cache(self, monkeypatch):
        """When CACHE_ENABLED is False, the function always re-executes."""
        monkeypatch.setattr(Config, "CACHE_ENABLED", False)
        calls = {"count": 0}

        @cached("test-disabled")
        def compute(value):
            calls["count"] += 1
            return {"value": value}

        compute("abc")
        compute("abc")

        assert calls["count"] == 2


class TestCacheHelpers:
    """Test cases for clear_cache() and cache_stats()."""

    def setup_method(self):
        """Ensure a clean cache state before each test."""
        clear_cache()

    def teardown_method(self):
        """Leave the shared cache clean for other test modules."""
        clear_cache()

    def test_clear_cache_removes_entries_and_resets_counters(self):
        @cached("test-clear")
        def compute(value):
            return {"value": value}

        compute("abc")
        compute("abc")  # hit

        stats_before = cache_stats()
        assert stats_before["size"] > 0
        assert stats_before["hits"] > 0

        clear_cache()

        stats_after = cache_stats()
        assert stats_after["size"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0

    def test_cache_stats_reports_expected_keys(self):
        stats = cache_stats()
        assert set(stats.keys()) == {"size", "maxsize", "ttl", "hits", "misses"}
        assert stats["maxsize"] == Config.CACHE_MAXSIZE
        assert stats["ttl"] == Config.CACHE_TTL_SECONDS

    def test_cache_stats_tracks_hits_and_misses(self):
        @cached("test-stats")
        def compute(value):
            return {"value": value}

        compute("a")  # miss
        compute("a")  # hit
        compute("b")  # miss

        stats = cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2


@pytest.fixture(autouse=True)
def _clean_cache_module_state():
    """Isolate each test in this module from residual cache state."""
    clear_cache()
    yield
    clear_cache()
