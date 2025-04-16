# app/vector_db/chroma_client.py
# Chroma DB 클라이언트 - 벡터 데이터베이스 연결 및 관리

import os
from typing import Dict, List, Any, Optional, Union
import logging
import json
import uuid

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.core.config import settings

logger = logging.getLogger(__name__)

class ChromaClient:
    """Chroma 벡터 데이터베이스 클라이언트"""
    
    def __init__(self, collection_name: str = "lecture_collection"):
        """
        초기화
        
        Args:
            collection_name: Chroma 컬렉션 이름
        """
        self.collection_name = collection_name
        self.client = self._create_client()
        
        # OpenAI 임베딩 함수 설정
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_EMBEDDING_MODEL
        )
        
        self.collection = self._get_or_create_collection()
    
    def _create_client(self) -> chromadb.Client:
        """
        Chroma 클라이언트 생성
        
        Returns:
            Chroma 클라이언트
        """
        try:
            client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"Chroma DB 클라이언트 생성 완료. 경로: {settings.CHROMA_DB_DIR}")
            return client
        except Exception as e:
            logger.error(f"Chroma DB 클라이언트 생성 실패: {str(e)}")
            raise
    
    def _get_or_create_collection(self) -> chromadb.Collection:
        """
        컬렉션 가져오기 또는 생성
        
        Returns:
            Chroma 컬렉션
        """
        try:
            # 기존 컬렉션이 있는지 확인
            try:
                collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"기존 컬렉션 로드: {self.collection_name}")
                return collection
            except Exception:
                # 컬렉션이 없으면 새로 생성
                collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "PDF 강의 데이터 컬렉션"}
                )
                logger.info(f"새 컬렉션 생성: {self.collection_name}")
                return collection
        except Exception as e:
            logger.error(f"컬렉션 가져오기/생성 실패: {str(e)}")
            raise
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        """
        텍스트를 벡터 DB에 추가
        
        Args:
            texts: 추가할 텍스트 리스트
            metadatas: 각 텍스트에 대한 메타데이터
            ids: 각 텍스트에 대한 ID (없으면 자동 생성)
        
        Returns:
            추가된 문서 ID 리스트
        """
        try:
            # ID가 없으면 자동 생성
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(texts))]
            
            # 메타데이터가 없으면 빈 딕셔너리 생성
            if metadatas is None:
                metadatas = [{} for _ in range(len(texts))]
            
            # 데이터 추가
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"{len(texts)}개 문서를 벡터 DB에 추가했습니다.")
            return ids
        except Exception as e:
            logger.error(f"벡터 DB에 텍스트 추가 실패: {str(e)}")
            raise
    
    def query(self, query_text: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        쿼리 실행
        
        Args:
            query_text: 쿼리 텍스트
            n_results: 반환할 결과 수
            where: 필터링 조건
        
        Returns:
            쿼리 결과
        """
        try:
            # OpenAI 임베딩 함수를 사용하여 임베딩 생성
            # 직접 임베딩 함수를 사용해 쿼리를 임베딩으로 변환하지 않고
            # 텍스트 기반 검색을 합니다
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            logger.info(f"쿼리 실행 완료. {len(results['documents'][0])}개 결과 반환.")
            return results
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    
    def get_collection_count(self) -> int:
        """
        컬렉션에 있는 문서 수 반환
        
        Returns:
            문서 수
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"컬렉션 개수 조회 실패: {str(e)}")
            return 0
    
    def delete_collection(self) -> bool:
        """
        컬렉션 삭제
        
        Returns:
            성공 여부
        """
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"컬렉션 삭제 완료: {self.collection_name}")
            # 컬렉션 다시 생성
            self.collection = self._get_or_create_collection()
            return True
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {str(e)}")
            return False
    
    def get_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        ID로 문서 가져오기
        
        Args:
            document_id: 문서 ID
        
        Returns:
            문서 정보
        """
        try:
            result = self.collection.get(ids=[document_id])
            if result and result["documents"]:
                return {
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {}
                }
            return {}
        except Exception as e:
            logger.error(f"ID로 문서 가져오기 실패: {str(e)}")
            return {}
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        ID로 문서 삭제
        
        Args:
            ids: 삭제할 문서 ID 리스트
        
        Returns:
            성공 여부
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"{len(ids)}개 문서 삭제 완료")
            return True
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            return False


def get_chroma_client(collection_name: str = "lecture_collection") -> ChromaClient:
    """
    Chroma 클라이언트 가져오기 헬퍼 함수
    
    Args:
        collection_name: 컬렉션 이름
    
    Returns:
        ChromaClient 인스턴스
    """
    return ChromaClient(collection_name)