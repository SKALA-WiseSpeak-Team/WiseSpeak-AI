"""
PDF 파일에서 텍스트 추출
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import PyPDF2
import pdfplumber

from ...utils.logger import get_logger
from ...utils.file_utils import is_valid_pdf

logger = get_logger(__name__)

class TextExtractor:
    """PDF 파일에서 텍스트 추출 클래스"""
    
    def __init__(self, use_pdfplumber: bool = True):
        """텍스트 추출기 초기화
        
        Args:
            use_pdfplumber (bool, optional): pdfplumber 사용 여부. 기본값은 True
        """
        self.use_pdfplumber = use_pdfplumber
        logger.info(f"텍스트 추출기 초기화 완료 (pdfplumber 사용: {use_pdfplumber})")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, str]:
        """PDF 파일에서 페이지별 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 텍스트 딕셔너리
        """
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return {}
        
        if self.use_pdfplumber:
            return self._extract_with_pdfplumber(pdf_path)
        else:
            return self._extract_with_pypdf2(pdf_path)
    
    def _extract_with_pypdf2(self, pdf_path: str) -> Dict[int, str]:
        """PyPDF2를 사용하여 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 텍스트 딕셔너리
        """
        result = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                for page_num in range(total_pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    result[page_num + 1] = text  # 1-based 페이지 번호
            
            logger.info(f"PyPDF2로 텍스트 추출 완료, 총 {total_pages}페이지")
            return result
        except Exception as e:
            logger.error(f"PyPDF2 텍스트 추출 중 오류 발생: {e}")
            return {}
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict[int, str]:
        """pdfplumber를 사용하여 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 텍스트 딕셔너리
        """
        result = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    result[page_num] = text
            
            logger.info(f"pdfplumber로 텍스트 추출 완료, 총 {total_pages}페이지")
            return result
        except Exception as e:
            logger.error(f"pdfplumber 텍스트 추출 중 오류 발생: {e}")
            return {}
    
    def extract_with_layout(self, pdf_path: str) -> Dict[int, List[Dict[str, Any]]]:
        """레이아웃 정보를 포함한 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
        
        Returns:
            Dict[int, List[Dict[str, Any]]]: 페이지별 텍스트 블록 목록
        """
        result = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    blocks = []
                    
                    # 텍스트 추출
                    chars = page.chars
                    if chars:
                        for char in chars:
                            text = char['text']
                            x0, top, x1, bottom = char['x0'], char['top'], char['x1'], char['bottom']
                            font_size = char.get('size', 0)
                            font_name = char.get('fontname', '')
                            
                            blocks.append({
                                'type': 'text',
                                'content': text,
                                'position': {
                                    'x0': x0,
                                    'y0': top,
                                    'x1': x1,
                                    'y1': bottom
                                },
                                'font_size': font_size,
                                'font_name': font_name
                            })
                    
                    result[page_num] = blocks
                
            logger.info(f"레이아웃 정보 포함 텍스트 추출 완료")
            return result
        except Exception as e:
            logger.error(f"레이아웃 텍스트 추출 중 오류 발생: {e}")
            return {}
    
    def extract_text_by_page_range(self, pdf_path: str, start_page: int, end_page: int) -> Dict[int, str]:
        """특정 페이지 범위의 텍스트 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            start_page (int): 시작 페이지 (1-based)
            end_page (int): 종료 페이지 (1-based)
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 텍스트 딕셔너리
        """
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return {}
        
        try:
            all_pages = self.extract_text_from_pdf(pdf_path)
            page_range = {p: all_pages[p] for p in range(start_page, end_page + 1) if p in all_pages}
            
            logger.info(f"페이지 범위 {start_page}-{end_page} 텍스트 추출 완료")
            return page_range
        except Exception as e:
            logger.error(f"페이지 범위 텍스트 추출 중 오류 발생: {e}")
            return {}
    
    def get_document_info(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 문서 정보 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
        
        Returns:
            Dict[str, Any]: 문서 정보
        """
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return {}
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                
                document_info = {
                    'title': info.title if info and hasattr(info, 'title') else None,
                    'author': info.author if info and hasattr(info, 'author') else None,
                    'subject': info.subject if info and hasattr(info, 'subject') else None,
                    'creator': info.creator if info and hasattr(info, 'creator') else None,
                    'producer': info.producer if info and hasattr(info, 'producer') else None,
                    'total_pages': len(reader.pages),
                    'file_name': Path(pdf_path).name,
                    'file_size': os.path.getsize(pdf_path)
                }
                
                logger.info(f"문서 정보 추출 완료: {document_info['file_name']}")
                return document_info
        except Exception as e:
            logger.error(f"문서 정보 추출 중 오류 발생: {e}")
            return {}
