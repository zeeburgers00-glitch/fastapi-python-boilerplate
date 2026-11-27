from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouTube AI Factory API"
    app_env: str = "development"
    database_path: str = "./data/youtube_factory.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    api_key: str = ""  # Required for API routes when APP_ENV=production
    llm_provider: str = "auto"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto:free"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    youtube_data_api_key: str = ""
    ffmpeg_binary: str = "ffmpeg"
    pexels_api_key: str = ""
    piper_binary: str = "piper"
    piper_model_path: str = ""
    sadtalker_path: str = ""
    avatar_python: str = "python"
    max_upload_mb: int = 500
    max_stock_download_mb: int = 250
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings():
    return Settings()
