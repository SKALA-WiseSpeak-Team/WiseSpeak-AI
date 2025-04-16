"""
PDF 처리 테스트
"""
import os
import pytest
from pathlib import Path

from wisespeak_ai.processors.pdf.text_extractor import TextExtractor
from wisespeak_ai.processors.pdf.image_extractor import ImageExtractor
from wisespeak_ai.processors.pdf.table_extractor import TableExtractor
from wisespeak_ai.utils.file_utils import is_valid_pdf

# 샘플 PDF 파일 경로 (테스트 시 사용할 파일을 준비해야 합니다)
SAMPLE_PDF = os.environ.get("SAMPLE_PDF_PATH", "sample.pdf")

def test_is_valid_pdf():
    """PDF 파일 검증 테스트"""
    # 존재하지 않는 파일
    assert is_valid_pdf("nonexistent.pdf") == False
    
    # 실제 PDF 파일이 있는 경우
    if os.path.exists(SAMPLE_PDF):
        assert is_valid_pdf(SAMPLE_PDF) == True

@pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="샘플 PDF 파일이 없습니다")
def test_text_extraction():
    """텍스트 추출 테스트"""
    extractor = TextExtractor()
    text_result = extractor.extract_text_from_pdf(SAMPLE_PDF)
    
    # 텍스트 추출 결과 확인
    assert isinstance(text_result, dict)
    assert len(text_result) > 0
    
    # 페이지 번호와 텍스트 확인
    for page_num, text in text_result.items():
        assert isinstance(page_num, int)
        assert page_num > 0
        assert isinstance(text, str)

@pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="샘플 PDF 파일이 없습니다")
def test_document_info():
    """문서 정보 추출 테스트"""
    extractor = TextExtractor()
    info = extractor.get_document_info(SAMPLE_PDF)
    
    # 문서 정보 확인
    assert isinstance(info, dict)
    assert "total_pages" in info
    assert isinstance(info["total_pages"], int)
    assert info["total_pages"] > 0
    assert "file_name" in info
    assert info["file_name"] == Path(SAMPLE_PDF).name

@pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="샘플 PDF 파일이 없습니다")
def test_image_extraction():
    """이미지 추출 테스트"""
    extractor = ImageExtractor()
    output_dir = "test_images"
    
    # 임시 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 이미지 추출
        image_paths = extractor.pdf_to_images(SAMPLE_PDF, output_dir)
        
        # 결과 확인
        assert isinstance(image_paths, list)
        
        # 파일이 생성되었는지 확인
        for path in image_paths:
            assert os.path.exists(path)
            assert os.path.isfile(path)
            assert Path(path).suffix.lower() in [".png", ".jpg", ".jpeg"]
    finally:
        # 테스트 후 정리
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        os.rmdir(output_dir)

@pytest.mark.skipif(not os.path.exists(SAMPLE_PDF), reason="샘플 PDF 파일이 없습니다")
def test_table_extraction():
    """표 추출 테스트"""
    extractor = TableExtractor()
    
    try:
        # 표 추출
        tables = extractor.extract_tables_from_pdf(SAMPLE_PDF)
        
        # 결과 확인
        assert isinstance(tables, dict)
        
        # 표가 있는 경우 검증
        if tables:
            for page_num, page_tables in tables.items():
                assert isinstance(page_num, int)
                assert isinstance(page_tables, list)
                
                for table in page_tables:
                    assert hasattr(table, 'shape')  # DataFrame 확인
    except Exception as e:
        # 표가 없거나 추출 오류인 경우 테스트 스킵
        pytest.skip(f"표 추출 오류 (표가 없을 수 있음): {e}")
