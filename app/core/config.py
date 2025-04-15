import os
from typing import List
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "WiseSpeak API"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Supabase 설정
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 스토리지 설정
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "wisespeak")
    
    # API 서버 설정
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")

    class Config:
        case_sensitive = True

settings = Settings()