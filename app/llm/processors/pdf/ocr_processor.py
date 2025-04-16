"""
OCR 처리 모듈
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pytesseract
import cv2
import numpy as np

from ...config import config
from ...utils.logger import get_logger
from .image_extractor import ImageExtractor

logger = get_logger(__name__)

class OCRProcessor:
    """OCR 처리 클래스"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """OCR 처리기 초기화
        
        Args:
            tesseract_path (Optional[str], optional): Tesseract 실행 파일 경로. 기본값은 config에서 로드
        """
        self.tesseract_path = tesseract_path or config.TESSERACT_PATH
        self.image_extractor = ImageExtractor(tesseract_path=self.tesseract_path)
        
        # Tesseract 경로 설정
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info(f"OCR 처리기 초기화 완료")
    
    def extract_text_from_image(self, 
                            image_path: str, 
                            lang: str = "kor+eng",
                            preprocess: bool = True) -> str:
        """이미지에서 텍스트 추출
        
        Args:
            image_path (str): 이미지 파일 경로
            lang (str, optional): OCR 언어 코드. 기본값은 "kor+eng"
            preprocess (bool, optional): 전처리 수행 여부. 기본값은 True
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return ""
            
            # 전처리 수행
            if preprocess:
                image = self._preprocess_image(image)
            
            # OCR 수행
            text = pytesseract.image_to_string(image, lang=lang)
            
            logger.info(f"이미지 {Path(image_path).name}에서 OCR 수행 완료")
            return text
        except Exception as e:
            logger.error(f"OCR 수행 중 오류 발생: {e}")
            return ""
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """OCR을 위한 이미지 전처리
        
        Args:
            image (np.ndarray): 원본 이미지
        
        Returns:
            np.ndarray: 전처리된 이미지
        """
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 이진화
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 모폴로지 연산 (노이즈 제거)
            kernel = np.ones((1, 1), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            return opening
        except Exception as e:
            logger.error(f"이미지 전처리 중 오류 발생: {e}")
            return image
    
    def extract_text_with_layout(self, 
                                image_path: str, 
                                lang: str = "kor+eng") -> List[Dict[str, Any]]:
        """레이아웃 정보를 포함한 텍스트 추출
        
        Args:
            image_path (str): 이미지 파일 경로
            lang (str, optional): OCR 언어 코드. 기본값은 "kor+eng"
        
        Returns:
            List[Dict[str, Any]]: 텍스트 블록 목록
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return []
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # OCR 수행 (데이터 + 레이아웃 정보)
            data = pytesseract.image_to_data(gray, lang=lang, output_type=pytesseract.Output.DICT)
            
            # 결과 포맷팅
            blocks = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                # 빈 텍스트 무시
                if data['text'][i].strip() == '':
                    continue
                
                # 신뢰도가 낮은 텍스트 무시 (0~100)
                if int(data['conf'][i]) < 30:
                    continue
                
                # 텍스트 블록 정보
                block = {
                    'text': data['text'][i],
                    'confidence': data['conf'][i],
                    'position': {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    },
                    'block_num': data['block_num'][i],
                    'line_num': data['line_num'][i],
                    'word_num': data['word_num'][i]
                }
                
                blocks.append(block)
            
            logger.info(f"이미지 {Path(image_path).name}에서 {len(blocks)}개 텍스트 블록 추출 완료")
            return blocks
        except Exception as e:
            logger.error(f"레이아웃 텍스트 추출 중 오류 발생: {e}")
            return []
    
    def extract_text_from_pdf_with_ocr(self, 
                                    pdf_path: str, 
                                    lang: str = "kor+eng") -> Dict[int, str]:
        """PDF 파일 전체에 OCR 수행
        
        Args:
            pdf_path (str): PDF 파일 경로
            lang (str, optional): OCR 언어 코드. 기본값은 "kor+eng"
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 텍스트 딕셔너리
        """
        return self.image_extractor.extract_text_from_pdf_with_ocr(pdf_path, lang)
    
    def extract_text_from_pdf_image_by_page(self, 
                                        pdf_path: str, 
                                        page_num: int,
                                        lang: str = "kor+eng") -> str:
        """PDF의 특정 페이지에 OCR 수행
        
        Args:
            pdf_path (str): PDF 파일 경로
            page_num (int): 페이지 번호 (1-based)
            lang (str, optional): OCR 언어 코드. 기본값은 "kor+eng"
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            # PDF를 이미지로 변환
            image_paths = self.image_extractor.pdf_to_images(pdf_path)
            
            # 페이지 번호 유효성 검사
            if page_num < 1 or page_num > len(image_paths):
                logger.error(f"유효하지 않은 페이지 번호: {page_num} (총 {len(image_paths)}페이지)")
                return ""
            
            # 해당 페이지 이미지에 OCR 수행
            image_path = image_paths[page_num - 1]
            text = self.extract_text_from_image(image_path, lang)
            
            logger.info(f"PDF {Path(pdf_path).name}의 {page_num}페이지에 OCR 수행 완료")
            return text
        except Exception as e:
            logger.error(f"PDF 페이지 OCR 수행 중 오류 발생: {e}")
            return ""
    
    def recognize_languages(self, image_path: str) -> Dict[str, float]:
        """이미지의 언어 인식
        
        Args:
            image_path (str): 이미지 파일 경로
        
        Returns:
            Dict[str, float]: 언어 코드를 키로 하는 신뢰도 값 딕셔너리
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return {}
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # OCR로 언어 인식 시도 (다양한 언어 포함)
            osd = pytesseract.image_to_osd(gray, output_type=pytesseract.Output.DICT)
            
            # 간단한 언어 신뢰도 계산 (실제로는 더 복잡한 로직 필요)
            languages = {
                "eng": 0.0,  # 영어
                "kor": 0.0,  # 한국어
                "jpn": 0.0,  # 일본어
                "chi_sim": 0.0  # 중국어 간체
            }
            
            # 스크립트 타입에 따른 기본 신뢰도 설정
            script = osd.get('script', '')
            if script == 'Latin':
                languages["eng"] = 0.8
            elif script == 'Hangul':
                languages["kor"] = 0.8
            elif script == 'Hiragana' or script == 'Katakana':
                languages["jpn"] = 0.8
            elif script == 'Han':
                languages["chi_sim"] = 0.6
                languages["jpn"] = 0.4
            
            logger.info(f"이미지 {Path(image_path).name}의 언어 인식 완료 (주요 스크립트: {script})")
            return languages
        except Exception as e:
            logger.error(f"언어 인식 중 오류 발생: {e}")
            return {"eng": 0.5}  # 오류 시 기본값
