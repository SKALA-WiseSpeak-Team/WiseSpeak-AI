"""
파일 처리 유틸리티
"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional

from .logger import get_logger
from ..config import config

logger = get_logger(__name__)

def ensure_directory(directory_path: str) -> str:
    """디렉토리가 존재하는지 확인하고, 없으면 생성
    
    Args:
        directory_path (str): 디렉토리 경로
    
    Returns:
        str: 생성된 디렉토리 경로
    """
    dir_path = Path(directory_path)
    os.makedirs(dir_path, exist_ok=True)
    return str(dir_path)

def get_file_hash(file_path: str) -> str:
    """파일의 SHA-256 해시 생성
    
    Args:
        file_path (str): 파일 경로
    
    Returns:
        str: 파일 해시
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def get_temp_path(file_name: Optional[str] = None) -> str:
    """임시 파일 경로 반환
    
    Args:
        file_name (Optional[str], optional): 파일 이름. 제공되지 않으면 임시 디렉토리만 반환
    
    Returns:
        str: 임시 파일 경로
    """
    if file_name:
        return str(config.TEMP_DIR / file_name)
    return str(config.TEMP_DIR)

def clean_temp_directory():
    """임시 디렉토리 정리"""
    try:
        if config.TEMP_DIR.exists():
            for item in config.TEMP_DIR.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        logger.info(f"임시 디렉토리 정리 완료: {config.TEMP_DIR}")
    except Exception as e:
        logger.error(f"임시 디렉토리 정리 중 오류 발생: {e}")

def get_file_extension(file_path: str) -> str:
    """파일 확장자 반환
    
    Args:
        file_path (str): 파일 경로
    
    Returns:
        str: 파일 확장자 (소문자로 변환)
    """
    return Path(file_path).suffix.lower()

def is_valid_pdf(file_path: str) -> bool:
    """유효한 PDF 파일인지 검사
    
    Args:
        file_path (str): 파일 경로
    
    Returns:
        bool: 유효한 PDF 파일이면 True, 아니면 False
    """
    if not Path(file_path).exists():
        logger.error(f"파일이 존재하지 않습니다: {file_path}")
        return False
    
    if get_file_extension(file_path) != ".pdf":
        logger.error(f"PDF 파일이 아닙니다: {file_path}")
        return False
    
    # PDF 매직 넘버 확인
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception as e:
        logger.error(f"PDF 파일 검증 중 오류 발생: {e}")
        return False
