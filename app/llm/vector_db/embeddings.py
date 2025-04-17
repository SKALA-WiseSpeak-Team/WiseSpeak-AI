# app/vector_db/embeddings.py
# 임베딩 생성 및 관리 - OpenAI 임베딩 모델을 사용하여 텍스트 임베딩 생성 및 관리

from typing import Dict, List, Any, Optional, Union
import logging
import json
import os
from pathlib import Path

import openai
import numpy as np

from app.core.config import settings
from app.llm.vector_db.chroma_client import get_chroma_client

logger = logging.getLogger(__name__)

# OpenAI API 키 설정
openai.api_key = settings.OPENAI_API_KEY

class TextEmbedder:
    """텍스트 임베딩 생성 및 관리 클래스"""
    
    def __init__(self, model_name: str = settings.OPENAI_EMBEDDING_MODEL):
        """
        초기화
        
        Args:
            model_name: OpenAI 임베딩 모델 이름
        """
        self.model_name = model_name
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.chroma_client = get_chroma_client()
    
    def get_embedding(self, text: str) -> List[float]:
        """
        텍스트의 임베딩 벡터 생성
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            임베딩 벡터
        """
        try:
            if not text.strip():
                return []
            
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=text
            )
            
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            return []
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트의 임베딩 벡터 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
        
        Returns:
            임베딩 벡터 리스트
        """
        try:
            if not texts:
                return []
            
            # 빈 문자열 필터링
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                return []
            
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=valid_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            return []
    
    def add_to_vectordb(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, namespace: str = "default") -> List[str]:
        """
        텍스트를 벡터 DB에 추가
        
        Args:
            texts: 추가할 텍스트 리스트
            metadatas: 각 텍스트에 대한 메타데이터
            namespace: 네임스페이스 (문서 식별을 위한 접두사)
        
        Returns:
            추가된 문서 ID 리스트
        """
        try:
            # 메타데이터가 없으면 기본 메타데이터 생성
            if metadatas is None:
                metadatas = [{"namespace": namespace, "index": i} for i in range(len(texts))]
            else:
                # 기존 메타데이터에 네임스페이스 추가
                for i, metadata in enumerate(metadatas):
                    metadata["namespace"] = namespace
                    metadata["index"] = i
            
            # Chroma DB에 추가
            ids = self.chroma_client.add_texts(texts, metadatas)
            return ids
        except Exception as e:
            logger.error(f"벡터 DB에 텍스트 추가 실패: {str(e)}")
            return []
    
    def add_document_chunks(self, document_chunks: List[Dict[str, Any]], namespace: str) -> List[str]:
        """
        문서 청크를 벡터 DB에 추가
        
        Args:
            document_chunks: 문서 청크 리스트 (텍스트와 메타데이터 포함)
            namespace: 네임스페이스
        
        Returns:
            추가된 문서 ID 리스트
        """
        try:
            texts = [chunk["text"] for chunk in document_chunks]
            metadatas = [chunk["metadata"] for chunk in document_chunks]
            
            return self.add_to_vectordb(texts, metadatas, namespace)
        except Exception as e:
            logger.error(f"문서 청크 추가 실패: {str(e)}")
            return []
    
    def query_similar(self, query_text: str, n_results: int = 5, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        유사한 문서 검색
        
        Args:
            query_text: 쿼리 텍스트
            n_results: 반환할 결과 수
            namespace: 특정 네임스페이스만 검색
        
        Returns:
            유사한 문서 리스트
        """
        try:
            # 네임스페이스 필터 설정
            where_filter = None
            if namespace:
                where_filter = {"namespace": namespace}
            
            # 쿼리 실행
            results = self.chroma_client.query(query_text, n_results, where_filter)
            
            # 결과 정리
            documents = []
            for i in range(len(results["documents"][0])):
                doc = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "id": results["ids"][0][i],
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0
                }
                documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"유사 문서 검색 실패: {str(e)}")
            return []
    
    def delete_namespace(self, namespace: str) -> bool:
        """
        네임스페이스 삭제
        
        Args:
            namespace: 삭제할 네임스페이스
        
        Returns:
            성공 여부
        """
        try:
            # 네임스페이스에 해당하는 모든 문서 가져오기
            results = self.chroma_client.collection.get(
                where={"namespace": namespace}
            )
            
            # 해당 문서가 있으면 삭제
            if results and results["ids"]:
                self.chroma_client.delete_by_ids(results["ids"])
                logger.info(f"네임스페이스 '{namespace}' 삭제 완료")
                return True
            
            logger.info(f"네임스페이스 '{namespace}' 문서 없음")
            return True
        except Exception as e:
            logger.error(f"네임스페이스 삭제 실패: {str(e)}")
            return False


def get_embedder() -> TextEmbedder:
    """
    TextEmbedder 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        TextEmbedder 인스턴스
    """
    return TextEmbedder()


def chunk_document(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    문서를 청크로 분할
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기
        chunk_overlap: 청크 간 중복 크기
    
    Returns:
        청크 리스트 (텍스트와 메타데이터 포함)
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        
        # 청크 메타데이터
        chunk_metadata = {
            "start": start,
            "end": end,
            "size": len(chunk_text)
        }
        
        # 청크 추가
        chunks.append({
            "text": chunk_text,
            "metadata": chunk_metadata
        })
        
        # 다음 시작 위치 (중복 고려)
        start = start + chunk_size - chunk_overlap
    
    return chunks