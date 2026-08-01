"""Configuration module for BookSage-AI."""
from pathlib import Path


class Config:
    """Application configuration."""

    # Paths
    BASE_DIR = Path(__file__).parent.parent.absolute()
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    LOGS_DIR = BASE_DIR / "logs"
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    STATIC_DIR = PROJECT_ROOT / "static"
    NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

    # Data files
    BOOKS_FILE = "BX-Books.csv"
    USERS_FILE = "BX-Users.csv"
    RATINGS_FILE = "BX-Book-Ratings.csv"

    # Model parameters
    MIN_USER_RATINGS = 200
    MIN_BOOK_RATINGS = 50
    TFIDF_MAX_FEATURES = 10000

    # Recommendation parameters
    DEFAULT_TOP_N = 10
    HYBRID_CF_WEIGHT = 0.6
    HYBRID_CB_WEIGHT = 0.4

    # Image settings
    DEFAULT_IMAGE_URL = "https://via.placeholder.com/150x220?text=No+Image"

    # Server settings
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False

    # Caching settings (in-memory, TTL-based)
    CACHE_ENABLED = True
    CACHE_TTL_SECONDS = 3600
    CACHE_MAXSIZE = 1000
    POPULAR_CACHE_TTL_SECONDS = 86400

    # Rate limiting settings
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_RECOMMEND = "30/minute"
    RATE_LIMIT_SEARCH = "60/minute"
    RATE_LIMIT_POPULAR = "60/minute"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create required directories if they don't exist."""
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.MODELS_DIR.mkdir(exist_ok=True)
