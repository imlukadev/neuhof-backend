from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Neuhof Live"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://neondb_owner:npg_0pAQt9gZRTdr@ep-broad-flower-ay1hqyqq.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"
    live_source_url: str = "https://www.sv-neuhof.de/livestream"
    live_cache_seconds: int = 300
    scraper_wait_seconds: float = 5
    headless: bool = True
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
