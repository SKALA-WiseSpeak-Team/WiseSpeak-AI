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

from app.llm.language.instructions import get_language_instructions
from app.llm.audio.tts import get_tts_processor

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
    
    # RAGSystem 클래스 내의 query 메서드 변경
    def query(self, query_text: str, language: str = "en", use_history: bool = True, namespace: Optional[str] = None, namespaces: Optional[List[str]] = None) -> Dict[str, Any]:
        # 여러 네임스페이스를 참조하는 경우 처리
        # namespaces가 있으면 여러 네임스페이스를 참조, 없으면 단일 네임스페이스 사용
        query_namespace = namespace if namespace is not None else self.namespace
        
        try:
            # 벡터 DB에서 관련 컨텍스트 검색
            if namespaces:
                # 여러 네임스페이스에서 반환된 문서들을 저장할 리스트
                all_relevant_docs = []
                
                # 각 네임스페이스에서 문서 검색
                for ns in namespaces:
                    logger.info(f"네임스페이스 '{ns}'에서 검색 중...")
                    docs = self.embedder.query_similar(query_text, n_results=5, namespace=ns)
                    if docs:
                        all_relevant_docs.extend(docs)
                
                # 점수를 기준으로 정렬하여 상위 5개만 유지
                relevant_docs = sorted(all_relevant_docs, key=lambda x: x.get("score", 0), reverse=True)[:5]
                logger.info(f"네임스페이스 검색 결과: {len(relevant_docs)}개 문서")
            else:
                # 단일 네임스페이스 검색
                relevant_docs = self.embedder.query_similar(query_text, n_results=5, namespace=query_namespace)
            
            # 컨텍스트 준비
            context = "\n\n".join([doc["text"] for doc in relevant_docs])
            
            # 언어별 지침 준비
            language_instructions = self._get_language_instructions(language)
            
            # 프롬프트 준비
            system_prompt = f"""당신은 강의 자료와 교육 콘텐츠에 기반하여 정확한 정보를 제공하는 전문 교육 비서입니다.
            {language_instructions}
            
            다음 체계적인 지침에 따라 응답하세요:
 
            1. 증거 기반 분석 단계:
            a. 제공된 컨텍스트를 철저히 분석하고 질문의 핵심 의도 파악
                b. 컨텍스트 내에서 사실 기반 정보만 추출하여 검증
                c. 관련 없는 정보나 불확실한 정보는 명확히 배제

            2. 명확한 한계 인식:
                a. 컨텍스트에 명시적으로 포함된 정보만 활=용
                b. 정보가 불충분할 경우 "제공된 자료에는 이 질문에 대한 충분한 정보가 없습니다"라고 정직하게 언급
                c. 추측이나 일반화는 절대 하지 않음

            3. 문화적 맥락 존중:
                a. 해당 언어의 문화적 뉴앙스와 표현 방식 고려
                b. 현지 교육 환경에 적합한 용어와 예시 사용
                c. 문화적 오해를 일으킬 수 있는 직역이나 표현 피하기

            4. 교육적 전달 방식:
                a. 명확하고 논리적인 구조로 정보 제시
                b. 복잡한 개념은 단계적으로 설명
                c. 교육자의 전문적이고 친절한 어조 유지

            5. 시각 자료 참조 시:
                a. 이미지나 도표가 직접 보이지 않음을 명시
                b. 시각 자료의 내용과 목적을 텍스트로 명확히 설명

            제공된 컨텍스트만 엄격하게 기반으로 응답하고, 확실하지 않은 정보는 절대 포함하지 마세요. 정확성이 가장 중요한 가치입니다."""
        
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
            
            # 텍스트를 음성으로 변환
            tts_processor = get_tts_processor()
            audio_path = tts_processor.text_to_speech(
                text=answer,
                language=language,
                voice="auto",
                apply_patterns=True
            )
            
            # 결과 구성
            result = {
                "query": query_text,
                "answer": answer,
                "language": language,
                "audio_path": audio_path,  # 오디오 경로 추가
                "relevant_sources": [
                    {
                        "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                        "metadata": doc["metadata"],
                        "score": doc["score"]
                    }
                    for doc in relevant_docs
                ]
            }
            
            logger.info(f"RAG 쿼리 응답 생성 완료: {len(answer)} 자, 오디오 파일: {audio_path}")
            return result
        except Exception as e:
            logger.error(f"RAG 쿼리 처리 실패: {str(e)}")
            return {
                "query": query_text,
                "answer": f"Error processing your query: {str(e)}",
                "language": language,
                "audio_path": None,  # 오디오 경로 추가 (오류 시 None)
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
        from app.llm.language.instructions import get_language_instructions
        return get_language_instructions(language)


def get_rag_system(namespace: str = "default") -> RAGSystem:
    """
    RAGSystem 인스턴스 가져오기 헬퍼 함수
    
    Args:
        namespace: 벡터 DB 네임스페이스
    
    Returns:
        RAGSystem 인스턴스
    """
    return RAGSystem(namespace)


def add_common_knowledge_to_default(document_text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    공통 지식을 default 네임스페이스에 추가하는 헬퍼 함수
    
    Args:
        document_text: 문서 텍스트
        metadata: 문서 메타데이터
    
    Returns:
        추가된 청크 ID 리스트
    """
    rag_system = get_rag_system("default")
    return rag_system.add_document_to_knowledge(document_text, metadata)


def process_query(query_text: str, language: str = "en", namespace: str = "default", use_history: bool = True) -> Dict[str, Any]:
    """
    쿼리 처리 헬퍼 함수
    
    Args:
        query_text: 질문 텍스트
        language: 언어 코드
        namespace: 벡터 DB 네임스페이스
        use_history: 대화 히스토리 사용 여부
    
    Returns:
        생성된 답변 및 관련 정보
    """
    rag_system = get_rag_system(namespace)
    return rag_system.query(query_text, language, use_history)


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