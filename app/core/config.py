import os
from typing import List, Dict, Any
from pathlib import Path
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "WiseSpeak API"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Supabase 설정
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # 스토리지 설정
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "wisespeak")
    
    # OpenAI API 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    OPENAI_TTS_MODEL: str = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    OPENAI_STT_MODEL: str = os.getenv("OPENAI_STT_MODEL", "whisper-1")
    
    # API 서버 설정
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # 파일 경로 설정
    PDF_DIR: str = os.getenv("PDF_DIR", str(BASE_DIR / "data" / "pdf"))
    AUDIO_DIR: str = os.getenv("AUDIO_DIR", str(BASE_DIR / "data" / "audio"))
    
    # Chroma DB 설정
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "data" / "vector_db"))
    
    # 지원 언어 설정
    SUPPORTED_LANGUAGES: str = os.getenv("SUPPORTED_LANGUAGES", "en,ko,ja,zh,es,fr,de").split(",")
    
    # TTS 음성 설정
    TTS_VOICES: dict = {
        "en": "alloy",  # 영어
        "ko": "shimmer",  # 한국어
        "ja": "nova",  # 일본어
        "zh": "echo",  # 중국어
        "es": "onyx",  # 스페인어
        "fr": "alloy",  # 프랑스어
        "de": "fable",  # 독일어
    }
    
    # 경로 생성 함수
    def ensure_directories(self):
        """필요한 디렉토리가 존재하는지 확인하고, 없으면 생성"""
        for path in [self.PDF_DIR, self.AUDIO_DIR, self.CHROMA_DB_DIR]:
            Path(path).mkdir(parents=True, exist_ok=True)

    # 설정 유효성 검사
    def validate_settings(self):
        """필수 설정이 존재하는지 확인"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    class Config:
        case_sensitive = True

 # 초기화
settings = Settings()
