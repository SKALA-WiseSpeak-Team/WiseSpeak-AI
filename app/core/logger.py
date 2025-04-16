# app/core/logger.py
# 로깅 설정 - 애플리케이션 로깅 설정 및 관리

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
import colorlog
from typing import Optional

from app.core.config import BASE_DIR

# 환경 변수에서 로깅 설정 가져오기
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "lecture_rag_system.log")

# 로그 파일 경로
LOG_PATH = os.path.join(BASE_DIR, LOG_FILE)

# 컬러 로그 형식 정의
COLOR_FORMAT = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}

def setup_logger(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름 (None이면 루트 로거)
        level: 로그 레벨 (None이면 환경 변수에서 가져옴)
    
    Returns:
        설정된 로거
    """
    # 로그 레벨 설정
    log_level = getattr(logging, level.upper() if level else LOG_LEVEL)
    
    # 로거 가져오기
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False
    
    # 이미 핸들러가 설정되어 있으면 반환
    if logger.handlers:
        return logger
    
    # 출력 형식 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 파일 핸들러 설정
    file_handler = RotatingFileHandler(
        LOG_PATH, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 설정 (컬러 로그)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        f"%(log_color)s{log_format}",
        datefmt=date_format,
        log_colors=COLOR_FORMAT
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    이름이 지정된 로거 가져오기
    
    Args:
        name: 로거 이름
    
    Returns:
        로거 인스턴스
    """
    return setup_logger(name)

# 루트 로거 설정
root_logger = setup_logger()