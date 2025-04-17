# app/process_common_data.py
# 공통 참조용 데이터를 default 네임스페이스에 추가하는 유틸리티

import os
import sys
import logging
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

# 상대 경로 임포트를 위한 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.ai.rag import add_common_knowledge_to_default
from app.core.config import settings
from app.llm.pdf.extractor import extract_pdf_data
from app.llm.pdf.parser import parse_pdf_data

# 로깅 가져오기
logger = logging.getLogger(__name__)

def process_common_data(data_text: str, source_name: str = "common_data") -> List[str]:
    """
    공통 데이터를 default 네임스페이스에 추가
    
    Args:
        data_text: 추가할 데이터 텍스트
        source_name: 데이터 출처 이름 (메타데이터용)
    
    Returns:
        추가된 청크 ID 리스트
    """
    try:
        # 메타데이터 준비
        metadata = {
            "source": source_name,
            "type": "common_knowledge",
            "namespace": "default"
        }
        
        # default 네임스페이스에 데이터 추가
        logger.info(f"공통 데이터 추가 중: {source_name}")
        chunk_ids = add_common_knowledge_to_default(data_text, metadata)
        
        logger.info(f"{len(chunk_ids)}개 청크가 추가되었습니다: {source_name}")
        return chunk_ids
    except Exception as e:
        logger.error(f"공통 데이터 추가 중 오류 발생: {str(e)}")
        return []

def process_text_file(file_path: str) -> List[str]:
    """
    텍스트 파일을 경로로 받아 처리
    
    Args:
        file_path: 텍스트 파일 경로
    
    Returns:
        추가된 청크 ID 리스트
    """
    try:
        # 파일 이름을 소스 이름으로 사용
        source_name = os.path.basename(file_path)
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data_text = f.read()
        
        if not data_text.strip():
            logger.warning(f"빈 파일: {file_path}")
            return []
        
        # 공통 데이터 처리
        return process_common_data(data_text, source_name)
    except Exception as e:
        logger.error(f"파일 처리 중 오류 발생: {str(e)}")
        return []

def process_pdf_file(file_path: str, language: str = "eng") -> List[str]:
    """
    PDF 파일을 경로로 받아 처리
    
    Args:
        file_path: PDF 파일 경로
        language: OCR 언어 (기본값: eng, 한국어: kor)
    
    Returns:
        추가된 청크 ID 리스트
    """
    try:
        # 파일 이름을 소스 이름으로 사용
        source_name = os.path.basename(file_path)
        
        logger.info(f"PDF 파일 처리 중: {file_path}")
        
        # PDF 데이터 추출
        pdf_data = extract_pdf_data(file_path, language)
        
        # PDF 데이터 파싱
        parsed_data = parse_pdf_data(pdf_data)
        
        # 모든 페이지의 텍스트 결합
        all_text = ""
        
        for page in parsed_data.get('pages', []):
            page_text = page.get('text', '')
            if page_text.strip():
                all_text += page_text + "\n\n"
        
        if not all_text.strip():
            logger.warning(f"PDF에서 텍스트를 추출할 수 없습니다: {file_path}")
            return []
        
        # 메타데이터 준비: 페이지 수 추가
        metadata_info = f"출처: {source_name}, 페이지 수: {parsed_data.get('page_count', 0)}"
        
        # 공통 데이터 처리
        return process_common_data(all_text, f"{source_name} (PDF)")
    except Exception as e:
        logger.error(f"PDF 파일 처리 중 오류 발생: {str(e)}")
        return []

def main():
    """고정된 공통 데이터를 default 네임스페이스에 추가하는 CLI 도구"""
    parser = argparse.ArgumentParser(description='공통 지식을 default 네임스페이스에 추가하는 도구')
    
    # 파일 경로 반드시 입력
    parser.add_argument('file_path', help='추가할 파일 경로 (텍스트 또는 PDF)')
    
    # 디렉토리 컬렉션 옵션
    parser.add_argument('--dir', action='store_true', help='파일 경로가 디렉토리인 경우 모든 .txt 및 .pdf 파일 처리')
    
    # PDF OCR 언어 설정 (한국어 PDF 처리용)
    parser.add_argument('--language', '-l', default='eng', help='PDF OCR 언어 (eng: 영어, kor: 한국어)')

    
    args = parser.parse_args()
    
    # 디렉토리 확인
    settings.ensure_directories()
    
    # 디렉토리 컬렉션 처리
    if args.dir and os.path.isdir(args.file_path):
        logger.info(f"디렉토리에서 파일 처리 중: {args.file_path}")
        processed_files = 0
        
        # 디렉토리의 모든 .txt 및 .pdf 파일 처리
        for filename in os.listdir(args.file_path):
            file_path = os.path.join(args.file_path, filename)
            
            if filename.lower().endswith('.txt'):
                logger.info(f"텍스트 파일 처리: {filename}")
                chunk_ids = process_text_file(file_path)
                if chunk_ids:
                    processed_files += 1
            
            elif filename.lower().endswith('.pdf'):
                logger.info(f"PDF 파일 처리: {filename}")
                chunk_ids = process_pdf_file(file_path, args.language)
                if chunk_ids:
                    processed_files += 1
        
        logger.info(f"{processed_files}개 파일을 처리했습니다.")
    else:
        # 단일 파일 처리
        if not os.path.isfile(args.file_path):
            logger.error(f"파일을 찾을 수 없습니다: {args.file_path}")
            return
        
        logger.info(f"파일 처리 중: {args.file_path}")
        
        if args.file_path.lower().endswith('.pdf'):
            # PDF 파일 처리
            chunk_ids = process_pdf_file(args.file_path, args.language)
        else:
            # 기타 파일은 텍스트 파일로 처리
            chunk_ids = process_text_file(args.file_path)
            
        logger.info(f"처리 완료. {len(chunk_ids)}개 청크가 추가되었습니다.")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('common_data_process.log')
        ]
    )
    
    main()