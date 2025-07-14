"""Application configuration using pydantic-settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = Field(default="Sports Betting Edge Finder")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API Keys
    odds_api_key: str = Field(..., description="The Odds API key")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./sportsbetting.db",
        description="Database connection URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )

    # Security
    secret_key: str = Field(
        default="your-secret-key-here",
        description="Secret key for JWT encoding"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Betting Settings
    alert_threshold_edge: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum edge percentage to trigger alert"
    )
    max_kelly_fraction: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Maximum Kelly fraction for bet sizing"
    )
    cache_ttl_seconds: int = Field(
        default=60,
        ge=0,
        description="Cache TTL in seconds"
    )

    # The Odds API Settings
    odds_api_base_url: str = Field(
        default="https://api.the-odds-api.com/v4",
        description="The Odds API base URL"
    )
    odds_api_timeout: int = Field(
        default=30,
        description="API request timeout in seconds"
    )
    odds_api_retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for API requests"
    )

    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is valid."""
        if v.startswith(("postgresql://", "postgres://", "sqlite+aiosqlite:///")):
            return v
        raise ValueError("Database URL must be PostgreSQL or SQLite")

    @validator("redis_url", "celery_broker_url", "celery_result_backend")
    def validate_redis_url(cls, v: str) -> str:
        """Ensure Redis URLs are valid."""
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v


# Global settings instance
settings = Settings()