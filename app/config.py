from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_name:str="YouTube AI Factory API"
 app_env:str="development"
 database_path:str="./data/youtube_factory.db"
 cors_origins:str="http://localhost:3000,http://127.0.0.1:3000"
 youtube_data_api_key:str=""
 ollama_base_url:str="http://localhost:11434"
 ollama_model:str="qwen2.5:3b"
 ffmpeg_binary:str="ffmpeg"
 pexels_api_key:str=""
 piper_binary:str="piper"
 piper_model_path:str=""
 max_upload_mb:int=500
 model_config=SettingsConfigDict(env_file=".env",extra="ignore")
 @property
 def allowed_origins(self):return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
@lru_cache
def get_settings():return Settings()
