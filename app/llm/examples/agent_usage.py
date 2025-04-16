"""
Agent 사용 예제
"""
import os
import argparse
from pathlib import Path
import json

from wisespeak_ai.processors.pdf.text_extractor import TextExtractor
from wisespeak_ai.processors.document.document_chunker import DocumentChunker
from wisespeak_ai.embeddings.embedding_pipeline import EmbeddingPipeline
from wisespeak_ai.rag.rag_engine import RAGEngine
from wisespeak_ai.agents.lecture_agent import LectureAgent
from wisespeak_ai.agents.qa_agent import QAAgent
from wisespeak_ai.utils.logger import get_logger

logger = get_logger(__name__)

def setup_lecture_system(pdf_path, collection_name="lecture_collection"):
    """PDF를 처리하고 강의 시스템 설정
    
    Args:
        pdf_path (str): PDF 파일 경로
        collection_name (str, optional): 컬렉션 이름. 기본값은 "lecture_collection"
    
    Returns:
        tuple: (문서 ID, 문서 내용, LectureAgent 객체)
    """
    # 텍스트 추출
    logger.info("1. PDF 텍스트 추출 시작")
    text_extractor = TextExtractor()
    extracted_text = text_extractor.extract_text_from_pdf(pdf_path)
    
    # 문서 정보 가져오기
    doc_info = text_extractor.get_document_info(pdf_path)
    logger.info(f"텍스트 추출 완료: {len(extracted_text)}페이지, 제목: {doc_info.get('title')}")
    
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
    
    # 에이전트 초기화
    lecture_agent = LectureAgent()
    
    return document_id, extracted_text, lecture_agent

def generate_lecture_content(lecture_agent, document_id, extracted_text, collection_name):
    """강의 컨텐츠 생성
    
    Args:
        lecture_agent (LectureAgent): 강의 에이전트 객체
        document_id (str): 문서 ID
        extracted_text (dict): 추출된 텍스트
        collection_name (str): 컬렉션 이름
    
    Returns:
        dict: 생성된 강의 컨텐츠
    """
    # 문서 제목 설정 (첫 페이지 텍스트에서 추출)
    first_page_text = extracted_text.get(1, "")
    title_candidate = first_page_text.split("\n")[0] if first_page_text else "강의 제목"
    
    # 제목이 너무 길면 조정
    lecture_title = title_candidate[:50] if len(title_candidate) > 50 else title_candidate
    
    # 강의 개요 생성
    logger.info("1. 강의 개요 생성 시작")
    lecture_outline = lecture_agent.generate_lecture_outline(
        document_content=extracted_text,
        lecture_title=lecture_title
    )
    logger.info("강의 개요 생성 완료")
    
    # 페이지별 스크립트 생성 (처음 3페이지만)
    logger.info("2. 페이지별 강의 스크립트 생성 시작")
    page_scripts = {}
    
    for page_num in sorted(extracted_text.keys())[:3]:  # 시간 절약을 위해 처음 3페이지만 처리
        logger.info(f"페이지 {page_num} 스크립트 생성 중...")
        
        page_content = {
            "page_number": page_num,
            "text": extracted_text[page_num],
            "document_id": document_id
        }
        
        script_result = lecture_agent.generate_lecture_script(
            page_content=page_content,
            collection_name=collection_name,
            lecture_title=lecture_title
        )
        
        page_scripts[page_num] = script_result
    
    logger.info(f"페이지별 스크립트 생성 완료: {len(page_scripts)}페이지")
    
    # 퀴즈 생성 (첫 페이지만)
    logger.info("3. 퀴즈 생성 시작")
    page_content = {
        "page_number": 1,
        "text": extracted_text[1],
        "document_id": document_id
    }
    
    quiz_result = lecture_agent.generate_lecture_quiz(
        page_content=page_content,
        collection_name=collection_name,
        lecture_title=lecture_title,
        num_questions=3
    )
    
    logger.info("퀴즈 생성 완료")
    
    # 결과 반환
    return {
        "title": lecture_title,
        "outline": lecture_outline,
        "scripts": page_scripts,
        "quiz": quiz_result
    }

