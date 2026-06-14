from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    QDRANT_URL: str
    QDRANT_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    JWT_SECRET: str
    FRONTEND_URL: str
    COLLECTION_NAME: str = "animatch"
    TOP_K: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
