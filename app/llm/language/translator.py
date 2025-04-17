# app/language/translator.py
# 번역 기능 - 필요한 경우 언어 간 번역 지원

from typing import Dict, List, Any, Optional, Union
import logging

from app.llm.ai.openai_client import get_openai_client
from app.llm.language.detector import get_language_detector
from app.core.config import settings

logger = logging.getLogger(__name__)

class Translator:
    """번역 클래스"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
        self.language_detector = get_language_detector()
    
    def translate(
        self, 
        text: str, 
        target_language: str, 
        source_language: Optional[str] = None
    ) -> str:
        """
        텍스트 번역
        
        Args:
            text: 번역할 텍스트
            target_language: 대상 언어 코드
            source_language: 원본 언어 코드 (None이면 자동 감지)
        
        Returns:
            번역된 텍스트
        """
        try:
            if not text:
                return ""
            
            # 원본 언어가 지정되지 않았으면 자동 감지
            if source_language is None:
                source_language = self.language_detector.detect_language(text)
            
            # 언어 코드 정리 및 확인
            source_lang = source_language.split('_')[0].lower()
            target_lang = target_language.split('_')[0].lower()
            
            # 이미 같은 언어면 그대로 반환
            if source_lang == target_lang:
                logger.info(f"원본 언어와 대상 언어가 동일합니다: {source_lang}")
                return text
            
            # 대상 언어가 지원되는지 확인
            if not self.language_detector.is_supported_language(target_lang):
                closest_lang = self.language_detector.get_closest_supported_language(target_lang)
                logger.warning(f"지원하지 않는 대상 언어: {target_lang}, {closest_lang}로 대체합니다")
                target_lang = closest_lang
            
            # 언어 이름 매핑
            language_names = {
                "en": "English",
                "ko": "Korean",
                "ja": "Japanese",
                "zh": "Chinese",
                "es": "Spanish",
                "fr": "French",
                "de": "German"
            }
            
            source_lang_name = language_names.get(source_lang, source_lang)
            target_lang_name = language_names.get(target_lang, target_lang)
            
            # 번역 프롬프트 준비
            prompt = [
                {"role": "system", "content": f"You are a professional translator. Translate the provided text from {source_lang_name} to {target_lang_name} accurately while preserving the meaning, tone, and style. Provide only the translated text without any additional notes or explanations."},
                {"role": "user", "content": text}
            ]
            
            # OpenAI API 호출
            response = self.openai_client.chat_completion(
                messages=prompt,
                temperature=0.3,
                max_tokens=len(text) * 2  # 번역 시 텍스트가 길어질 수 있으므로 여유 있게 설정
            )
            
            translated_text = response.get("text", "")
            logger.info(f"번역 완료: {source_lang} -> {target_lang} ({len(text)} -> {len(translated_text)} 자)")
            
            return translated_text
        except Exception as e:
            logger.error(f"번역 실패: {str(e)}")
            return text  # 오류 발생 시 원본 텍스트 반환


def get_translator() -> Translator:
    """
    Translator 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        Translator 인스턴스
    """
    return Translator()


def translate_text(
    text: str, 
    target_language: str, 
    source_language: Optional[str] = None
) -> str:
    """
    텍스트 번역 헬퍼 함수
    
    Args:
        text: 번역할 텍스트
        target_language: 대상 언어 코드
        source_language: 원본 언어 코드 (None이면 자동 감지)
    
    Returns:
        번역된 텍스트
    """
    translator = get_translator()
    return translator.translate(text, target_language, source_language)