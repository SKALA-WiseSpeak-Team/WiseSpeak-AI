import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union
import argparse
from pathlib import Path

# 상대 경로 임포트를 위한 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.llm.pdf.extractor import extract_pdf_data
from app.llm.pdf.parser import parse_pdf_data
from app.llm.vector_db.embeddings import get_embedder, chunk_document
from app.llm.ai.script_gen import generate_script
from app.llm.ai.rag import get_rag_system
from app.llm.audio.tts import get_tts_processor
from app.llm.audio.stt import get_stt_processor
from app.llm.language.detector import get_language_detector
from app.llm.language.translator import get_translator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('lecture_rag_system.log')
    ]
)

logger = logging.getLogger(__name__)

class LectureRAGSystem:
    """PDF 기반 다국어 강의 생성 및 질의응답 시스템"""
    
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
    
    def process_audio_query(self, audio_data: bytes, namespace: str, language: str) -> Dict[str, Any]:
        """
        음성 질의 처리
        
        Args:
            audio_data: 오디오 바이너리 데이터
            namespace: 벡터 DB 네임스페이스
        
        Returns:
            처리 결과
        """
        try:
            # # 1. 음성을 텍스트로 변환
            # logger.info("음성을 텍스트로 변환")
            # stt_result = self.stt_processor.speech_to_text_from_bytes(audio_data)
            
            # query_text = stt_result.get('text', '')
            # detected_language = stt_result.get('language', 'en')
            
            # if not query_text:
            #     logger.warning("변환된 질의 텍스트가 없습니다")
            #     return {'error': '질의를 인식할 수 없습니다.'}
            
            # 2. 벡터 DB에서 RAG 기반 답변 생성
            logger.info(f"RAG 기반 답변 생성 (언어: {language})")
            rag_result = self.rag_system.query(audio_data, language, namespace=namespace)
            
            answer_text = rag_result.get('answer', '')
            
            if not answer_text:
                logger.warning("생성된 답변이 없습니다")
                return {'error': '답변을 생성할 수 없습니다.'}
            
            # 3. 답변을 음성으로 변환
            # logger.info(f"답변을 음성으로 변환 (언어: {language})")
            # answer_audio = self.tts_processor.text_to_speech(
            #     text=answer_text,
            #     language=language,
            #     voice="auto"
            # )
            
            # 4. 결과 반환
            result = {
                'query': audio_data,
                'query_language': language,
                'answer': answer_text,
                # 'answer_audio_path': answer_audio,
                'relevant_sources': rag_result.get('relevant_sources', [])
            }
            
            logger.info("음성 질의 처리 완료")
            return result
        except Exception as e:
            logger.error(f"음성 질의 처리 중 오류 발생: {str(e)}")
            return {'error': str(e)}
        
    def text_query(self, query_text: str, namespace: str, language: Optional[str] = None) -> Dict[str, Any]:
        try:
            # 언어 감지 (지정되지 않은 경우)
            if language is None:
                language = self.language_detector.detect_language(query_text)
            
            # RAG 시스템 인스턴스 생성 (지정된 PDF 네임스페이스와 기본 네임스페이스 모두 사용)
            # 'default' 네임스페이스는 공통 지식베이스로 항상 참조
            namespaces = [namespace, "default"]
            logger.info(f"참조 네임스페이스: {namespaces}")
            
            # RAG 기반 답변 생성 (여러 네임스페이스 참조)
            logger.info(f"텍스트 질의 처리 (언어: {language})")
            rag_system = get_rag_system()
            rag_result = rag_system.query(query_text, language, use_history=True, namespaces=namespaces)
            
            return rag_result
        except Exception as e:
            logger.error(f"텍스트 질의 처리 중 오류 발생: {str(e)}")
            return {'error': str(e)}
