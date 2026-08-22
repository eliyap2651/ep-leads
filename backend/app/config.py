from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "EP LEADS"
    ENV: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"  # noqa: S105 - dev fallback only, override in .env
    API_V1_PREFIX: str = "/api"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ep_leads:ep_leads@postgres:5432/ep_leads"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://ep_leads:ep_leads@postgres:5432/ep_leads"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Auth
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # AI (Anthropic) - never hardcode a real key; set in environment
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"

    # Search adapter
    SEARCH_PROVIDER: str = "serper"  # serper | bing | google_cse | none
    SERPER_API_KEY: str | None = None
    BING_API_KEY: str | None = None
    GOOGLE_CSE_API_KEY: str | None = None
    GOOGLE_CSE_CX: str | None = None

    # Email (SMTP)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "alerts@ep-leads.local"
    SMTP_USE_TLS: bool = True

    # Scoring
    LEAD_SCORE_THRESHOLD_HOT: int = 90
    LEAD_SCORE_THRESHOLD_HIGH: int = 75
    LEAD_SCORE_THRESHOLD_MEDIUM: int = 55

    # File storage
    STORAGE_DIR: str = "/data/documents"

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "200/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
