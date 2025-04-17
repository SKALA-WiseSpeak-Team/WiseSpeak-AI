# app/audio/stt.py
# Speech-to-Text - 음성을 텍스트로 변환하는 기능

import os
from typing import Dict, List, Any, Optional, Union
import logging
import json
from pathlib import Path
import tempfile

from app.llm.ai.openai_client import get_openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class STTProcessor:
    """음성을 텍스트로 변환하는 프로세서"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
    
    def speech_to_text(
        self, 
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        오디오 파일에서 텍스트 추출
        
        Args:
            audio_file_path: 오디오 파일 경로
            language: 언어 코드 (None이면 자동 감지)
            prompt: 처리 힌트 제공
        
        Returns:
            변환 결과 (텍스트, 감지된 언어 등)
        """
        try:
            # 파일 존재 확인
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")
            
            # 오디오 파일 읽기
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
            
            # STT 변환
            result = self.openai_client.speech_to_text(
                audio_data=audio_data,
                language=language,
                prompt=prompt
            )
            
            logger.info(f"STT 변환 완료: {audio_file_path} ({len(result['text'])} 자)")
            return result
        except Exception as e:
            logger.error(f"STT 변환 실패: {str(e)}")
            return {"text": "", "language": "unknown", "duration": 0, "error": str(e)}
    
    def speech_to_text_from_bytes(
        self, 
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        오디오 바이너리 데이터에서 텍스트 추출
        
        Args:
            audio_data: 오디오 바이너리 데이터
            language: 언어 코드 (None이면 자동 감지)
            prompt: 처리 힌트 제공
        
        Returns:
            변환 결과 (텍스트, 감지된 언어 등)
        """
        try:
            # STT 변환
            result = self.openai_client.speech_to_text(
                audio_data=audio_data,
                language=language,
                prompt=prompt
            )
            
            logger.info(f"바이너리 데이터 STT 변환 완료 ({len(result['text'])} 자)")
            return result
        except Exception as e:
            logger.error(f"바이너리 데이터 STT 변환 실패: {str(e)}")
            return {"text": "", "language": "unknown", "duration": 0, "error": str(e)}
    
    def save_and_transcribe(
        self, 
        audio_data: bytes,
        output_dir: str = settings.AUDIO_DIR,
        filename: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        오디오 데이터를 저장하고 텍스트로 변환
        
        Args:
            audio_data: 오디오 바이너리 데이터
            output_dir: 출력 디렉토리
            filename: 파일 이름 (None이면 임시 파일 사용)
            language: 언어 코드
            prompt: 처리 힌트 제공
        
        Returns:
            변환 결과 및 저장된 파일 경로
        """
        try:
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 파일 저장
            if filename:
                # 확장자가 없으면 mp3 추가
                if not filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg', '.webm')):
                    filename += ".mp3"
                
                file_path = os.path.join(output_dir, filename)
                
                with open(file_path, "wb") as f:
                    f.write(audio_data)
            else:
                # 임시 파일 사용
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=output_dir) as tmp:
                    tmp.write(audio_data)
                    file_path = tmp.name
            
            # STT 변환
            result = self.speech_to_text(
                audio_file_path=file_path,
                language=language,
                prompt=prompt
            )
            
            # 파일 경로 추가
            result["file_path"] = file_path
            
            return result
        except Exception as e:
            logger.error(f"오디오 저장 및 변환 실패: {str(e)}")
            return {"text": "", "language": "unknown", "duration": 0, "error": str(e), "file_path": ""}


def get_stt_processor() -> STTProcessor:
    """
    STTProcessor 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        STTProcessor 인스턴스
    """
    return STTProcessor()


def transcribe_audio_file(
    audio_file_path: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    오디오 파일 변환 헬퍼 함수
    
    Args:
        audio_file_path: 오디오 파일 경로
        language: 언어 코드
        prompt: 처리 힌트 제공
    
    Returns:
        변환 결과
    """
    processor = get_stt_processor()
    return processor.speech_to_text(audio_file_path, language, prompt)