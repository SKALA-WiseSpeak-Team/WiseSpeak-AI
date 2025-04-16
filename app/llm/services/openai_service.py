"""
OpenAI API와의 통신 담당
"""
import time
import json
from typing import List, Dict, Any, Optional, Union

from openai import OpenAI, APIError
from tenacity import (
    retry,
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception_type
)

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIService:
    """OpenAI API 서비스 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """OpenAI 서비스 초기화
        
        Args:
            api_key (Optional[str], optional): OpenAI API 키. 기본값은 config에서 로드
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.model = config.OPENAI_MODEL
        self.embedding_model = config.OPENAI_EMBEDDING_MODEL
        logger.info(f"OpenAI 서비스 초기화 완료 (모델: {self.model}, 임베딩 모델: {self.embedding_model})")
    
    @retry(
        retry=retry_if_exception_type((APIError, ConnectionError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=lambda retry_state: logger.warning(
            f"API 오류 발생, {retry_state.attempt_number}번째 재시도 중..."
        )
    )
    def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 반환
        
        Args:
            text (str): 임베딩할 텍스트
        
        Returns:
            List[float]: 임베딩 벡터
        """
        if not text.strip():
            logger.warning("빈 텍스트에 대한 임베딩 요청이 무시되었습니다.")
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((APIError, ConnectionError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=lambda retry_state: logger.warning(
            f"API 오류 발생, {retry_state.attempt_number}번째 재시도 중..."
        )
    )
    def generate_text(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, Any]:
        """텍스트 생성 요청
        
        Args:
            prompt (str): 프롬프트 텍스트
            system_message (Optional[str], optional): 시스템 메시지. 기본값은 None
            temperature (float, optional): 온도 파라미터. 기본값은 0.7
            max_tokens (Optional[int], optional): 최대 토큰 수. 기본값은 None
            stream (bool, optional): 스트리밍 모드 사용 여부. 기본값은 False
        
        Returns:
            Union[str, Any]: 생성된 텍스트 또는 스트림 객체
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"텍스트 생성 중 오류 발생: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((APIError, ConnectionError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=lambda retry_state: logger.warning(
            f"API 오류 발생, {retry_state.attempt_number}번째 재시도 중..."
        )
    )
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트의 임베딩 벡터 일괄 반환
        
        Args:
            texts (List[str]): 임베딩할 텍스트 목록
        
        Returns:
            List[List[float]]: 임베딩 벡터 목록
        """
        # 빈 텍스트 필터링
        filtered_texts = [text for text in texts if text.strip()]
        
        if not filtered_texts:
            logger.warning("빈 텍스트 목록에 대한 임베딩 요청이 무시되었습니다.")
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=filtered_texts
            )
            
            # 결과를 원래 순서에 맞게 정렬
            embeddings = []
            for i, text in enumerate(texts):
                if text.strip():
                    for data in response.data:
                        if data.index == len(embeddings):
                            embeddings.append(data.embedding)
                            break
                else:
                    embeddings.append([])
            
            return embeddings
        except Exception as e:
            logger.error(f"일괄 임베딩 생성 중 오류 발생: {e}")
            raise
    
    def process_stream(self, stream):
        """스트림 응답 처리
        
        Args:
            stream: OpenAI API의 스트리밍 응답
        
        Yields:
            str: 텍스트 조각
        """
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
