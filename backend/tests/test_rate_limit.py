"""Tests for slowapi rate limiting on FastAPI endpoints."""
from app.core.config import Config
from app.main import app


def _limit_amount(limit_string: str) -> int:
    """Extract the numeric amount from a limit string like '30/minute'."""
    return int(limit_string.split("/")[0])


class TestRateLimiting:
    """Test cases for rate limiting behavior."""

    def test_requests_under_limit_succeed(self, test_client):
        """A handful of requests, well under the limit, should all succeed."""
        for _ in range(5):
            response = test_client.get("/api/popular")
            assert response.status_code == 200

    def test_exceeding_limit_returns_429_with_expected_body(self, test_client):
        """Requests beyond the configured limit return a clean 429 body."""
        limit = _limit_amount(Config.RATE_LIMIT_RECOMMEND)

        last_response = None
        for _ in range(limit + 1):
            last_response = test_client.post(
                "/api/recommend",
                data={"book_title": "The Great Gatsby", "method": "hybrid"}
            )

        assert last_response.status_code == 429
        assert last_response.json() == {
            "detail": "Rate limit exceeded. Please try again shortly."
        }
        assert "Retry-After" in last_response.headers

    def test_forwarded_for_creates_separate_buckets(self, test_client):
        """Different X-Forwarded-For values are rate limited independently."""
        limit = _limit_amount(Config.RATE_LIMIT_SEARCH)

        for _ in range(limit):
            response = test_client.get(
                "/api/search_books?query=gatsby",
                headers={"X-Forwarded-For": "10.0.0.1"}
            )
            assert response.status_code == 200

        blocked = test_client.get(
            "/api/search_books?query=gatsby",
            headers={"X-Forwarded-For": "10.0.0.1"}
        )
        assert blocked.status_code == 429

        # A different client IP has its own, untouched bucket.
        allowed = test_client.get(
            "/api/search_books?query=gatsby",
            headers={"X-Forwarded-For": "10.0.0.2"}
        )
        assert allowed.status_code == 200

    def test_health_check_is_never_rate_limited(self, test_client):
        """/api/health has no configured limit, however many times it's hit."""
        limit = _limit_amount(Config.RATE_LIMIT_POPULAR)
        for _ in range(limit + 5):
            response = test_client.get("/api/health")
            assert response.status_code == 200

    def test_rate_limit_disabled_allows_unlimited_requests(self, test_client):
        """Toggling the limiter off removes all enforcement."""
        original_enabled = app.state.limiter.enabled
        app.state.limiter.enabled = False
        try:
            limit = _limit_amount(Config.RATE_LIMIT_RECOMMEND)
            for _ in range(limit + 5):
                response = test_client.post(
                    "/api/recommend",
                    data={"book_title": "The Great Gatsby", "method": "hybrid"}
                )
                assert response.status_code == 200
        finally:
            app.state.limiter.enabled = original_enabled
