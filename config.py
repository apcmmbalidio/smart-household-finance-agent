# ============================================================
# Smart Household Finance Agent — Configuration & Supabase
# ============================================================

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()


# ── Environment Variable Helpers ──────────────────────────

def _require_env(key: str) -> str:
    """Fetch a required environment variable or raise a clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: '{key}'. "
            f"Please set it in your .env file."
        )
    return value


# ── App Configuration ─────────────────────────────────────

class Config:
    """Central configuration object for the application."""

    # Anthropic
    ANTHROPIC_API_KEY: str = _require_env("ANTHROPIC_API_KEY")

    # Supabase
    SUPABASE_URL: str = _require_env("SUPABASE_URL")
    SUPABASE_ANON_KEY: str = _require_env("SUPABASE_ANON_KEY")

    # App meta
    APP_ENV: str = os.getenv("APP_ENV", "production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Claude model to use for vision analysis
    CLAUDE_MODEL: str = "claude-opus-4-5"

    # Supported image MIME types
    SUPPORTED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]

    # Database table names
    TABLE_EXPENSES: str = "expenses"
    TABLE_CATEGORIES: str = "categories"


# ── Supabase Client (singleton) ───────────────────────────

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_ANON_KEY,
        )
    return _supabase_client


# Convenience alias
config = Config()
