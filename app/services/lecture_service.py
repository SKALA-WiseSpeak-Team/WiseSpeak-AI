import os
from fastapi import UploadFile
from tempfile import NamedTemporaryFile
from pathlib import Path
import sys
import logging
from typing import Dict, List, Any, Optional, Union
import argparse
from app.core.config import settings
from app.db.session import supabase
from app.llm.pdf.extractor import extract_pdf_data
from app.llm.pdf.parser import parse_pdf_data
from app.llm.vector_db.embeddings import get_embedder, chunk_document
from app.llm.ai.script_gen import generate_script
from app.llm.ai.rag import get_rag_system
from app.llm.audio.tts import get_tts_processor
from app.llm.audio.stt import get_stt_processor
from app.llm.language.detector import get_language_detector
from app.llm.language.translator import get_translator
# from app.llm.database.supabase_client import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('lecture_rag_system.log')
    ]
)

logger = logging.getLogger(__name__)

class LectureService:
  def __init__(self):
    """초기화"""
    # 디렉토리 확인
    settings.ensure_directories()
    
    # 컴포넌트 초기화
    self.embedder = get_embedder()
    self.rag_system = get_rag_system()
    self.tts_processor = get_tts_processor()
    self.stt_processor = get_stt_processor()
    self.language_detector = get_language_detector()
    self.translator = get_translator()
    # self.supabase_client = get_supabase_client()
    
    # logger.info("LectureRAGSystem 초기화 완료")
        
  def process_pdf(self, pdf_path: str, language: str = "en") -> Dict[str, Any]:
    """
    PDF 처리 및 강의 생성
    
    Args:
        pdf_path: PDF 파일 경로
        language: 강의 언어
    
    Returns:
        처리 결과
    """
    try:
        # 1. PDF 데이터 추출
        logger.info(f"PDF 데이터 추출 시작: {pdf_path}")
        pdf_data = extract_pdf_data(pdf_path)
        
        # 2. PDF 데이터 파싱
        logger.info("PDF 데이터 파싱 시작")
        parsed_data = parse_pdf_data(pdf_data)
        
        # 3. 벡터 DB 네임스페이스 생성 (파일명 기반)
        filename = os.path.basename(pdf_path)
        namespace = f"lecture_{filename.replace('.', '_')}"
        
        # 4. 강의 스크립트 생성
        logger.info(f"강의 스크립트 생성 시작 (언어: {language})")
        script_data = generate_script(parsed_data, language, namespace)
        script_text = script_data["full_script"]
        
        # 5. 스크립트를 지식 베이스에 추가
        logger.info("스크립트를 지식 베이스에 추가")
        for i, page in enumerate(parsed_data.get('pages', [])):
            page_script = next((item['script'] for item in script_data.get('page_scripts', []) 
                                if item['page_number'] == page.get('page_number')), "")
            self.rag_system.add_page_to_knowledge(page, page_script)
        
        # 6. 스크립트를 오디오로 변환
        logger.info(f"스크립트를 오디오로 변환 시작 (언어: {language})")
        audio_results = self.tts_processor.generate_script_audio(
            script_data.get('page_scripts', []),
            language=language
        )
        audio_path = audio_results[0]["audio_path"]
        
        # 7. 결과 반환
        result = {
            'filename': filename,
            'language': language,
            'script_text': script_text,
            'audio_path': audio_path,
            'namespace': namespace
        }
        
        logger.info(f"PDF 처리 완료: {pdf_path}")
        return result
    except Exception as e:
        logger.error(f"PDF 처리 중 오류 발생: {str(e)}")
        return {'error': str(e)}