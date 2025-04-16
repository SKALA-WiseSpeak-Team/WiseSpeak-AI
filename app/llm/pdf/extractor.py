# app/pdf/extractor.py
# PDF 데이터 추출 - 텍스트, 이미지, 표, 차트 등을 추출하는 기능

import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import tempfile
import logging
from io import BytesIO

import PyPDF2
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image
import pytesseract
import numpy as np

logger = logging.getLogger(__name__)

class PDFExtractor:
    """PDF에서 텍스트, 이미지, 표 등을 추출하는 클래스"""
    
    def __init__(self, pdf_path: str, language: str = "eng"):
        """
        초기화
        
        Args:
            pdf_path: PDF 파일 경로
            language: OCR 언어 (기본값: eng, 한국어: kor)
        """
        self.pdf_path = pdf_path
        self.language = language
        self._validate_file()
    
    def _validate_file(self):
        """PDF 파일이 존재하는지 확인"""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {self.pdf_path}")
        
        if not self.pdf_path.lower().endswith('.pdf'):
            raise ValueError(f"파일이 PDF 형식이 아닙니다: {self.pdf_path}")
    
    def extract_text(self) -> List[str]:
        """
        PDF에서 텍스트를 추출
        
        Returns:
            페이지별 텍스트 리스트
        """
        try:
            pages_text = []
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    pages_text.append(text)
            return pages_text
        except Exception as e:
            logger.error(f"텍스트 추출 중 오류 발생: {str(e)}")
            return []
    
    def extract_images(self) -> List[List[np.ndarray]]:
        """
        PDF에서 이미지를 추출
        
        Returns:
            페이지별 이미지 리스트 (numpy 배열 형식)
        """
        try:
            pages_images = []
            images = convert_from_path(self.pdf_path, dpi=300)
            
            for image in images:
                # PIL 이미지를 numpy 배열로 변환
                img_array = np.array(image)
                pages_images.append([img_array])
            
            return pages_images
        except Exception as e:
            logger.error(f"이미지 추출 중 오류 발생: {str(e)}")
            return []
    
    def extract_tables_ocr(self, pages_images: List[List[np.ndarray]]) -> List[List[str]]:
        """
        OCR을 사용하여 이미지에서 표를 추출
        
        Args:
            pages_images: 페이지별 이미지 리스트
        
        Returns:
            페이지별 표 텍스트 리스트
        """
        try:
            pages_tables = []
            
            for page_images in pages_images:
                page_tables = []
                
                for img_array in page_images:
                    # numpy 배열을 PIL 이미지로 변환
                    img = Image.fromarray(img_array)
                    
                    # OCR로 텍스트 추출
                    table_text = pytesseract.image_to_string(img, lang=self.language)
                    
                    # 기본적인 표 형식 감지 (예: 줄 끝에 '|' 문자가 있는 경우)
                    if '|' in table_text or '\t' in table_text:
                        page_tables.append(table_text)
                
                pages_tables.append(page_tables)
            
            return pages_tables
        except Exception as e:
            logger.error(f"표 추출 중 오류 발생: {str(e)}")
            return []
    
    def extract_all(self) -> Dict[str, Any]:
        """
        PDF에서 모든 정보를 추출
        
        Returns:
            페이지별 텍스트, 이미지, 표 등을 포함하는 딕셔너리
        """
        try:
            # 텍스트 추출
            pages_text = self.extract_text()
            
            # 이미지 추출
            pages_images = self.extract_images()
            
            # 표 추출
            pages_tables = self.extract_tables_ocr(pages_images)
            
            # 결과 구성
            result = {
                'filename': os.path.basename(self.pdf_path),
                'page_count': len(pages_text),
                'pages': []
            }
            
            for i in range(len(pages_text)):
                page_data = {
                    'page_number': i + 1,
                    'text': pages_text[i] if i < len(pages_text) else "",
                    'tables': pages_tables[i] if i < len(pages_tables) else [],
                    'has_image': len(pages_images) > i and len(pages_images[i]) > 0
                }
                result['pages'].append(page_data)
            
            return result
        except Exception as e:
            logger.error(f"데이터 추출 중 오류 발생: {str(e)}")
            return {'filename': os.path.basename(self.pdf_path), 'page_count': 0, 'pages': []}


def extract_pdf_data(pdf_path: str, language: str = "eng") -> Dict[str, Any]:
    """
    PDF 데이터 추출 헬퍼 함수
    
    Args:
        pdf_path: PDF 파일 경로
        language: OCR 언어
    
    Returns:
        추출된 PDF 데이터
    """
    extractor = PDFExtractor(pdf_path, language)
    return extractor.extract_all()