"""
PDF 파일에서 표 추출
"""
import os
import uuid
import io
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import camelot
import tabula

from ...utils.logger import get_logger
from ...utils.file_utils import is_valid_pdf, get_temp_path

logger = get_logger(__name__)

class TableExtractor:
    """PDF 파일에서 표 추출 클래스"""
    
    def __init__(self, 
                preferred_library: str = "camelot", 
                flavor: str = "lattice"):
        """표 추출기 초기화
        
        Args:
            preferred_library (str, optional): 선호하는 라이브러리 ('camelot' 또는 'tabula'). 기본값은 "camelot"
            flavor (str, optional): 표 형식 ('lattice' 또는 'stream'). 기본값은 "lattice"
        """
        self.preferred_library = preferred_library
        self.flavor = flavor
        logger.info(f"표 추출기 초기화 완료 (라이브러리: {preferred_library}, 형식: {flavor})")
    
    def extract_tables_from_pdf(self, 
                            pdf_path: str, 
                            pages: str = "all") -> Dict[int, List[pd.DataFrame]]:
        """PDF 파일에서 표 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            pages (str, optional): 페이지 범위 (예: "1,3,4-10" 또는 "all"). 기본값은 "all"
        
        Returns:
            Dict[int, List[pd.DataFrame]]: 페이지 번호를 키로 하는 표 데이터프레임 목록 딕셔너리
        """
        if not is_valid_pdf(pdf_path):
            logger.error(f"유효하지 않은 PDF 파일: {pdf_path}")
            return {}
        
        if self.preferred_library == "camelot":
            return self._extract_with_camelot(pdf_path, pages)
        else:
            return self._extract_with_tabula(pdf_path, pages)
    
    def _extract_with_camelot(self, 
                            pdf_path: str, 
                            pages: str) -> Dict[int, List[pd.DataFrame]]:
        """camelot을 사용하여 표 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            pages (str): 페이지 범위
        
        Returns:
            Dict[int, List[pd.DataFrame]]: 페이지 번호를 키로 하는 표 데이터프레임 목록 딕셔너리
        """
        result = {}
        
        try:
            # Camelot으로 표 추출
            tables = camelot.read_pdf(
                pdf_path,
                pages=pages,
                flavor=self.flavor
            )
            
            # 추출된 표 정리
            for table in tables:
                page_number = table.page
                df = table.df
                
                if page_number not in result:
                    result[page_number] = []
                
                result[page_number].append(df)
            
            num_tables = sum(len(tables) for tables in result.values())
            logger.info(f"camelot으로 {num_tables}개 표 추출 완료")
            return result
        except Exception as e:
            logger.error(f"camelot 표 추출 중 오류 발생: {e}")
            return {}
    
    def _extract_with_tabula(self, 
                            pdf_path: str, 
                            pages: str) -> Dict[int, List[pd.DataFrame]]:
        """tabula를 사용하여 표 추출
        
        Args:
            pdf_path (str): PDF 파일 경로
            pages (str): 페이지 범위
        
        Returns:
            Dict[int, List[pd.DataFrame]]: 페이지 번호를 키로 하는 표 데이터프레임 목록 딕셔너리
        """
        result = {}
        
        try:
            # 페이지 문자열을 tabula 형식으로 변환
            if pages == "all":
                tabula_pages = "all"
            else:
                tabula_pages = pages
            
            # Tabula로 표 추출
            dfs = tabula.read_pdf(
                pdf_path,
                pages=tabula_pages,
                multiple_tables=True
            )
            
            # 추출된 표 정리
            # tabula는 페이지 정보를 반환하지 않으므로 현재 페이지 추정
            if pages == "all" or "," in pages or "-" in pages:
                # 현재 버전에서는 페이지 정보 추정이 어려움
                # 모든 표를 페이지 1로 처리
                result[1] = dfs
            else:
                try:
                    # 단일 페이지인 경우
                    page_num = int(pages)
                    result[page_num] = dfs
                except ValueError:
                    # 변환 실패 시 페이지 1로 처리
                    result[1] = dfs
            
            num_tables = sum(len(tables) for tables in result.values())
            logger.info(f"tabula로 {num_tables}개 표 추출 완료")
            return result
        except Exception as e:
            logger.error(f"tabula 표 추출 중 오류 발생: {e}")
            return {}
    
    def tables_to_csv(self, 
                    tables: Dict[int, List[pd.DataFrame]], 
                    output_dir: Optional[str] = None) -> Dict[int, List[str]]:
        """추출된 표를 CSV 파일로 저장
        
        Args:
            tables (Dict[int, List[pd.DataFrame]]): 추출된 표 데이터
            output_dir (Optional[str], optional): 출력 디렉토리. 기본값은 임시 디렉토리
        
        Returns:
            Dict[int, List[str]]: 페이지 번호를 키로 하는 CSV 파일 경로 목록 딕셔너리
        """
        if not tables:
            logger.warning("저장할 표가 없습니다")
            return {}
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = get_temp_path(f"pdf_tables_{uuid.uuid4().hex}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        result = {}
        
        try:
            for page_num, dfs in tables.items():
                result[page_num] = []
                
                for i, df in enumerate(dfs):
                    # CSV 파일 경로
                    csv_path = os.path.join(output_dir, f"page_{page_num}_table_{i+1}.csv")
                    
                    # 데이터프레임을 CSV로 저장
                    df.to_csv(csv_path, index=False)
                    result[page_num].append(csv_path)
            
            num_files = sum(len(files) for files in result.values())
            logger.info(f"{num_files}개 표를 CSV로 저장 완료")
            return result
        except Exception as e:
            logger.error(f"표를 CSV로 저장 중 오류 발생: {e}")
            return {}
    
    def tables_to_markdown(self, 
                        tables: Dict[int, List[pd.DataFrame]]) -> Dict[int, List[str]]:
        """추출된 표를 마크다운 형식으로 변환
        
        Args:
            tables (Dict[int, List[pd.DataFrame]]): 추출된 표 데이터
        
        Returns:
            Dict[int, List[str]]: 페이지 번호를 키로 하는 마크다운 텍스트 목록 딕셔너리
        """
        if not tables:
            logger.warning("변환할 표가 없습니다")
            return {}
        
        result = {}
        
        try:
            for page_num, dfs in tables.items():
                result[page_num] = []
                
                for i, df in enumerate(dfs):
                    # 데이터프레임을 마크다운으로 변환
                    markdown = df.to_markdown(index=False)
                    result[page_num].append(markdown)
            
            num_tables = sum(len(tables) for tables in result.values())
            logger.info(f"{num_tables}개 표를 마크다운으로 변환 완료")
            return result
        except Exception as e:
            logger.error(f"표를 마크다운으로 변환 중 오류 발생: {e}")
            return {}
    
    def tables_to_json(self, 
                    tables: Dict[int, List[pd.DataFrame]]) -> Dict[int, List[str]]:
        """추출된 표를 JSON 형식으로 변환
        
        Args:
            tables (Dict[int, List[pd.DataFrame]]): 추출된 표 데이터
        
        Returns:
            Dict[int, List[str]]: 페이지 번호를 키로 하는 JSON 텍스트 목록 딕셔너리
        """
        if not tables:
            logger.warning("변환할 표가 없습니다")
            return {}
        
        result = {}
        
        try:
            for page_num, dfs in tables.items():
                result[page_num] = []
                
                for df in dfs:
                    # 데이터프레임을 JSON으로 변환
                    json_str = df.to_json(orient="records", force_ascii=False)
                    result[page_num].append(json_str)
            
            num_tables = sum(len(tables) for tables in result.values())
            logger.info(f"{num_tables}개 표를 JSON으로 변환 완료")
            return result
        except Exception as e:
            logger.error(f"표를 JSON으로 변환 중 오류 발생: {e}")
            return {}
    
    def analyze_table_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """표 내용 분석
        
        Args:
            df (pd.DataFrame): 분석할 표 데이터프레임
        
        Returns:
            Dict[str, Any]: 분석 결과
        """
        try:
            # 기본 분석 정보
            analysis = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "data_types": {col: str(df[col].dtype) for col in df.columns},
                "empty_cells": df.isna().sum().to_dict(),
                "summary": {}
            }
            
            # 숫자 열에 대한 통계 분석
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                analysis["summary"]["numeric"] = {}
                for col in numeric_cols:
                    analysis["summary"]["numeric"][col] = {
                        "min": df[col].min(),
                        "max": df[col].max(),
                        "mean": df[col].mean(),
                        "median": df[col].median()
                    }
            
            # 텍스트 열에 대한 분석
            text_cols = df.select_dtypes(include=['object']).columns
            if len(text_cols) > 0:
                analysis["summary"]["text"] = {}
                for col in text_cols:
                    unique_values = df[col].nunique()
                    most_common = df[col].value_counts().head(3).to_dict() if unique_values < len(df) / 2 else {}
                    analysis["summary"]["text"][col] = {
                        "unique_values": unique_values,
                        "most_common": most_common
                    }
            
            logger.info(f"표 분석 완료 ({analysis['rows']}행 x {analysis['columns']}열)")
            return analysis
        except Exception as e:
            logger.error(f"표 분석 중 오류 발생: {e}")
            return {"error": str(e)}
