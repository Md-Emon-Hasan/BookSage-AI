"""FastAPI application for BookSage-AI."""
from contextlib import asynccontextmanager
from typing import Any

import pandas as pd
from fastapi import FastAPI, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.cache import cached
from app.core.config import Config
from app.core.logger import logger
from app.services.recommendation_engine import RecommendationEngine

# Global recommendation engine instance
engine: RecommendationEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global engine

    # Startup: Load models
    logger.info("Starting BookSage-AI application...")
    Config.ensure_directories()

    engine = RecommendationEngine()
    if not engine.load_trained_models():
        logger.warning(
            "No pre-trained models found. "
            "Please train models first using the training script."
        )

    yield

    # Shutdown
    logger.info("Shutting down BookSage-AI application...")


# Create FastAPI app
app = FastAPI(
    title="BookSage-AI",
    description="AI-powered book recommendation system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    """Resolve the rate-limiting key, preferring the first X-Forwarded-For hop."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip, enabled=Config.RATE_LIMIT_ENABLED)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return a clean JSON error body with a Retry-After header on 429."""
    retry_after = exc.limit.limit.get_expiry()
    logger.warning(
        f"Rate limit exceeded for {get_client_ip(request)} "
        f"on {request.url.path}"
    )
    response = JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again shortly."},
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


@cached("recommend")
def _get_cached_recommendations(
    book_title: str, method: str
) -> list[dict[str, Any]]:
    """Compute recommendations for a book/method pair (cached)."""
    return engine.get_recommendations(
        book_title=book_title,
        method=method,
        top_n=10
    )


@app.get("/api/popular", response_class=JSONResponse)
@limiter.limit(Config.RATE_LIMIT_POPULAR)
@cached("popular", ttl=Config.POPULAR_CACHE_TTL_SECONDS)
def get_popular_books(request: Request) -> list[dict[str, Any]]:
    """Get popular books."""
    popular_books = []
    if engine and engine.is_trained:
        popular_books = engine.get_popular_books(limit=10)
    return popular_books


@app.post("/api/recommend", response_class=JSONResponse)
@limiter.limit(Config.RATE_LIMIT_RECOMMEND)
def recommend(
    request: Request,
    book_title: str = Form(...),
    method: str = Form(default="hybrid")
) -> dict[str, Any]:
    """Get book recommendations."""
    recommendations: list[dict[str, Any]] = []
    selected_book: dict[str, Any] | None = None

    if engine and engine.is_trained:
        # Get selected book details
        selected_book = engine.get_book_info(book_title)

        # Get recommendations
        recommendations = _get_cached_recommendations(book_title, method)
        logger.info(
            f"Generated {len(recommendations)} {method} recommendations "
            f"for '{book_title}'"
        )

    return {
        "recommendations": recommendations,
        "book_title": book_title,
        "method": method,
        "selected_book": selected_book
    }


@app.get("/api/search_books", response_class=JSONResponse)
@limiter.limit(Config.RATE_LIMIT_SEARCH)
@cached("search_books")
def search_books(
    request: Request,
    query: str = Query(default="")
) -> list[dict[str, Any]]:
    """
    Search for books by title.
    """
    if not query:
        return []

    if not engine or not engine.is_trained:
        logger.warning("Engine not ready for search")
        return []

    query_lower = query.lower()

    # Search in books_content
    books_content = engine.processed_data["books_content"]
    matching_books = books_content[
        books_content["title"].str.lower().str.contains(
            query_lower, na=False
        )
    ]

    # If not enough results, search in books
    if len(matching_books) < 5:
        books = engine.processed_data["books"]
        additional = books[
            books["title"].str.lower().str.contains(query_lower, na=False)
        ]
        matching_books = pd.concat(
            [matching_books, additional]
        ).drop_duplicates("title")

    results = []
    for _, row in matching_books.head(9).iterrows():
        img_url = row["img_url"]
        if not isinstance(img_url, str) or not img_url.startswith("http"):
            img_url = Config.DEFAULT_IMAGE_URL

        results.append({
            "title": row["title"],
            "author": row["author"],
            "image_url": img_url
        })

    logger.debug(f"Search for '{query}' returned {len(results)} results")
    return results


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "models_loaded": engine.is_trained if engine else False,
        "version": "2.0.0"
    }


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True
    )
