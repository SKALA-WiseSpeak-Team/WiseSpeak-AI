"""
PDF 추출 기능 예제
"""
import os
import argparse
from pathlib import Path

from wisespeak_ai.processors.pdf.text_extractor import TextExtractor
from wisespeak_ai.processors.pdf.image_extractor import ImageExtractor
from wisespeak_ai.processors.pdf.table_extractor import TableExtractor
from wisespeak_ai.processors.pdf.ocr_processor import OCRProcessor
from wisespeak_ai.utils.logger import get_logger

logger = get_logger(__name__)

def extract_pdf_content(pdf_path, output_dir=None):
    """PDF 파일에서 다양한 컨텐츠 추출 예제
    
    Args:
        pdf_path (str): PDF 파일 경로
        output_dir (str, optional): 출력 디렉토리. 기본값은 현재 디렉토리의 'output'
    """
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path("output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 텍스트 추출
    logger.info("1. 텍스트 추출 시작")
    text_extractor = TextExtractor()
    extracted_text = text_extractor.extract_text_from_pdf(pdf_path)
    
    # 결과 출력
    text_output_path = Path(output_dir) / "extracted_text.txt"
    with open(text_output_path, "w", encoding="utf-8") as f:
        for page_num, text in sorted(extracted_text.items()):
            f.write(f"=== 페이지 {page_num} ===\n")
            f.write(text)
            f.write("\n\n")
    
    logger.info(f"텍스트 추출 결과 저장: {text_output_path}")
    
    # 이미지 추출
    logger.info("2. 이미지 추출 시작")
    image_extractor = ImageExtractor()
    images_output_dir = Path(output_dir) / "images"
    os.makedirs(images_output_dir, exist_ok=True)
    
    image_paths = image_extractor.pdf_to_images(pdf_path, str(images_output_dir))
    logger.info(f"이미지 {len(image_paths)}개 추출 완료: {images_output_dir}")
    
    # OCR 처리
    logger.info("3. OCR 처리 시작")
    ocr_processor = OCRProcessor()
    ocr_results = {}
    
    for i, image_path in enumerate(image_paths[:3]):  # 처리 시간 단축을 위해 처음 3개만 처리
        logger.info(f"이미지 {i+1}/{len(image_paths[:3])} OCR 처리 중...")
        ocr_text = ocr_processor.extract_text_from_image(image_path)
        ocr_results[f"page_{i+1}"] = ocr_text
    
    ocr_output_path = Path(output_dir) / "ocr_results.txt"
    with open(ocr_output_path, "w", encoding="utf-8") as f:
        for page_name, text in ocr_results.items():
            f.write(f"=== {page_name} ===\n")
            f.write(text)
            f.write("\n\n")
    
    logger.info(f"OCR 결과 저장: {ocr_output_path}")
    
    # 표 추출
    logger.info("4. 표 추출 시작")
    table_extractor = TableExtractor()
    table_output_dir = Path(output_dir) / "tables"
    os.makedirs(table_output_dir, exist_ok=True)
    
    try:
        extracted_tables = table_extractor.extract_tables_from_pdf(pdf_path)
        csv_paths = table_extractor.tables_to_csv(extracted_tables, str(table_output_dir))
        
        num_tables = sum(len(tables) for tables in csv_paths.values())
        logger.info(f"표 {num_tables}개 추출 완료: {table_output_dir}")
    except Exception as e:
        logger.error(f"표 추출 중 오류 발생: {e}")
    
    logger.info("PDF 추출 작업 완료")
    return {
        "text": extracted_text,
        "images": image_paths,
        "ocr": ocr_results,
        "tables": extracted_tables if "extracted_tables" in locals() else {}
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF 컨텐츠 추출 예제")
    parser.add_argument("pdf_path", help="PDF 파일 경로")
    parser.add_argument("--output", "-o", help="출력 디렉토리", default="output")
    
    args = parser.parse_args()
    
    extract_pdf_content(args.pdf_path, args.output)
