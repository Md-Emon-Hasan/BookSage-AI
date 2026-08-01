"""Pytest fixtures and configuration."""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_books_df():
    """Create sample books DataFrame for testing."""
    return pd.DataFrame({
        "ISBN": ["0001", "0002", "0003", "0004", "0005"],
        "title": [
            "The Great Gatsby",
            "To Kill a Mockingbird",
            "1984",
            "Pride and Prejudice",
            "The Catcher in the Rye"
        ],
        "author": [
            "F. Scott Fitzgerald",
            "Harper Lee",
            "George Orwell",
            "Jane Austen",
            "J.D. Salinger"
        ],
        "year": ["1925", "1960", "1949", "1813", "1951"],
        "publisher": [
            "Scribner",
            "J. B. Lippincott",
            "Secker & Warburg",
            "T. Egerton",
            "Little, Brown"
        ],
        "img_url": [
            "http://example.com/gatsby.jpg",
            "http://example.com/mockingbird.jpg",
            "http://example.com/1984.jpg",
            "http://example.com/pride.jpg",
            "http://example.com/catcher.jpg"
        ]
    })


@pytest.fixture
def sample_users_df():
    """Create sample users DataFrame for testing."""
    return pd.DataFrame({
        "user_id": [1, 2, 3, 4, 5],
        "location": [
            "New York, USA",
            "London, UK",
            "Paris, France",
            "Tokyo, Japan",
            "Sydney, Australia"
        ],
        "age": [25, 30, 35, 40, 28]
    })


@pytest.fixture
def sample_ratings_df():
    """Create sample ratings DataFrame for testing."""
    return pd.DataFrame({
        "user_id": [1, 1, 2, 2, 3, 3, 4, 5, 5, 5],
        "ISBN": [
            "0001", "0002", "0001", "0003",
            "0002", "0004", "0003", "0001", "0004", "0005"
        ],
        "rating": [8, 9, 7, 10, 8, 9, 6, 10, 8, 7]
    })


@pytest.fixture
def sample_books_content_df(sample_books_df):
    """Create sample books content DataFrame for testing."""
    df = sample_books_df.copy()
    df["content_features"] = (
        df["title"] + " " +
        df["author"] + " " +
        df["publisher"] + " " +
        df["year"]
    )
    return df


@pytest.fixture
def sample_final_rating_df(sample_books_df, sample_ratings_df):
    """Create sample final rating DataFrame for testing."""
    merged = sample_ratings_df.merge(sample_books_df, on="ISBN")
    merged["num_ratings"] = 2
    return merged


@pytest.fixture
def mock_engine():
    """Create a mock recommendation engine."""
    engine = MagicMock()
    engine.is_trained = True
    engine.get_popular_books.return_value = [
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "image_url": "http://example.com/gatsby.jpg"
        }
    ]
    engine.get_recommendations.return_value = [
        {
            "title": "1984",
            "author": "George Orwell",
            "year": "1949",
            "publisher": "Secker & Warburg",
            "image_url": "http://example.com/1984.jpg",
            "score": 0.85,
            "type": "hybrid"
        }
    ]
    engine.processed_data = {
        "books_content": pd.DataFrame({
            "title": ["The Great Gatsby", "1984"],
            "author": ["F. Scott Fitzgerald", "George Orwell"],
            "img_url": [
                "http://example.com/gatsby.jpg",
                "http://example.com/1984.jpg"
            ]
        }),
        "books": pd.DataFrame({
            "title": ["The Great Gatsby", "1984"],
            "author": ["F. Scott Fitzgerald", "George Orwell"],
            "img_url": [
                "http://example.com/gatsby.jpg",
                "http://example.com/1984.jpg"
            ]
        }),
        "final_rating": pd.DataFrame({
            "title": ["The Great Gatsby", "1984"],
            "rating": [8, 9]
        })
    }
    return engine


@pytest.fixture
def test_client(mock_engine):
    """Create test client with mocked engine."""
    with patch("app.main.engine", mock_engine):
        from app.main import app
        client = TestClient(app)
        yield client


@pytest.fixture(autouse=True)
def _reset_cache_and_rate_limiter():
    """Clear the response cache and reset rate-limit counters between tests."""
    from app.core.cache import clear_cache
    from app.main import app

    clear_cache()
    app.state.limiter.reset()
    yield
    clear_cache()
    app.state.limiter.reset()
