"""
SRAGA AI 시스템 환경 설정
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# 디렉토리 생성
for dir_path in [DATA_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

# ChromaDB 설정
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", str(BASE_DIR / "chroma_db"))

# PDF 처리 설정
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")  # Tesseract 실행 파일 경로

# 청킹 설정
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# 다국어 설정
SUPPORTED_LANGUAGES = ["ko", "en", "ja", "zh"]  # 한국어, 영어, 일본어, 중국어
DEFAULT_LANGUAGE = "ko"

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "sraga_ai.log"))

# 벡터 검색 설정
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# 실행 환경 설정
ENV = os.getenv("ENV", "development")  # 'development' 또는 'production'

# 환경 변수 검증
def validate_config():
    """환경 설정 유효성 검사"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    return True

# 설정 출력
def print_config():
    """현재 설정 출력"""
    config_dict = {
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": DATA_DIR,
        "OUTPUT_DIR": OUTPUT_DIR,
        "TEMP_DIR": TEMP_DIR,
        "OPENAI_MODEL": OPENAI_MODEL,
        "OPENAI_EMBEDDING_MODEL": OPENAI_EMBEDDING_MODEL,
        "CHROMA_DB_DIR": CHROMA_DB_DIR,
        "TESSERACT_PATH": TESSERACT_PATH,
        "CHUNK_SIZE": CHUNK_SIZE,
        "CHUNK_OVERLAP": CHUNK_OVERLAP,
        "SUPPORTED_LANGUAGES": SUPPORTED_LANGUAGES,
        "DEFAULT_LANGUAGE": DEFAULT_LANGUAGE,
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_FILE": LOG_FILE,
        "TOP_K_RESULTS": TOP_K_RESULTS,
        "ENV": ENV
    }
    
    for key, value in config_dict.items():
        print(f"{key}: {value}")
