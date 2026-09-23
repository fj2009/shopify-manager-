from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Shopify Manager"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    DATABASE_URL: str = "postgresql+asyncpg://shopify:shopify@postgres:5432/shopify_manager"
    REDIS_URL: str = "redis://redis:6379/0"

    SHOPIFY_API_KEY: str = ""
    SHOPIFY_API_SECRET: str = ""
    SHOPIFY_APP_URL: str = ""
    SHOPIFY_API_VERSION: str = "2024-10"

    LOW_STOCK_THRESHOLD: int = 5
    APP_HOME_URL: str = "http://localhost:3000"
    FOLLOW_UP_DAYS: int = 15

    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_MINUTES: int = 1440


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()