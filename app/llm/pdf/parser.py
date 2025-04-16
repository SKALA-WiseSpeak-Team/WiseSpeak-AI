# app/pdf/parser.py
# 추출된 PDF 데이터 파싱 - 텍스트, 이미지, 표 등을 구분하여 정리하고 강의 스크립트 생성 준비

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    """추출된 PDF 데이터를 파싱하는 클래스"""
    
    def __init__(self, pdf_data: Dict[str, Any]):
        """
        초기화
        
        Args:
            pdf_data: PDF에서 추출된 데이터
        """
        self.pdf_data = pdf_data
        self.filename = pdf_data.get('filename', '')
        self.page_count = pdf_data.get('page_count', 0)
        self.pages = pdf_data.get('pages', [])
    
    def _clean_text(self, text: str) -> str:
        """
        텍스트 정리
        
        Args:
            text: 원본 텍스트
        
        Returns:
            정리된 텍스트
        """
        if not text:
            return ""
        
        # 연속된 공백 제거
        cleaned = re.sub(r'\s+', ' ', text)
        # 텍스트 앞뒤 공백 제거
        cleaned = cleaned.strip()
        return cleaned
    
    def _parse_table(self, table_text: str) -> List[List[str]]:
        """
        표 텍스트를 파싱하여 2차원 배열로 변환
        
        Args:
            table_text: 표 텍스트
        
        Returns:
            2차원 배열 형태의 표 데이터
        """
        if not table_text:
            return []
        
        parsed_table = []
        
        # 줄 단위로 분리
        rows = table_text.split('\n')
        for row in rows:
            if row.strip():
                # '|'로 셀 구분 (표 형식이 '|'로 구분된 경우)
                if '|' in row:
                    cells = [cell.strip() for cell in row.split('|')]
                    # 빈 셀 제거
                    cells = [cell for cell in cells if cell]
                # 탭으로 셀 구분
                elif '\t' in row:
                    cells = [cell.strip() for cell in row.split('\t')]
                # 공백으로 셀 구분 (덜 정확함)
                else:
                    cells = [cell.strip() for cell in row.split('  ') if cell.strip()]
                
                if cells:
                    parsed_table.append(cells)
        
        return parsed_table
    
    def parse_page(self, page_number: int) -> Dict[str, Any]:
        """
        특정 페이지 데이터 파싱
        
        Args:
            page_number: 페이지 번호 (1부터 시작)
        
        Returns:
            파싱된 페이지 데이터
        """
        if page_number < 1 or page_number > self.page_count:
            logger.error(f"유효하지 않은 페이지 번호: {page_number}")
            return {}
        
        page_data = self.pages[page_number - 1]
        
        # 텍스트 정리
        cleaned_text = self._clean_text(page_data.get('text', ''))
        
        # 표 파싱
        tables = []
        for table_text in page_data.get('tables', []):
            parsed_table = self._parse_table(table_text)
            if parsed_table:
                tables.append(parsed_table)
        
        # 제목, 소제목 추출 (간단한 휴리스틱 사용)
        titles = []
        subtitles = []
        
        text_lines = cleaned_text.split('\n')
        for line in text_lines:
            line = line.strip()
            if not line:
                continue
            
            # 제목 판단 (짧고, 대문자가 많거나, 특정 기호로 끝나지 않는 등)
            if len(line) < 100 and (line.isupper() or not line.endswith(('.', ',', ';', ':', '?', '!'))):
                if len(line) < 50:
                    titles.append(line)
                else:
                    subtitles.append(line)
        
        # 결과 구성
        parsed_data = {
            'page_number': page_number,
            'text': cleaned_text,
            'titles': titles,
            'subtitles': subtitles,
            'tables': tables,
            'has_image': page_data.get('has_image', False)
        }
        
        return parsed_data
    
    def parse_all(self) -> Dict[str, Any]:
        """
        모든 페이지 데이터 파싱
        
        Returns:
            파싱된 모든 페이지 데이터
        """
        parsed_pages = []
        
        for page_number in range(1, self.page_count + 1):
            parsed_page = self.parse_page(page_number)
            if parsed_page:
                parsed_pages.append(parsed_page)
        
        # 문서 전체 데이터
        document_data = {
            'filename': self.filename,
            'page_count': self.page_count,
            'pages': parsed_pages,
            'document_structure': self._extract_document_structure(parsed_pages)
        }
        
        return document_data
    
    def _extract_document_structure(self, parsed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 구조 추출
        
        Args:
            parsed_pages: 파싱된 페이지 데이터 리스트
        
        Returns:
            문서 구조 정보
        """
        # 모든 제목과 소제목을 수집
        all_titles = []
        all_subtitles = []
        
        for page in parsed_pages:
            all_titles.extend([(title, page['page_number']) for title in page.get('titles', [])])
            all_subtitles.extend([(subtitle, page['page_number']) for subtitle in page.get('subtitles', [])])
        
        # 문서 구조 생성
        structure = {
            'main_title': all_titles[0][0] if all_titles else "",
            'sections': []
        }
        
        current_section = None
        
        # 제목을 기준으로 섹션 구분
        for i, (title, page_num) in enumerate(all_titles):
            if i == 0 and structure['main_title'] == title:
                continue
                
            section = {
                'title': title,
                'page': page_num,
                'subsections': []
            }
            
            structure['sections'].append(section)
            current_section = section
        
        # 소제목을 해당 섹션의 하위 섹션으로 할당
        for subtitle, page_num in all_subtitles:
            if not structure['sections']:
                # 섹션이 없는 경우 기본 섹션 생성
                section = {
                    'title': structure['main_title'] or "문서",
                    'page': 1,
                    'subsections': []
                }
                structure['sections'].append(section)
                current_section = section
            
            subsection = {
                'title': subtitle,
                'page': page_num
            }
            
            # 페이지 번호로 가장 가까운 섹션 찾기
            closest_section = None
            min_distance = float('inf')
            
            for section in structure['sections']:
                distance = abs(section['page'] - page_num)
                if distance < min_distance:
                    min_distance = distance
                    closest_section = section
            
            if closest_section:
                closest_section['subsections'].append(subsection)
        
        return structure


def parse_pdf_data(pdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    PDF 데이터 파싱 헬퍼 함수
    
    Args:
        pdf_data: PDF에서 추출된 데이터
    
    Returns:
        파싱된 PDF 데이터
    """
    parser = PDFParser(pdf_data)
    return parser.parse_all()