"""Application configuration using pydantic BaseSettings.

SECURITY: All sensitive values must be loaded from environment variables.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Jade SmartBank"
    app_version: str = "1.0.0"
    debug: bool = False

    # SECURITY: JWT Configuration
    secret_key: str  # REQUIRED 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # SECURITY: Password Policy
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    # SECURITY: Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Database
    database_url: str  # REQUIRED
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings singleton
    """
    return Settings()
