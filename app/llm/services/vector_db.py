"""
ChromaDB 벡터 데이터베이스 서비스
"""
import os
from typing import List, Dict, Any, Optional, Tuple, Union
import chromadb
from chromadb.utils import embedding_functions

from ..config import config
from ..utils.logger import get_logger
from .openai_service import OpenAIService

logger = get_logger(__name__)

class VectorDBService:
    """ChromaDB 벡터 데이터베이스 서비스 클래스"""
    
    def __init__(self, 
                db_path: Optional[str] = None, 
                openai_service: Optional[OpenAIService] = None):
        """ChromaDB 서비스 초기화
        
        Args:
            db_path (Optional[str], optional): ChromaDB 저장 경로. 기본값은 config에서 로드
            openai_service (Optional[OpenAIService], optional): OpenAI 서비스 객체
        """
        self.db_path = db_path or config.CHROMA_DB_DIR
        os.makedirs(self.db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.openai_service = openai_service or OpenAIService()
        
        # OpenAI 임베딩 함수 설정
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_service.api_key,
            model_name=config.OPENAI_EMBEDDING_MODEL
        )
        
        logger.info(f"ChromaDB 서비스 초기화 완료 (경로: {self.db_path})")
    
    def create_collection(self, collection_name: str) -> Any:
        """컬렉션 생성 또는 가져오기
        
        Args:
            collection_name (str): 컬렉션 이름
        
        Returns:
            Any: ChromaDB 컬렉션 객체
        """
        try:
            # 기존 컬렉션이 있으면 가져오고, 없으면 생성
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": f"SRAGA {collection_name} collection"}
            )
            logger.info(f"컬렉션 준비 완료: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"컬렉션 생성 중 오류 발생: {e}")
            raise
    
    def list_collections(self) -> List[str]:
        """모든 컬렉션 목록 반환
        
        Returns:
            List[str]: 컬렉션 이름 목록
        """
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 중 오류 발생: {e}")
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """컬렉션 삭제
        
        Args:
            collection_name (str): 삭제할 컬렉션 이름
        
        Returns:
            bool: 성공 여부
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"컬렉션 삭제 완료: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"컬렉션 삭제 중 오류 발생: {e}")
            return False
    
    def add_documents(self, 
                    collection_name: str, 
                    documents: List[str], 
                    metadatas: List[Dict[str, Any]],
                    ids: Optional[List[str]] = None) -> bool:
        """문서 추가
        
        Args:
            collection_name (str): 컬렉션 이름
            documents (List[str]): 문서 텍스트 목록
            metadatas (List[Dict[str, Any]]): 문서 메타데이터 목록
            ids (Optional[List[str]], optional): 문서 ID 목록
        
        Returns:
            bool: 성공 여부
        """
        try:
            collection = self.create_collection(collection_name)
            
            # ID가 제공되지 않으면 임의로 생성
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in range(len(documents))]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"컬렉션 {collection_name}에 {len(documents)}개 문서 추가 완료")
            return True
        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {e}")
            return False
    
    def search(self, 
            collection_name: str, 
            query: str, 
            n_results: int = 5,
            ㄴwhere: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """쿼리와 유사한 문서 검색
        
        Args:
            collection_name (str): 컬렉션 이름
            query (str): 검색 쿼리
            n_results (int, optional): 반환할 결과 수. 기본값은 5
            where (Optional[Dict[str, Any]], optional): 필터링 조건
        
        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            collection = self.create_collection(collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
            
            logger.info(f"컬렉션 {collection_name}에서 '{query}' 검색 완료, {len(formatted_results)}개 결과 반환")
            return formatted_results
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return []
    
    def get_by_id(self, collection_name: str, doc_id: str) -> Dict[str, Any]:
        """ID로 문서 조회
        
        Args:
            collection_name (str): 컬렉션 이름
            doc_id (str): 문서 ID
        
        Returns:
            Dict[str, Any]: 문서 정보
        """
        try:
            collection = self.create_collection(collection_name)
            result = collection.get(ids=[doc_id])
            
            if not result["documents"]:
                logger.warning(f"문서 ID {doc_id}를 찾을 수 없습니다")
                return {}
            
            return {
                "document": result["documents"][0],
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
                "id": doc_id
            }
        except Exception as e:
            logger.error(f"ID로 문서 조회 중 오류 발생: {e}")
            return {}
    
    def update_document(self, 
                        collection_name: str, 
                        doc_id: str, 
                        document: str, 
                        metadata: Dict[str, Any]) -> bool:
        """문서 업데이트
        
        Args:
            collection_name (str): 컬렉션 이름
            doc_id (str): 문서 ID
            document (str): 새 문서 내용
            metadata (Dict[str, Any]): 새 메타데이터
        
        Returns:
            bool: 성공 여부
        """
        try:
            collection = self.create_collection(collection_name)
            collection.update(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"문서 ID {doc_id} 업데이트 완료")
            return True
        except Exception as e:
            logger.error(f"문서 업데이트 중 오류 발생: {e}")
            return False
    
    def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """문서 삭제
        
        Args:
            collection_name (str): 컬렉션 이름
            doc_id (str): 삭제할 문서 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            collection = self.create_collection(collection_name)
            collection.delete(ids=[doc_id])
            logger.info(f"문서 ID {doc_id} 삭제 완료")
            return True
        except Exception as e:
            logger.error(f"문서 삭제 중 오류 발생: {e}")
            return False
    
    def count_documents(self, collection_name: str) -> int:
        """컬렉션의 문서 수 반환
        
        Args:
            collection_name (str): 컬렉션 이름
        
        Returns:
            int: 문서 수
        """
        try:
            collection = self.create_collection(collection_name)
            count = collection.count()
            logger.info(f"컬렉션 {collection_name}의 문서 수: {count}")
            return count
        except Exception as e:
            logger.error(f"문서 수 조회 중 오류 발생: {e}")
            return 0
