"""
문서 청크화 모듈
"""
from typing import List, Dict, Any, Optional, Tuple
import re

from ...config import config
from ...utils.logger import get_logger

logger = get_logger(__name__)

class DocumentChunker:
    """문서 청크화 클래스"""
    
    def __init__(self, 
                chunk_size: int = None, 
                chunk_overlap: int = None,
                chunking_strategy: str = "sentence"):
        """청크화 처리기 초기화
        
        Args:
            chunk_size (int, optional): 청크 크기. 기본값은 config에서 로드
            chunk_overlap (int, optional): 청크 겹침 크기. 기본값은 config에서 로드
            chunking_strategy (str, optional): 청크화 전략 ('character', 'sentence', 'paragraph'). 기본값은 "sentence"
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        self.chunking_strategy = chunking_strategy
        
        logger.info(f"문서 청크화 처리기 초기화 완료 (청크 크기: {self.chunk_size}, 겹침: {self.chunk_overlap}, 전략: {self.chunking_strategy})")
    
    def chunk_text(self, text: str) -> List[str]:
        """텍스트를 청크로 분할
        
        Args:
            text (str): 분할할 텍스트
        
        Returns:
            List[str]: 청크 목록
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트가 전달되어 분할을 건너뜁니다")
            return []
        
        if self.chunking_strategy == "character":
            return self._chunk_by_character(text)
        elif self.chunking_strategy == "paragraph":
            return self._chunk_by_paragraph(text)
        else:  # default: 'sentence'
            return self._chunk_by_sentence(text)
    
    def _chunk_by_character(self, text: str) -> List[str]:
        """문자 단위로 청크화
        
        Args:
            text (str): 분할할 텍스트
        
        Returns:
            List[str]: 청크 목록
        """
        chunks = []
        text = text.strip()
        start = 0
        
        while start < len(text):
            # 청크 크기를 고려한 종료 위치
            end = min(start + self.chunk_size, len(text))
            
            # 청크 추출
            chunk = text[start:end]
            chunks.append(chunk)
            
            # 다음 시작 위치 (겹침 고려)
            start = end - self.chunk_overlap
            
            # 진행이 없는 경우 무한 루프 방지
            if start >= end:
                start = end
        
        logger.debug(f"텍스트를 {len(chunks)}개의 문자 기반 청크로 분할")
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """문장 단위로 청크화
        
        Args:
            text (str): 분할할 텍스트
        
        Returns:
            List[str]: 청크 목록
        """
        # 문장 분리를 위한 정규식 (한국어 포함)
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z가-힣])'
        sentences = re.split(sentence_endings, text)
        
        # 작은 문장들 결합
        processed_sentences = []
        current_sentence = ""
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            if len(current_sentence) + len(sentence) < self.chunk_size:
                current_sentence += " " + sentence if current_sentence else sentence
            else:
                if current_sentence:
                    processed_sentences.append(current_sentence)
                current_sentence = sentence
        
        # 마지막 문장 추가
        if current_sentence:
            processed_sentences.append(current_sentence)
        
        # 청크 생성
        chunks = []
        current_chunk = ""
        
        for sentence in processed_sentences:
            # 문장이 청크 크기보다 큰 경우
            if len(sentence) > self.chunk_size:
                # 기존 청크 추가
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # 큰 문장은 문자 기반으로 분할
                sentence_chunks = self._chunk_by_character(sentence)
                chunks.extend(sentence_chunks)
                continue
                
            # 청크 크기를 초과하는지 확인
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.debug(f"텍스트를 {len(chunks)}개의 문장 기반 청크로 분할")
        return chunks
    
    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """단락 단위로 청크화
        
        Args:
            text (str): 분할할 텍스트
        
        Returns:
            List[str]: 청크 목록
        """
        # 단락 분리 (빈 줄 기준)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 단락이 청크 크기보다 큰 경우
            if len(paragraph) > self.chunk_size:
                # 기존 청크 추가
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # 큰 단락은 문장 기반으로 분할
                paragraph_chunks = self._chunk_by_sentence(paragraph)
                chunks.extend(paragraph_chunks)
                continue
                
            # 청크 크기를 초과하는지 확인
            if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.debug(f"텍스트를 {len(chunks)}개의 단락 기반 청크로 분할")
        return chunks
    
    def chunk_document(self, document: Dict[int, str]) -> Dict[str, List[Dict[str, Any]]]:
        """페이지별 문서 텍스트를 청크화
        
        Args:
            document (Dict[int, str]): 페이지 번호를 키로 하는 텍스트 딕셔너리
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 메타데이터를 포함한 청크 데이터
        """
        chunked_document = {"chunks": []}
        
        for page_num, text in document.items():
            chunks = self.chunk_text(text)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"page_{page_num}_chunk_{i+1}"
                chunk_data = {
                    "chunk_id": chunk_id,
                    "page_number": page_num,
                    "chunk_index": i,
                    "text": chunk,
                    "metadata": {
                        "page_number": page_num,
                        "chunk_index": i,
                        "chunk_id": chunk_id,
                    }
                }
                chunked_document["chunks"].append(chunk_data)
        
        logger.info(f"문서를 총 {len(chunked_document['chunks'])}개 청크로 분할 완료")
        return chunked_document
    
    def chunk_document_with_overlap(self, 
                                document: Dict[int, str], 
                                overlap_pages: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """페이지 간 겹침을 포함한 문서 청크화
        
        Args:
            document (Dict[int, str]): 페이지 번호를 키로 하는 텍스트 딕셔너리
            overlap_pages (bool, optional): 페이지 간 겹침 사용 여부. 기본값은 True
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 메타데이터를 포함한 청크 데이터
        """
        chunked_document = {"chunks": []}
        
        if not overlap_pages:
            return self.chunk_document(document)
        
        # 페이지 번호 정렬
        page_numbers = sorted(document.keys())
        
        # 각 페이지를 청크화하되, 페이지 간 겹침 고려
        for i, page_num in enumerate(page_numbers):
            text = document[page_num]
            
            # 이전 페이지의 마지막 부분을 현재 페이지 앞에 추가
            if i > 0 and overlap_pages:
                prev_page_num = page_numbers[i-1]
                prev_text = document[prev_page_num]
                
                # 이전 페이지의 마지막 부분 (최대 청크 겹침 크기만큼)
                overlap_size = min(self.chunk_overlap, len(prev_text))
                overlap_text = prev_text[-overlap_size:] if overlap_size > 0 else ""
                
                # 텍스트 결합
                text = overlap_text + "\n" + text
            
            # 현재 페이지 텍스트 청크화
            chunks = self.chunk_text(text)
            
            for j, chunk in enumerate(chunks):
                chunk_id = f"page_{page_num}_chunk_{j+1}"
                chunk_data = {
                    "chunk_id": chunk_id,
                    "page_number": page_num,
                    "chunk_index": j,
                    "text": chunk,
                    "metadata": {
                        "page_number": page_num,
                        "chunk_index": j,
                        "chunk_id": chunk_id,
                        "spans_pages": overlap_pages and j == 0 and i > 0
                    }
                }
                chunked_document["chunks"].append(chunk_data)
        
        logger.info(f"문서를 페이지 겹침을 포함하여 총 {len(chunked_document['chunks'])}개 청크로 분할 완료")
        return chunked_document
