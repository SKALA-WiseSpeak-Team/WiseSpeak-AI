# app/language/detector.py
# 언어 감지 - 입력 텍스트/음성의 언어 감지 및 지원 언어 확인

from typing import Dict, List, Any, Optional, Union
import logging

from langdetect import detect, detect_langs, LangDetectException
from app.core.config import settings

logger = logging.getLogger(__name__)

class LanguageDetector:
    """언어 감지 클래스"""
    
    def __init__(self, supported_languages: List[str] = settings.SUPPORTED_LANGUAGES):
        """
        초기화
        
        Args:
            supported_languages: 지원하는 언어 코드 리스트
        """
        self.supported_languages = supported_languages
    
    def detect_language(self, text: str) -> str:
        """
        텍스트의 언어 감지
        
        Args:
            text: 언어를 감지할 텍스트
        
        Returns:
            감지된 언어 코드 (감지 실패 시 'en')
        """
        try:
            if not text or len(text.strip()) < 5:
                logger.warning(f"텍스트가 너무 짧아 언어 감지가 어렵습니다: '{text}'")
                return "en"
            
            # 언어 감지
            detected = detect(text)
            
            # 언어 코드 정리 (예: 'ko_KR' -> 'ko')
            lang_code = detected.split('_')[0].lower()
            
            logger.info(f"언어 감지 결과: {lang_code} (원본 텍스트 길이: {len(text)}자)")
            return lang_code
        except LangDetectException as e:
            logger.error(f"언어 감지 실패: {str(e)}")
            return "en"
        except Exception as e:
            logger.error(f"언어 감지 중 오류 발생: {str(e)}")
            return "en"
    
    def detect_language_with_confidence(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트의 언어 감지 (확률 포함)
        
        Args:
            text: 언어를 감지할 텍스트
        
        Returns:
            감지된 언어 및 확률 리스트
        """
        try:
            if not text or len(text.strip()) < 5:
                logger.warning(f"텍스트가 너무 짧아 언어 감지가 어렵습니다: '{text}'")
                return [{"lang": "en", "prob": 1.0}]
            
            # 언어 감지
            detected_langs = detect_langs(text)
            
            # 결과 리스트로 변환
            result = []
            for lang in detected_langs:
                # 언어 코드 정리 (예: 'ko_KR' -> 'ko')
                lang_code = lang.lang.split('_')[0].lower()
                result.append({
                    "lang": lang_code,
                    "prob": lang.prob
                })
            
            logger.info(f"언어 감지 결과 (상위 3개): {result[:3]}")
            return result
        except LangDetectException as e:
            logger.error(f"언어 감지 실패: {str(e)}")
            return [{"lang": "en", "prob": 1.0}]
        except Exception as e:
            logger.error(f"언어 감지 중 오류 발생: {str(e)}")
            return [{"lang": "en", "prob": 1.0}]
    
    def is_supported_language(self, language_code: str) -> bool:
        """
        지원하는 언어인지 확인
        
        Args:
            language_code: 언어 코드
        
        Returns:
            지원 여부
        """
        # 언어 코드 정리 (예: 'ko_KR' -> 'ko')
        lang_code = language_code.split('_')[0].lower()
        
        return lang_code in self.supported_languages
    
    def get_closest_supported_language(self, language_code: str) -> str:
        """
        가장 가까운 지원 언어 반환
        
        Args:
            language_code: 언어 코드
        
        Returns:
            가장 가까운 지원 언어 코드
        """
        # 언어 코드 정리 (예: 'ko_KR' -> 'ko')
        lang_code = language_code.split('_')[0].lower()
        
        # 이미 지원하는 언어면 그대로 반환
        if self.is_supported_language(lang_code):
            return lang_code
        
        # 언어 매핑 (비슷한 언어 그룹)
        language_groups = {
            # 중국어 방언
            "zh": ["zh-cn", "zh-tw", "zh-hk"],
            # 영어 변형
            "en": ["en-us", "en-gb", "en-au", "en-ca"],
            # 스페인어 변형
            "es": ["es-es", "es-mx", "es-ar"],
            # 프랑스어 변형
            "fr": ["fr-fr", "fr-ca"],
            # 독일어 변형
            "de": ["de-de", "de-at", "de-ch"]
        }
        
        # 언어 그룹에서 매칭 확인
        for supported_lang, variants in language_groups.items():
            if lang_code in variants:
                return supported_lang
        
        # 매칭되는 것이 없으면 영어 반환
        logger.warning(f"지원하지 않는 언어: {language_code}, 영어로 대체합니다")
        return "en"


def get_language_detector() -> LanguageDetector:
    """
    LanguageDetector 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        LanguageDetector 인스턴스
    """
    return LanguageDetector()


def detect_text_language(text: str) -> str:
    """
    텍스트 언어 감지 헬퍼 함수
    
    Args:
        text: 언어를 감지할 텍스트
    
    Returns:
        감지된 언어 코드
    """
    detector = get_language_detector()
    return detector.detect_language(text)