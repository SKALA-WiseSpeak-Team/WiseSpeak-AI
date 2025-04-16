"""
임베딩 파이프라인 모듈
"""
from typing import List, Dict, Any, Optional, Tuple
import uuid
from tqdm import tqdm

from ..config import config
from ..utils.logger import get_logger
from ..services.openai_service import OpenAIService
from ..services.vector_db import VectorDBService

logger = get_logger(__name__)

class EmbeddingPipeline:
    """임베딩 파이프라인 클래스"""
    
    def __init__(self, 
                openai_service: Optional[OpenAIService] = None,
                vector_db_service: Optional[VectorDBService] = None,
                batch_size: int = 10):
        """임베딩 파이프라인 초기화
        
        Args:
            openai_service (Optional[OpenAIService], optional): OpenAI 서비스 객체
            vector_db_service (Optional[VectorDBService], optional): 벡터 DB 서비스 객체
            batch_size (int, optional): 배치 크기. 기본값은 10
        """
        self.openai_service = openai_service or OpenAIService()
        self.vector_db_service = vector_db_service or VectorDBService()
        self.batch_size = batch_size
        
        logger.info(f"임베딩 파이프라인 초기화 완료 (배치 크기: {self.batch_size})")
    
    def embed_text(self, text: str) -> List[float]:
        """텍스트 임베딩 벡터 생성
        
        Args:
            text (str): 임베딩할 텍스트
        
        Returns:
            List[float]: 임베딩 벡터
        """
        return self.openai_service.get_embedding(text)
    
    def embed_texts_batch(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트 임베딩 벡터 일괄 생성
        
        Args:
            texts (List[str]): 임베딩할 텍스트 목록
        
        Returns:
            List[List[float]]: 임베딩 벡터 목록
        """
        return self.openai_service.get_embeddings_batch(texts)
    
    def process_chunks(self, 
                    chunks: List[Dict[str, Any]], 
                    collection_name: str) -> bool:
        """청크 처리 및 벡터 DB 저장
        
        Args:
            chunks (List[Dict[str, Any]]): 처리할 청크 목록
            collection_name (str): 저장할 컬렉션 이름
        
        Returns:
            bool: 성공 여부
        """
        if not chunks:
            logger.warning("처리할 청크가 없습니다")
            return False
        
        total_chunks = len(chunks)
        logger.info(f"총 {total_chunks}개 청크 처리 시작")
        
        try:
            # 배치 단위로 처리
            for i in range(0, total_chunks, self.batch_size):
                batch = chunks[i:i + self.batch_size]
                
                # 텍스트 및 메타데이터 추출
                texts = [chunk["text"] for chunk in batch]
                metadatas = [chunk["metadata"] for chunk in batch]
                
                # ID 생성 (없는 경우)
                ids = [chunk.get("chunk_id") or f"chunk_{uuid.uuid4().hex}" for chunk in batch]
                
                # 벡터 DB에 저장
                self.vector_db_service.add_documents(
                    collection_name=collection_name,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.debug(f"배치 {i//self.batch_size + 1}/{(total_chunks + self.batch_size - 1)//self.batch_size} 처리 완료")
            
            logger.info(f"총 {total_chunks}개 청크 처리 및 저장 완료")
            return True
        except Exception as e:
            logger.error(f"청크 처리 중 오류 발생: {e}")
            return False
    
    def process_document(self, 
                        document_data: Dict[str, List[Dict[str, Any]]], 
                        collection_name: str,
                        document_id: Optional[str] = None) -> bool:
        """문서 데이터 처리 및 벡터 DB 저장
        
        Args:
            document_data (Dict[str, List[Dict[str, Any]]]): 문서 데이터 (청크 목록 포함)
            collection_name (str): 저장할 컬렉션 이름
            document_id (Optional[str], optional): 문서 ID
        
        Returns:
            bool: 성공 여부
        """
        chunks = document_data.get("chunks", [])
        
        if not chunks:
            logger.warning("처리할 청크가 없는 문서입니다")
            return False
        
        # 각 청크에 문서 ID 추가
        if document_id:
            for chunk in chunks:
                chunk["metadata"]["document_id"] = document_id
        
        return self.process_chunks(chunks, collection_name)
    
    def delete_document_embeddings(self, 
                                collection_name: str, 
                                document_id: str) -> bool:
        """문서 임베딩 삭제
        
        Args:
            collection_name (str): 컬렉션 이름
            document_id (str): 삭제할 문서 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 컬렉션 가져오기
            collection = self.vector_db_service.create_collection(collection_name)
            
            # 문서 ID로 필터링하여 삭제
            collection.delete(where={"document_id": document_id})
            
            logger.info(f"문서 ID {document_id}의 임베딩 삭제 완료")
            return True
        except Exception as e:
            logger.error(f"문서 임베딩 삭제 중 오류 발생: {e}")
            return False
    
    def process_and_store_text(self, 
                            text: str, 
                            collection_name: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            doc_id: Optional[str] = None) -> str:
        """텍스트 처리 및 저장
        
        Args:
            text (str): 처리할 텍스트
            collection_name (str): 저장할 컬렉션 이름
            metadata (Optional[Dict[str, Any]], optional): 메타데이터
            doc_id (Optional[str], optional): 문서 ID
        
        Returns:
            str: 생성된 문서 ID
        """
        if not text or not text.strip():
            logger.warning("처리할 텍스트가 없습니다")
            return ""
        
        doc_id = doc_id or f"doc_{uuid.uuid4().hex}"
        metadata = metadata or {}
        metadata["document_id"] = doc_id
        
        try:
            # 벡터 DB에 저장
            self.vector_db_service.add_documents(
                collection_name=collection_name,
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"텍스트 처리 및 저장 완료 (ID: {doc_id})")
            return doc_id
        except Exception as e:
            logger.error(f"텍스트 처리 중 오류 발생: {e}")
            return ""
