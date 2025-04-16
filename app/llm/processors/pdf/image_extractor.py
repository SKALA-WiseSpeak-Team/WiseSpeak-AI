"""
PDF 파일에서 이미지 추출
"""
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pdf2image
import cv2
import numpy as np
import pytesseract

from ...config import config
from ...utils.logger import get_logger
from ...utils.file_utils import is_valid_pdf, ensure_directory, get_temp_path

logger = get_logger(__name__)

class ImageExtractor:
    """PDF 파일에서 이미지 추출 클래스"""
    
    def __init__(self, 
                dpi: int = 300, 
                output_format: str = "png",
                tesseract_path: Optional[str] = None):
        """이미지 추출기 초기화
        
        Args:
            dpi (int, optional): 이미지 해상도. 기본값은 300
            output_format (str, optional): 출력 이미지 형식. 기본값은 "png"
            tesseract_path (Optional[str], optional): Tesseract 실행 파일 경로. 기본값은 config에서 로드
        """
        self.dpi = dpi
        self.output_format = output_format
        self.tesseract_path = tesseract_path or config.TESSERACT_PATH
        
        # Tesseract 경로 설정
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info(f"이미지 추출기 초기화 완료 (DPI: {dpi}, 형식: {output_format})")
    
    def pdf_to_images(self, pdf_path: str, output_dir: Optional[str] = None) -> List[str]:
        """PDF를 페이지별 이미지로 변환
        
        Args:
            pdf_path (str): PDF 파일 경로
            output_dir (Optional[str], optional): 이미지 저장 디렉토리. 기본값은 임시 디렉토리
        
        Returns:
            List[str]: 생성된 이미지 파일 경로 목록
        """
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return []
        
        try:
            # 출력 디렉토리 설정
            if output_dir is None:
                output_dir = get_temp_path(f"pdf_images_{uuid.uuid4().hex}")
            
            ensure_directory(output_dir)
            
            # PDF를 이미지로 변환
            images = pdf2image.convert_from_path(
                pdf_path, 
                dpi=self.dpi, 
                output_folder=output_dir,
                fmt=self.output_format
            )
            
            # 생성된 이미지 파일 경로 목록
            image_paths = []
            for i, image in enumerate(images):
                image_path = os.path.join(output_dir, f"page_{i+1}.{self.output_format}")
                # 이미 저장되었는지 확인
                if not os.path.exists(image_path):
                    image.save(image_path)
                image_paths.append(image_path)
            
            logger.info(f"PDF {Path(pdf_path).name}를 {len(image_paths)}개의 이미지로 변환 완료")
            return image_paths
        except Exception as e:
            logger.error(f"PDF를 이미지로 변환 중 오류 발생: {e}")
            return []
    
    def extract_images_from_pdf(self, pdf_path: str, output_dir: Optional[str] = None) -> Dict[int, List[str]]:
        """PDF 파일에서 포함된 이미지 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            output_dir (Optional[str], optional): 이미지 저장 디렉토리
        
        Returns:
            Dict[int, List[str]]: 페이지 번호를 키로 하는 이미지 경로 목록 딕셔너리
        """
        # 현재는 페이지별 이미지로 변환하는 메소드 사용
        # PDF 내부 이미지 추출은 더 복잡한 라이브러리 필요 (예: fitz/PyMuPDF)
        image_paths = self.pdf_to_images(pdf_path, output_dir)
        
        result = {}
        for i, path in enumerate(image_paths):
            result[i+1] = [path]
        
        return result
    
    def perform_ocr(self, image_path: str, lang: str = "kor+eng") -> str:
        """이미지에서 OCR 수행
        
        Args:
            image_path (str): 이미지 파일 경로
            lang (str, optional): OCR 언어 코드. 기본값은 "kor+eng"
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return ""
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 노이즈 제거 및 대비 향상
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # OCR 수행
            text = pytesseract.image_to_string(gray, lang=lang)
            
            logger.info(f"이미지 {Path(image_path).name}에서 OCR 수행 완료")
            return text
        except Exception as e:
            logger.error(f"OCR 수행 중 오류 발생: {e}")
            return ""
    
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
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return {}
        
        try:
            # PDF를 이미지로 변환
            image_paths = self.pdf_to_images(pdf_path)
            
            # 각 이미지에 OCR 수행
            results = {}
            for i, image_path in enumerate(image_paths):
                text = self.perform_ocr(image_path, lang)
                results[i+1] = text
            
            logger.info(f"PDF {Path(pdf_path).name}에 OCR 수행 완료, 총 {len(results)}페이지")
            return results
        except Exception as e:
            logger.error(f"PDF OCR 수행 중 오류 발생: {e}")
            return {}
    
    def detect_image_regions(self, image_path: str) -> List[Dict[str, Any]]:
        """이미지에서 영역 감지 (텍스트, 이미지 등)
        
        Args:
            image_path (str): 이미지 파일 경로
        
        Returns:
            List[Dict[str, Any]]: 감지된 영역 정보 목록
        """
        try:
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"이미지를 읽을 수 없습니다: {image_path}")
                return []
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 엣지 감지
            edges = cv2.Canny(gray, 50, 150)
            
            # 윤곽선 찾기
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 찾은 영역 정보 반환
            regions = []
            for contour in contours:
                # 작은 영역 무시
                if cv2.contourArea(contour) < 500:
                    continue
                
                # 영역 좌표
                x, y, w, h = cv2.boundingRect(contour)
                
                # OCR로 텍스트 영역인지 확인
                roi = gray[y:y+h, x:x+w]
                text = pytesseract.image_to_string(roi)
                
                # 텍스트가 있으면 텍스트 영역, 없으면 이미지 영역으로 분류
                region_type = "text" if text.strip() else "image"
                
                regions.append({
                    "type": region_type,
                    "position": {
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h
                    },
                    "text": text if region_type == "text" else None
                })
            
            logger.info(f"이미지 {Path(image_path).name}에서 {len(regions)}개 영역 감지")
            return regions
        except Exception as e:
            logger.error(f"이미지 영역 감지 중 오류 발생: {e}")
            return []
