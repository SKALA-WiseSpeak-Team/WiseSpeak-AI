"""
SRAGA AI 패키지
"""
from pathlib import Path
import os

# 환경 변수 기본값 설정 (패키지 임포트 시)
if "OPENAI_API_KEY" not in os.environ:
    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv()

__version__ = "0.1.0"
__author__ = "SRAGA Team"
