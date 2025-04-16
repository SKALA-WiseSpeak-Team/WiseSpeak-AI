# app/ai/rag.py
# RAG 구현 - 쿼리 처리 및 컨텍스트 검색, 검색 결과 기반 답변 생성

import os
from typing import Dict, List, Any, Optional, Union
import logging
import json
from pathlib import Path

from app.llm.ai.openai_client import get_openai_client
from app.llm.vector_db.embeddings import get_embedder
from app.core.config import settings

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG(Retrieval-Augmented Generation) 시스템"""
    
    def __init__(self, namespace: str = "default"):
        """
        초기화
        
        Args:
            namespace: 벡터 DB 네임스페이스
        """
        self.openai_client = get_openai_client()
        self.embedder = get_embedder()
        self.namespace = namespace
        self.conversation_history = []
    
    def query(self, query_text: str, language: str = "en", use_history: bool = True) -> Dict[str, Any]:
        """
        쿼리 처리 및 답변 생성
        
        Args:
            query_text: 질문 텍스트
            language: 언어 코드
            use_history: 대화 히스토리 사용 여부
        
        Returns:
            생성된 답변 및 관련 정보
        """
        try:
            # 벡터 DB에서 관련 컨텍스트 검색
            relevant_docs = self.embedder.query_similar(query_text, n_results=5, namespace=self.namespace)
            
            # 컨텍스트 준비
            context = "\n\n".join([doc["text"] for doc in relevant_docs])
            
            # 언어별 지침 준비
            language_instructions = self._get_language_instructions(language)
            
            # 프롬프트 준비
            system_prompt = f"""You are an educational assistant that helps with questions about lecture content.
            {language_instructions}
            
            Follow these guidelines:
            1. Answer the question accurately based on the provided context
            2. If the context doesn't contain the answer, say you don't have enough information
            3. Be clear, helpful, and educational in your tone
            4. Keep answers concise but comprehensive
            5. If referring to images or diagrams, mention that they are not directly visible
            
            Answer only based on the provided context, without adding speculative information."""
            
            prompt = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 대화 히스토리 추가 (선택적)
            if use_history and self.conversation_history:
                # 최근 대화 히스토리만 사용 (토큰 제한 고려)
                recent_history = self.conversation_history[-3:]
                prompt.extend(recent_history)
            
            # 컨텍스트 및 질문 추가
            prompt.append({
                "role": "user", 
                "content": f"""Please answer the following question based on this context:
                
                Context:
                {context}
                
                Question: {query_text}"""
            })
            
            # OpenAI API 호출
            response = self.openai_client.chat_completion(
                messages=prompt,
                temperature=0.5,
                max_tokens=800
            )
            
            answer = response.get("text", "")
            
            # 대화 히스토리 업데이트
            self.conversation_history.append({"role": "user", "content": query_text})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # 결과 구성
            result = {
                "query": query_text,
                "answer": answer,
                "language": language,
                "relevant_sources": [
                    {
                        "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                        "metadata": doc["metadata"],
                        "score": doc["score"]
                    }
                    for doc in relevant_docs
                ]
            }
            
            logger.info(f"RAG 쿼리 응답 생성 완료: {len(answer)} 자")
            return result
        except Exception as e:
            logger.error(f"RAG 쿼리 처리 실패: {str(e)}")
            return {
                "query": query_text,
                "answer": f"Error processing your query: {str(e)}",
                "language": language,
                "relevant_sources": []
            }
    
    def add_document_to_knowledge(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        문서를 지식 베이스에 추가
        
        Args:
            document_text: 문서 텍스트
            metadata: 문서 메타데이터
        
        Returns:
            추가된 청크 ID 리스트
        """
        try:
            from app.llm.vector_db.embeddings import chunk_document
            
            # 문서를 청크로 분할
            chunks = chunk_document(document_text)
            
            # 메타데이터 추가
            if metadata:
                for chunk in chunks:
                    chunk["metadata"].update(metadata)
            
            # 벡터 DB에 추가
            chunk_ids = self.embedder.add_document_chunks(chunks, self.namespace)
            
            logger.info(f"{len(chunk_ids)}개 청크를 지식 베이스에 추가했습니다")
            return chunk_ids
        except Exception as e:
            logger.error(f"문서 추가 실패: {str(e)}")
            return []
    
    def add_page_to_knowledge(self, page_data: Dict[str, Any], page_script: Optional[str] = None) -> List[str]:
        """
        페이지 데이터를 지식 베이스에 추가
        
        Args:
            page_data: 페이지 데이터
            page_script: 페이지 스크립트 (없으면 페이지 텍스트만 사용)
        
        Returns:
            추가된 청크 ID 리스트
        """
        try:
            page_number = page_data.get("page_number", 0)
            page_text = page_data.get("text", "")
            
            # 페이지 텍스트와 스크립트 결합
            combined_text = page_text
            if page_script:
                newline = '\n'  # 백슬래시 문제 해결을 위해 변수 사용
                combined_text += f"{newline}{newline}Lecture Script:{newline}{page_script}"
            
            # 메타데이터 준비
            metadata = {
                "page_number": page_number,
                "source_type": "lecture_page"
            }
            
            # 제목 추가 (있는 경우)
            titles = page_data.get("titles", [])
            if titles:
                metadata["title"] = titles[0]
            
            # 지식 베이스에 추가
            return self.add_document_to_knowledge(combined_text, metadata)
        except Exception as e:
            logger.error(f"페이지 추가 실패: {str(e)}")
            return []
    
    def clear_history(self) -> None:
        """대화 히스토리 초기화"""
        self.conversation_history = []
        logger.info("대화 히스토리를 초기화했습니다")
    
    def _get_language_instructions(self, language: str) -> str:
        """
        언어별 지침 생성
        
        Args:
            language: 언어 코드
        
        Returns:
            언어 지침
        """
        language = language.lower()
        
        # 지원하지 않는 언어인 경우 영어로 기본 설정
        if language not in settings.SUPPORTED_LANGUAGES:
            logger.warning(f"지원하지 않는 언어: {language}, 영어로 대체합니다")
            language = "en"
        
        instructions = {
            "en": "Respond in English using clear, natural language.",
            "ko": "Respond in Korean (한국어). Use natural, idiomatic Korean expressions.",
            "ja": "Respond in Japanese (日本語). Use natural, idiomatic Japanese expressions.",
            "zh": "Respond in Chinese (中文). Use natural, idiomatic Chinese expressions.",
            "es": "Respond in Spanish. Use natural, idiomatic Spanish expressions.",
            "fr": "Respond in French. Use natural, idiomatic French expressions.",
            "de": "Respond in German. Use natural, idiomatic German expressions."
        }
        
        return instructions.get(language, instructions["en"])


def get_rag_system(namespace: str = "default") -> RAGSystem:
    """
    RAGSystem 인스턴스 가져오기 헬퍼 함수
    
    Args:
        namespace: 벡터 DB 네임스페이스
    
    Returns:
        RAGSystem 인스턴스
    """
    return RAGSystem(namespace)


def process_query(query_text: str, language: str = "en", namespace: str = "default") -> Dict[str, Any]:
    """
    쿼리 처리 헬퍼 함수
    
    Args:
        query_text: 질문 텍스트
        language: 언어 코드
        namespace: 벡터 DB 네임스페이스
    
    Returns:
        생성된 답변 및 관련 정보
    """
    rag_system = get_rag_system(namespace)
    return rag_system.query(query_text, language)


def add_document_knowledge(document_text: str, metadata: Optional[Dict[str, Any]] = None, namespace: str = "default") -> List[str]:
    """
    문서를 지식 베이스에 추가 헬퍼 함수
    
    Args:
        document_text: 문서 텍스트
        metadata: 문서 메타데이터
        namespace: 벡터 DB 네임스페이스
    
    Returns:
        추가된 청크 ID 리스트
    """
    rag_system = get_rag_system(namespace)
    return rag_system.add_document_to_knowledge(document_text, metadata)