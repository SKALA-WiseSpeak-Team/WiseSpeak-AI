"""
RAG 검색 기능 예제
"""
import os
import argparse
from pathlib import Path

from wisespeak_ai.processors.pdf.text_extractor import TextExtractor
from wisespeak_ai.processors.document.document_chunker import DocumentChunker
from wisespeak_ai.embeddings.embedding_pipeline import EmbeddingPipeline
from wisespeak_ai.rag.rag_engine import RAGEngine
from wisespeak_ai.utils.logger import get_logger
from wisespeak_ai.config import config

logger = get_logger(__name__)

def setup_rag_system(pdf_path, collection_name="test_collection"):
    """PDF를 처리하고 RAG 시스템 설정
    
    Args:
        pdf_path (str): PDF 파일 경로
        collection_name (str, optional): 컬렉션 이름. 기본값은 "test_collection"
    
    Returns:
        tuple: (문서 ID, RAG 엔진)
    """
    # 텍스트 추출
    logger.info("1. PDF 텍스트 추출 시작")
    text_extractor = TextExtractor()
    extracted_text = text_extractor.extract_text_from_pdf(pdf_path)
    logger.info(f"텍스트 추출 완료: {len(extracted_text)}페이지")
    
    # 청크화
    logger.info("2. 텍스트 청크화 시작")
    chunker = DocumentChunker()
    chunked_document = chunker.chunk_document(extracted_text)
    logger.info(f"청크화 완료: {len(chunked_document['chunks'])}개 청크")
    
    # 임베딩
    logger.info("3. 임베딩 및 벡터 DB 저장 시작")
    embedding_pipeline = EmbeddingPipeline()
    document_id = f"doc_{Path(pdf_path).stem}"
    
    # 각 청크에 문서 ID 추가
    for chunk in chunked_document["chunks"]:
        chunk["metadata"]["document_id"] = document_id
    
    # 벡터 DB에 저장
    embedding_pipeline.process_chunks(chunked_document["chunks"], collection_name)
    logger.info(f"임베딩 및 저장 완료: 컬렉션={collection_name}, 문서 ID={document_id}")
    
    # RAG 엔진 초기화
    rag_engine = RAGEngine()
    
    return document_id, rag_engine

def perform_rag_search(rag_engine, collection_name, query, document_id=None):
    """RAG 검색 수행
    
    Args:
        rag_engine (RAGEngine): RAG 엔진 객체
        collection_name (str): 컬렉션 이름
        query (str): 검색 쿼리
        document_id (str, optional): 문서 ID (필터링용)
    
    Returns:
        dict: 검색 결과
    """
    logger.info(f"RAG 검색 수행: '{query}'")
    
    # 메타데이터 필터 설정
    filter_metadata = {}
    if document_id:
        filter_metadata["document_id"] = document_id
    
    # 기본 RAG 검색
    basic_results = rag_engine.rag_query(
        query=query,
        collection_name=collection_name,
        filter_metadata=filter_metadata
    )
    logger.info("기본 RAG 검색 완료")
    
    # 향상된 RAG 검색
    enhanced_results = rag_engine.enhanced_rag_query(
        query=query,
        collection_name=collection_name,
        filter_metadata=filter_metadata,
        reranking=True,
        query_expansion=True,
        context_compression=True
    )
    logger.info("향상된 RAG 검색 완료")
    
    return {
        "basic": basic_results,
        "enhanced": enhanced_results
    }

def run_rag_demo(pdf_path, queries, output_dir=None):
    """RAG 데모 실행
    
    Args:
        pdf_path (str): PDF 파일 경로
        queries (list): 테스트할 쿼리 목록
        output_dir (str, optional): 출력 디렉토리. 기본값은 현재 디렉토리의 'output'
    """
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path("output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 컬렉션 이름 설정
    collection_name = f"demo_{Path(pdf_path).stem}"
    
    # RAG 시스템 설정
    document_id, rag_engine = setup_rag_system(pdf_path, collection_name)
    
    # 각 쿼리에 대해 검색 수행
    all_results = {}
    
    for i, query in enumerate(queries):
        logger.info(f"쿼리 {i+1}/{len(queries)} 처리 중: '{query}'")
        results = perform_rag_search(rag_engine, collection_name, query, document_id)
        all_results[query] = results
    
    # 결과 저장
    results_output_path = Path(output_dir) / "rag_results.txt"
    with open(results_output_path, "w", encoding="utf-8") as f:
        for query, results in all_results.items():
            f.write(f"=== 쿼리: {query} ===\n\n")
            
            # 기본 RAG 결과
            f.write("-- 기본 RAG 결과 --\n")
            f.write(f"응답: {results['basic']['response']}\n\n")
            
            # 향상된 RAG 결과
            f.write("-- 향상된 RAG 결과 --\n")
            f.write(f"응답: {results['enhanced']['response']}\n")
            if results['enhanced']['expanded_query']:
                f.write(f"확장된 쿼리: {results['enhanced']['expanded_query']}\n")
            
            f.write("\n" + "="*80 + "\n\n")
    
    logger.info(f"RAG 결과 저장: {results_output_path}")
    logger.info("RAG 데모 완료")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG 검색 기능 예제")
    parser.add_argument("pdf_path", help="PDF 파일 경로")
    parser.add_argument("--queries", "-q", nargs="+", help="검색 쿼리 목록", 
                    default=["이 문서의 주요 내용은 무엇인가요?", 
                            "가장 중요한 개념은 무엇인가요?", 
                            "이 내용을 실제로 어떻게 적용할 수 있을까요?"])
    parser.add_argument("--output", "-o", help="출력 디렉토리", default="output")
    
    args = parser.parse_args()
    
    run_rag_demo(args.pdf_path, args.queries, args.output)
