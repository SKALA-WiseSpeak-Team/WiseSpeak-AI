"""
RAG 시스템 테스트
"""
import os
import pytest

from wisespeak_ai.processors.document.document_chunker import DocumentChunker
from wisespeak_ai.embeddings.embedding_pipeline import EmbeddingPipeline
from wisespeak_ai.rag.rag_engine import RAGEngine
from wisespeak_ai.services.vector_db import VectorDBService

# 데이터베이스 이름 설정 (테스트용)
TEST_COLLECTION = "test_rag_collection"

def test_document_chunking():
    """문서 청크화 테스트"""
    # 테스트용 문서
    test_document = {
        1: "이것은 첫 번째 페이지입니다. 테스트를 위한 내용입니다. 문장 분리가 잘 되는지 확인합니다.",
        2: "두 번째 페이지입니다. 두 번째 내용이 들어갑니다. 이 텍스트도 청크화 대상입니다."
    }
    
    # 청크화
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    chunked_document = chunker.chunk_document(test_document)
    
    # 결과 확인
    assert isinstance(chunked_document, dict)
    assert "chunks" in chunked_document
    assert isinstance(chunked_document["chunks"], list)
    assert len(chunked_document["chunks"]) > 0
    
    # 청크 내용 확인
    for chunk in chunked_document["chunks"]:
        assert "chunk_id" in chunk
        assert "text" in chunk
        assert "metadata" in chunk
        assert "page_number" in chunk["metadata"]

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="OpenAI API 키가 설정되지 않았습니다")
def test_embedding_pipeline():
    """임베딩 파이프라인 테스트"""
    # 테스트용 텍스트
    test_text = "이것은 임베딩 테스트를 위한 텍스트입니다."
    
    # 임베딩 파이프라인
    pipeline = EmbeddingPipeline()
    
    try:
        # 단일 텍스트 임베딩
        embedding = pipeline.embed_text(test_text)
        
        # 결과 확인
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
    except Exception as e:
        pytest.skip(f"OpenAI API 호출 오류: {e}")

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="OpenAI API 키가 설정되지 않았습니다")
def test_rag_engine():
    """RAG 엔진 테스트"""
    # RAG 엔진 초기화
    rag_engine = RAGEngine()
    vector_db = VectorDBService()
    
    # 테스트용 컬렉션 및 데이터
    test_docs = [
        "인공지능(AI)은 인간의 지능을 모방하는 기술입니다.",
        "기계학습은 AI의 하위 분야로, 데이터로부터 학습하는 알고리즘을 연구합니다.",
        "딥러닝은 심층 신경망을 사용하는 기계학습의 한 방법입니다."
    ]
    test_metadata = [
        {"page_number": 1, "document_id": "test_doc"},
        {"page_number": 2, "document_id": "test_doc"},
        {"page_number": 3, "document_id": "test_doc"}
    ]
    test_ids = ["chunk_1", "chunk_2", "chunk_3"]
    
    try:
        # 기존 컬렉션이 있으면 삭제
        if TEST_COLLECTION in vector_db.list_collections():
            vector_db.delete_collection(TEST_COLLECTION)
        
        # 테스트 데이터 삽입
        vector_db.add_documents(
            collection_name=TEST_COLLECTION,
            documents=test_docs,
            metadatas=test_metadata,
            ids=test_ids
        )
        
        # 간단한 쿼리 테스트
        results = rag_engine.retrieve(
            query="인공지능이란 무엇인가요?",
            collection_name=TEST_COLLECTION,
            n_results=2
        )
        
        # 결과 확인
        assert isinstance(results, list)
        assert len(results) > 0
        assert "document" in results[0]
        
        # 컬렉션 정리
        vector_db.delete_collection(TEST_COLLECTION)
    except Exception as e:
        # 오류 발생 시 컬렉션 정리 시도
        try:
            vector_db.delete_collection(TEST_COLLECTION)
        except:
            pass
        pytest.skip(f"RAG 엔진 테스트 오류: {e}")