def setup_qa_system(pdf_path, collection_name="qa_collection"):
    """PDF를 처리하고 QA 시스템 설정
    
    Args:
        pdf_path (str): PDF 파일 경로
        collection_name (str, optional): 컬렉션 이름. 기본값은 "qa_collection"
    
    Returns:
        tuple: (문서 ID, QAAgent 객체)
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
    
    # 에이전트 초기화
    qa_agent = QAAgent()
    
    return document_id, qa_agent

def run_qa_chat(qa_agent, collection_name, document_id, questions):
    """QA 채팅 실행
    
    Args:
        qa_agent (QAAgent): QA 에이전트 객체
        collection_name (str): 컬렉션 이름
        document_id (str): 문서 ID
        questions (list): 질문 목록
    
    Returns:
        list: 질문-답변 목록
    """
    conversation_history = []
    results = []
    
    for i, question in enumerate(questions):
        logger.info(f"질문 {i+1}/{len(questions)} 처리 중: '{question}'")
        
        answer_result = qa_agent.answer_question(
            question=question,
            collection_name=collection_name,
            document_id=document_id,
            conversation_history=conversation_history
        )
        
        # 대화 이력 업데이트
        conversation_history.append({"user": question})
        conversation_history.append({"assistant": answer_result["answer"]})
        
        results.append({
            "question": question,
            "answer": answer_result["answer"]
        })
    
    return results

def run_agent_demo(pdf_path, output_dir=None):
    """Agent 데모 실행
    
    Args:
        pdf_path (str): PDF 파일 경로
        output_dir (str, optional): 출력 디렉토리. 기본값은 현재 디렉토리의 'output'
    """
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path("output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 강의 시스템 설정 및 컨텐츠 생성
    logger.info("=== 강의 시스템 설정 및 컨텐츠 생성 ===")
    lecture_collection = f"lecture_{Path(pdf_path).stem}"
    document_id, extracted_text, lecture_agent = setup_lecture_system(pdf_path, lecture_collection)
    
    lecture_content = generate_lecture_content(
        lecture_agent=lecture_agent,
        document_id=document_id,
        extracted_text=extracted_text,
        collection_name=lecture_collection
    )
    
    # 강의 컨텐츠 저장
    lecture_output_path = Path(output_dir) / "lecture_content.json"
    with open(lecture_output_path, "w", encoding="utf-8") as f:
        json.dump(lecture_content, f, ensure_ascii=False, indent=2)
    
    logger.info(f"강의 컨텐츠 저장: {lecture_output_path}")
    
    # 강의 스크립트 텍스트 저장
    scripts_output_path = Path(output_dir) / "lecture_scripts.txt"
    with open(scripts_output_path, "w", encoding="utf-8") as f:
        f.write(f"강의 제목: {lecture_content['title']}\n\n")
        f.write("=== 강의 개요 ===\n")
        f.write(lecture_content['outline']['outline'])
        f.write("\n\n")
        
        for page_num, script in sorted(lecture_content['scripts'].items()):
            f.write(f"=== 페이지 {page_num} 스크립트 ===\n")
            f.write(script['script'])
            f.write("\n\n")
    
    logger.info(f"강의 스크립트 저장: {scripts_output_path}")
    
    # QA 시스템 설정 및 질의응답
    logger.info("\n=== QA 시스템 설정 및 질의응답 ===")
    qa_collection = f"qa_{Path(pdf_path).stem}"
    qa_document_id, qa_agent = setup_qa_system(pdf_path, qa_collection)
    
    # 질문 목록
    questions = [
        "이 문서의 주요 내용은 무엇인가요?",
        "가장 중요한 개념은 무엇인가요?",
        "이 내용을 실제로 어떻게 적용할 수 있을까요?",
        "이전 질문에 대한 답변을 더 자세히 설명해주세요."
    ]
    
    qa_results = run_qa_chat(
        qa_agent=qa_agent,
        collection_name=qa_collection,
        document_id=qa_document_id,
        questions=questions
    )
    
    # QA 결과 저장
    qa_output_path = Path(output_dir) / "qa_results.txt"
    with open(qa_output_path, "w", encoding="utf-8") as f:
        for i, qa in enumerate(qa_results):
            f.write(f"=== 질문 {i+1} ===\n")
            f.write(f"Q: {qa['question']}\n\n")
            f.write(f"A: {qa['answer']}\n\n")
    
    logger.info(f"QA 결과 저장: {qa_output_path}")
    
    logger.info("Agent 데모 완료")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 사용 예제")
    parser.add_argument("pdf_path", help="PDF 파일 경로")
    parser.add_argument("--output", "-o", help="출력 디렉토리", default="output")
    
    args = parser.parse_args()
    
    run_agent_demo(args.pdf_path, args.output)
