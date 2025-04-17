# app/ai/openai_client.py
# OpenAI API 클라이언트 - OpenAI API 연결 및 요청/응답 처리

import os
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import json
import time

import openai
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API 클라이언트"""
    
    def __init__(
        self, 
        api_key: str = settings.OPENAI_API_KEY,
        chat_model: str = settings.OPENAI_CHAT_MODEL,
        embedding_model: str = settings.OPENAI_EMBEDDING_MODEL,
        tts_model: str = settings.OPENAI_TTS_MODEL,
        stt_model: str = settings.OPENAI_STT_MODEL
    ):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키
            chat_model: 채팅 모델 이름
            embedding_model: 임베딩 모델 이름
            tts_model: TTS 모델 이름
            stt_model: STT 모델 이름
        """
        self.api_key = api_key
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.tts_model = tts_model
        self.stt_model = stt_model
        
        # OpenAI 클라이언트 생성
        self.client = OpenAI(api_key=api_key)
        
        # 초기화 테스트
        self._test_connection()
    
    def _test_connection(self) -> None:
        """API 연결 테스트"""
        try:
            # 간단한 API 호출로 연결 테스트
            response = self.client.models.list()
            if response:
                logger.info("OpenAI API 연결 성공")
            else:
                logger.warning("OpenAI API 응답이 비어 있습니다")
        except Exception as e:
            logger.error(f"OpenAI API 연결 테스트 실패: {str(e)}")
            logger.warning("API 연결이 실패했지만, 클라이언트 초기화는 계속됩니다")
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        채팅 완성 요청
        
        Args:
            messages: 메시지 목록
            model: 모델 이름 (None이면 기본값 사용)
            temperature: 온도 (0~2)
            max_tokens: 최대 토큰 수
            retry_count: 재시도 횟수
        
        Returns:
            응답 데이터
        """
        try:
            model = model or self.chat_model
            
            # API 요청 준비
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            # 최대 토큰 수가 지정된 경우 추가
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            
            # 재시도 로직
            for attempt in range(retry_count):
                try:
                    response = self.client.chat.completions.create(**request_params)
                    
                    # 응답 처리
                    result = {
                        "text": response.choices[0].message.content,
                        "model": response.model,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        }
                    }
                    
                    return result
                except Exception as e:
                    # 마지막 시도가 아니면 재시도
                    if attempt < retry_count - 1:
                        wait_time = 2 ** attempt  # 지수 백오프
                        logger.warning(f"API 요청 실패, {wait_time}초 후 재시도 ({attempt + 1}/{retry_count}): {str(e)}")
                        time.sleep(wait_time)
                    else:
                        # 모든 재시도 실패
                        raise
            
            # 여기에 도달하지 않지만, 형식적으로 추가
            return {"text": "", "model": model, "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        except Exception as e:
            logger.error(f"채팅 완성 요청 실패: {str(e)}")
            return {"text": f"오류: {str(e)}", "model": model, "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
    
    def text_to_speech(
        self, 
        text: str, 
        voice: str = "alloy",
        model: Optional[str] = None,
        output_format: str = "mp3",
        speed: float = 1.0
    ) -> bytes:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 변환할 텍스트
            voice: 음성 (alloy, echo, fable, onyx, nova, shimmer)
            model: 모델 이름 (None이면 기본값 사용)
            output_format: 출력 형식 (mp3, opus, aac, flac)
            speed: 음성 속도 (0.25~4.0)
        
        Returns:
            오디오 바이너리 데이터
        """
        try:
            model = model or self.tts_model
            
            # 텍스트가 너무 길면 잘라내기 (OpenAI API 제한)
            max_chars = 4000
            if len(text) > max_chars:
                logger.warning(f"텍스트가 너무 깁니다. {max_chars}자로 제한합니다. 원본 길이: {len(text)}자")
                text = text[:max_chars]
            
            # API 요청
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=output_format,
                speed=speed
            )
            
            # 응답 처리
            audio_data = response.content
            
            logger.info(f"TTS 변환 완료: {len(audio_data)} 바이트")
            return audio_data
        except Exception as e:
            logger.error(f"TTS 변환 실패: {str(e)}")
            raise
    
    def speech_to_text(
        self, 
        audio_data: bytes,
        model: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        음성을 텍스트로 변환
        
        Args:
            audio_data: 오디오 바이너리 데이터
            model: 모델 이름 (None이면 기본값 사용)
            language: 언어 코드 (None이면 자동 감지)
            prompt: 처리 힌트 제공
        
        Returns:
            변환 결과
        """
        try:
            model = model or self.stt_model
            
            # API 요청 준비
            request_params = {
                "model": model,
                "file": ("audio.mp3", audio_data, "audio/mpeg"),
                "response_format": "verbose_json"
            }
            
            # 언어가 지정된 경우 추가
            if language:
                request_params["language"] = language
            
            # 프롬프트가 지정된 경우 추가
            if prompt:
                request_params["prompt"] = prompt
            
            # API 요청
            response = self.client.audio.transcriptions.create(**request_params)
            
            # 응답 처리
            result = {
                "text": response.text,
                "language": response.language,
                "duration": response.duration
            }
            
            logger.info(f"STT 변환 완료: {len(result['text'])} 자")
            return result
        except Exception as e:
            logger.error(f"STT 변환 실패: {str(e)}")
            return {"text": "", "language": "unknown", "duration": 0}
    
    def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        텍스트의 임베딩 벡터 생성
        
        Args:
            text: 임베딩할 텍스트
            model: 모델 이름 (None이면 기본값 사용)
        
        Returns:
            임베딩 벡터
        """
        try:
            model = model or self.embedding_model
            
            # API 요청
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            # 응답 처리
            embedding = response.data[0].embedding
            
            logger.info(f"임베딩 생성 완료: {len(embedding)} 차원")
            return embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            return []


def get_openai_client() -> OpenAIClient:
    """
    OpenAIClient 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        OpenAIClient 인스턴스
    """
    return OpenAIClient()


def get_language_voice(language_code: str) -> str:
    """
    언어 코드에 적합한 음성 가져오기
    
    Args:
        language_code: 언어 코드 (예: 'en', 'ko')
    
    Returns:
        음성 이름
    """
    return settings.TTS_VOICES.get(language_code, settings.TTS_VOICES.get('en', 'alloy'))