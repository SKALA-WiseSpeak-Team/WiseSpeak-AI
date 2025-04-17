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
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = os.getenv("BACKEND_CORS_ORIGINS")
    
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
    
    VOICE_CHARACTERISTICS: dict[str, dict[str, str]] = {
        # 각 목소리별 특성 정의
        "alloy": {
            "age": "50대",
            "role": "교수",
            "style": "정중하고 학술적인 어조, 약간의 울림이 있는 목소리",
            "speed": "중간 속도",
            "features": "전문적인 뉘앙스, 가끔 짧은 생각하는 멈춤, 중요 개념 강조 시 속도 조절",
            "culture": "미국, 영국, 캐나다 등 다양한 영어권 문화에 적합"
        },
        "echo": {
            "age": "40대",
            "role": "전문 강사",
            "style": "명확하고 자신감 있는 발음, 적절한 강약 변화",
            "speed": "중간~빠른 속도",
            "features": "질문할 때 음성 높낮이 변화, 중요 포인트에서 잠시 멈춤",
            "culture": "중국 및 아시아 교육 환경에 적합"
        },
        "fable": {
            "age": "30대",
            "role": "차분한 내레이터",
            "style": "부드럽고 따뜻한 어조, 편안한 발음",
            "speed": "중간~느린 속도",
            "features": "이야기를 들려주듯 자연스러운 흐름, 개념 설명 시 명확한 발음",
            "culture": "독일어권 및 유럽 교육 환경에 적합"
        },
        "onyx": {
            "age": "45대",
            "role": "권위 있는 전문가",
            "style": "깊고, 울림 있는 목소리, 확신에 찬 어조",
            "speed": "중간 속도",
            "features": "중요 개념 강조 시 속도 감소, 문장 사이 자연스러운 휴식",
            "culture": "스페인어권 및 라틴 아메리카 교육 환경에 적합"
        },
        "nova": {
            "age": "35대",
            "role": "활기찬 교육자",
            "style": "밝고 생동감 있는 어조, 명확한 발음",
            "speed": "중간~빠른 속도",
            "features": "질문 형식 사용, 강의 내용에 대한 열정적 전달, 짧은 유머 활용",
            "culture": "일본 및 동아시아 교육 환경에 적합"
        },
        "shimmer": {
            "age": "40대",
            "role": "친근한 멘토",
            "style": "부드럽고 친근한 어조, 명확한 발음, 적절한 강약 변화",
            "speed": "중간 속도",
            "features": "'함께 알아보아요', '이해하셨나요?' 같은 참여 유도 표현 사용",
            "culture": "한국 교육 문화에 적합한 존댓말과 예의 바른 표현"
        },
        "ash": {
            "age": "45대",
            "role": "분석적 전문가",
            "style": "냉철하고 논리적인, 정확한 발음",
            "speed": "중간 속도",
            "features": "데이터와 사실에 기반한 설명, 복잡한 개념을 단계별로 분석",
            "culture": "북미 및 유럽의 학술적 환경에 적합"
        },
        "ballad": {
            "age": "50대",
            "role": "철학적 교육자",
            "style": "깊이 있고 사려 깊은 어조, 여유 있는 속도",
            "speed": "느린~중간 속도",
            "features": "개념의 본질을 탐구하는 성찰적 접근, 깊이 있는 질문 던지기",
            "culture": "다양한 문화권의 인문학적 교육 환경에 적합"
        },
        "coral": {
            "age": "30대",
            "role": "창의적 퍼실리테이터",
            "style": "활기차고 열정적인 어조, 흥미로운 억양 변화",
            "speed": "중간~빠른 속도",
            "features": "학습자의 상상력과 창의성을 자극하는 질문, 사례 중심 설명",
            "culture": "서구권의 참여형 교육 환경에 적합"
        },
        "sage": {
            "age": "60대",
            "role": "지혜로운 원로 교수",
            "style": "깊고 차분한 어조, 경험에서 우러나오는 설득력",
            "speed": "느린~중간 속도",
            "features": "이론과 실제를 연결하는 통찰력, 오랜 경험에서 나오는 일화 공유",
            "culture": "다양한 문화권의 학술 및 전통적 교육 환경에 적합"
        }
    }
    
    # 자연스러운 강의 톤을 위한 TTS 설정
    TTS_SPEECH_PATTERNS: dict[str, dict[str, float | list[int]]] = {
        # 속도 변화 패턴
        "speed_variations": {
            "new_topic": 0.9,        # 새로운 주제 도입: 약간 느린 속도 (기본 속도의 90%)
            "core_concept": 1.0,     # 핵심 개념 설명: 중간 속도 (기본 속도의 100%)
            "important_point": 0.85,  # 중요 포인트 강조: 더 느린 속도 (기본 속도의 85%)
            "examples": 1.1,         # 예시나 사례 설명: 약간 빠른 속도 (기본 속도의 110%)
            "humor": 1.15,          # 유머나 일화 공유: 빠른 속도 (기본 속도의 115%)
            "summary": 1.0,         # 마무리 및 요약: 중간 속도 (기본 속도의 100%)
            "page_transition": 0.8   # 페이지 전환 안내: 느린 속도 (기본 속도의 80%)
        },
        
        # 휴지(멈춤) 패턴 (밀리초 단위)
        "pause_patterns": {
            "sentence": [300, 500],       # 문장 사이: 짧은 휴지
            "paragraph": [700, 900],      # 단락 사이: 중간 휴지
            "key_concept": [900, 1100],   # 주요 개념 전후: 긴 휴지
            "after_question": [1000, 1200], # 질문 후: 생각할 시간을 위한 휴지
            "after_humor": [800, 1000],    # 유머 표현 후: 반응을 위한 휴지
            "before_emphasis": [500, 700],  # 중요 정보 강조 전: 주의 집중을 위한 짧은 휴지
            "before_transition": [1100, 1300] # 페이지 전환 안내 전: 내용 정리를 위한 긴 휴지
        }
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
