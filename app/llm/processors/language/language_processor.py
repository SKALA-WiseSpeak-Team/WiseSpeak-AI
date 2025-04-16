"""
다국어 처리 모듈
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from langdetect import detect, DetectorFactory
from googletrans import Translator

from ...config import config
from ...utils.logger import get_logger

# 언어 감지 결과 일관성 유지
DetectorFactory.seed = 0

logger = get_logger(__name__)

class LanguageProcessor:
    """다국어 처리 클래스"""
    
    def __init__(self, 
                supported_languages: List[str] = None,
                default_language: str = None):
        """다국어 처리기 초기화
        
        Args:
            supported_languages (List[str], optional): 지원하는 언어 코드 목록. 기본값은 config에서 로드
            default_language (str, optional): 기본 언어 코드. 기본값은 config에서 로드
        """
        self.supported_languages = supported_languages or config.SUPPORTED_LANGUAGES
        self.default_language = default_language or config.DEFAULT_LANGUAGE
        self.translator = Translator()
        
        # 언어 코드 매핑 (langdetect와 googletrans 간 차이 해결)
        self.lang_code_map = {
            "ko": "ko",  # 한국어
            "en": "en",  # 영어
            "ja": "ja",  # 일본어
            "zh-cn": "zh",  # 중국어 간체
            "zh-tw": "zh-tw"  # 중국어 번체
        }
        
        # 영어 언어명 매핑
        self.lang_name_map = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese (Simplified)",
            "zh-tw": "Chinese (Traditional)"
        }
        
        logger.info(f"다국어 처리기 초기화 완료 (지원 언어: {', '.join(self.supported_languages)})")
    
    def detect_language(self, text: str) -> str:
        """텍스트의 언어 감지
        
        Args:
            text (str): 언어를 감지할 텍스트
        
        Returns:
            str: 감지된 언어 코드 (지원하지 않는 언어는 기본 언어 반환)
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트의 언어 감지가 무시되었습니다")
            return self.default_language
        
        try:
            detected = detect(text)
            
            # 중국어 구분 (간체/번체)
            if detected == "zh-cn" or detected == "zh-tw":
                normalized_lang = detected
            else:
                # 언어 코드 정규화
                normalized_lang = detected.split("-")[0]
            
            # 지원하는 언어인지 확인
            if normalized_lang in self.supported_languages:
                logger.info(f"텍스트 언어 감지 결과: {normalized_lang}")
                return normalized_lang
            else:
                logger.warning(f"감지된 언어 {normalized_lang}은(는) 지원되지 않아 기본 언어 {self.default_language}로 대체됩니다")
                return self.default_language
        except Exception as e:
            logger.error(f"언어 감지 중 오류 발생: {e}")
            return self.default_language
    
    def translate_text(self, 
                    text: str, 
                    target_language: str, 
                    source_language: Optional[str] = None) -> str:
        """텍스트 번역
        
        Args:
            text (str): 번역할 텍스트
            target_language (str): 대상 언어 코드
            source_language (Optional[str], optional): 원본 언어 코드. 기본값은 자동 감지
        
        Returns:
            str: 번역된 텍스트
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트의 번역이 무시되었습니다")
            return ""
        
        # 대상 언어가 지원되는지 확인
        if target_language not in self.supported_languages:
            logger.warning(f"대상 언어 {target_language}은(는) 지원되지 않습니다")
            return text
        
        # 소스 언어가 제공되지 않으면 감지
        if not source_language:
            source_language = self.detect_language(text)
        
        # 이미 대상 언어와 같으면 번역 불필요
        if source_language == target_language:
            logger.info(f"텍스트가 이미 {target_language} 언어입니다")
            return text
        
        try:
            # 구글 번역 API 사용
            translation = self.translator.translate(
                text, 
                dest=self.lang_code_map.get(target_language, target_language),
                src=self.lang_code_map.get(source_language, source_language)
            )
            
            logger.info(f"{source_language}에서 {target_language}로 텍스트 번역 완료")
            return translation.text
        except Exception as e:
            logger.error(f"텍스트 번역 중 오류 발생: {e}")
            return text
    
    def translate_chunks(self, 
                        chunks: List[Dict[str, Any]], 
                        target_language: str) -> List[Dict[str, Any]]:
        """청크 목록 번역
        
        Args:
            chunks (List[Dict[str, Any]]): 번역할 청크 목록
            target_language (str): 대상 언어 코드
        
        Returns:
            List[Dict[str, Any]]: 번역된 청크 목록
        """
        translated_chunks = []
        
        for chunk in chunks:
            # 원본 텍스트
            original_text = chunk.get("text", "")
            
            # 텍스트 번역
            translated_text = self.translate_text(original_text, target_language)
            
            # 청크 복사 및 번역 텍스트 설정
            translated_chunk = chunk.copy()
            translated_chunk["text"] = translated_text
            
            # 메타데이터에 언어 정보 추가
            metadata = translated_chunk.get("metadata", {})
            metadata["language"] = target_language
            metadata["translated_from"] = self.detect_language(original_text)
            translated_chunk["metadata"] = metadata
            
            translated_chunks.append(translated_chunk)
        
        logger.info(f"{len(chunks)}개 청크를 {target_language}로 번역 완료")
        return translated_chunks
    
    def detect_language_confidence(self, text: str) -> Dict[str, float]:
        """텍스트의 언어 감지 신뢰도
        
        Args:
            text (str): 언어를 감지할 텍스트
        
        Returns:
            Dict[str, float]: 언어 코드를 키로 하는 신뢰도 값 딕셔너리
        """
        # 참고: langdetect는 기본적으로 단일 언어만 반환하므로
        # 여러 언어의 확률을 얻으려면 다른 라이브러리나 방법이 필요합니다.
        # 현재 구현은 단순화된 버전입니다.
        
        if not text or not text.strip():
            return {lang: 0.0 for lang in self.supported_languages}
        
        try:
            detected = self.detect_language(text)
            
            # 검출된 언어에 높은 신뢰도, 나머지는 낮은 값 할당
            confidence = {lang: 0.05 for lang in self.supported_languages}
            confidence[detected] = 0.9
            
            return confidence
        except Exception as e:
            logger.error(f"언어 신뢰도 감지 중 오류 발생: {e}")
            return {lang: 1.0 / len(self.supported_languages) for lang in self.supported_languages}
    
    def get_language_name(self, lang_code: str) -> str:
        """언어 코드에 해당하는 영어 언어명 반환
        
        Args:
            lang_code (str): 언어 코드
        
        Returns:
            str: 영어 언어명
        """
        return self.lang_name_map.get(lang_code, "Unknown")
    
    def is_supported_language(self, lang_code: str) -> bool:
        """지원하는 언어인지 확인
        
        Args:
            lang_code (str): 확인할 언어 코드
        
        Returns:
            bool: 지원하면 True, 아니면 False
        """
        return lang_code in self.supported_languages
