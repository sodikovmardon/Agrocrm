from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "AgroSmart AI Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agrosmart"
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    JWT_SECRET_KEY: str = "change-this-to-a-very-long-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PASSWORD_MIN_LENGTH: int = 8

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.3

    DEFAULT_CURRENCY: str = "UZS"

    RATE_LIMIT_PER_MINUTE: int = 30

    REDIS_ENTRY_TTL_SECONDS: int = 3600

    ALERT_DAILY_MILK_DROP_PERCENT: float = 10.0
    ALERT_FEED_DAYS_REMAINING: int = 5
    ALERT_EXPIRY_DAYS: int = 30

    CELERY_DAILY_METRICS_HOUR: int = 2
    CELERY_DAILY_METRICS_MINUTE: int = 0
    CELERY_ALERTS_HOUR: int = 6
    CELERY_ALERTS_MINUTE: int = 0

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Managed hosts (Railway, Heroku, etc.) give a plain postgres URL,
        # but the async engine needs the +asyncpg driver scheme.
        if v.startswith("postgresql+asyncpg://"):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    @property
    def jwt_access_expire_delta_seconds(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def jwt_refresh_expire_delta_seconds(self) -> int:
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400


settings = Settings()
