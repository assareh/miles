"""Configuration management for Miles - fully environment-driven."""

import os

from dotenv import load_dotenv
from llm_tools_server import ServerConfig

# Load environment variables from .env file
load_dotenv()


class MilesConfig(ServerConfig):
    """Miles-specific configuration extending ServerConfig."""

    @classmethod
    def load(cls):
        """Load Miles configuration from environment variables."""
        config = cls.from_env("MILES_")

        # Miles-specific settings
        config.MODEL_NAME = os.getenv("MILES_MODEL_NAME", "askmiles/miles")
        config.DATA_DIR = os.getenv("DATA_DIR", "data")
        config.USER_DATA_FILE = os.getenv("USER_DATA_FILE", "data/user.json")
        config.DATA_API_URL = os.getenv("DATA_API_URL", "https://api.askmiles.ai")

        # WebUI settings
        config.WEBUI_PORT = int(os.getenv("WEBUI_PORT", "8001"))
        config.WEBUI_AUTH = os.getenv("WEBUI_AUTH", "false").lower() == "true"

        # RAG settings
        config.RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
        config.RAG_CACHE_DIR = os.getenv("RAG_CACHE_DIR", "doc_index")
        config.RAG_UPDATE_INTERVAL_HOURS = int(os.getenv("RAG_UPDATE_INTERVAL_HOURS", "168"))  # 7 days
        config.RAG_BM25_WEIGHT = float(os.getenv("RAG_BM25_WEIGHT", "0.4"))
        config.RAG_SEMANTIC_WEIGHT = float(os.getenv("RAG_SEMANTIC_WEIGHT", "0.6"))
        config.RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
        config.RAG_RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "true").lower() == "true"
        config.RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        config.RAG_MAX_CRAWL_DEPTH = int(os.getenv("RAG_MAX_CRAWL_DEPTH", "2"))
        config.RAG_MAX_PAGES = int(os.getenv("RAG_MAX_PAGES", "500")) if os.getenv("RAG_MAX_PAGES") else None
        config.RAG_RATE_LIMIT_DELAY = float(os.getenv("RAG_RATE_LIMIT_DELAY", "0.5"))
        config.RAG_MAX_WORKERS = int(os.getenv("RAG_MAX_WORKERS", "3"))

        # RAG periodic update settings (for long-running applications)
        config.RAG_PERIODIC_UPDATE_ENABLED = os.getenv("RAG_PERIODIC_UPDATE_ENABLED", "false").lower() == "true"
        config.RAG_PERIODIC_UPDATE_INTERVAL_HOURS = float(os.getenv("RAG_PERIODIC_UPDATE_INTERVAL_HOURS", "6.0"))

        # RAG documentation sources (comma-separated URLs)
        config.RAG_DOC_SOURCES = os.getenv("RAG_DOC_SOURCES", "").split(",") if os.getenv("RAG_DOC_SOURCES") else []

        # RAG URL patterns
        config.RAG_URL_INCLUDE_PATTERNS = (
            os.getenv("RAG_URL_INCLUDE_PATTERNS", "").split(",") if os.getenv("RAG_URL_INCLUDE_PATTERNS") else []
        )
        config.RAG_URL_EXCLUDE_PATTERNS = (
            os.getenv("RAG_URL_EXCLUDE_PATTERNS", "").split(",")
            if os.getenv("RAG_URL_EXCLUDE_PATTERNS")
            else [
                ".*/category/.*",
                ".*/tag/.*",
                ".*/author/.*",
                ".*/\\d{4}/\\d{2}/.*",  # Blog date URLs
                ".*/go/.*",  # Go redirect URLs
            ]
        )

        return config


# Create singleton config instance
config = MilesConfig.load()
