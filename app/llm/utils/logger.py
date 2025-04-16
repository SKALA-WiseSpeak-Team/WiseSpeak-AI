"""
로깅 유틸리티
"""
import os
import sys
from pathlib import Path
from loguru import logger

from ..config import config

# 로그 디렉토리 생성
log_dir = Path(config.LOG_FILE).parent
os.makedirs(log_dir, exist_ok=True)

# 기본 로거 설정 제거
logger.remove()

# 콘솔 로거 추가
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL,
)

# 파일 로거 추가
logger.add(
    config.LOG_FILE,
    rotation="10 MB",  # 10MB마다 로그 파일 교체
    retention="1 month",  # 1개월 동안 로그 보관
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=config.LOG_LEVEL,
)

def get_logger(name):
    """모듈별 로거 생성
    
    Args:
        name (str): 모듈 이름
    
    Returns:
        loguru.logger: 로거 인스턴스
    """
    return logger.bind(name=name)
