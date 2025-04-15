import os
import uuid
import PyPDF2
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from app.db.session import supabase
from app.core.config import settings

class PDFService:
    @staticmethod
    async def extract_text_from_pdf(file: UploadFile) -> dict:
        """PDF 파일에서 텍스트를 추출하고 임시 저장"""
        temp_file_id = str(uuid.uuid4())
        
        # 파일을 임시로 저장
        suffix = Path(file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # PDF 파일 열기
            with open(tmp_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                # 각 페이지의 텍스트 추출
                pages_text = {}
                for i in range(total_pages):
                    page = pdf_reader.pages[i]
                    pages_text[i+1] = page.extract_text()
                
                # Supabase Storage에 PDF 업로드
                with open(tmp_path, 'rb') as f:
                    file_path = f"temp/{temp_file_id}{suffix}"
                    supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                        file_path, 
                        f.read()
                    )
                
                # 미리보기 URL 생성
                pdf_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
                
                return {
                    "temp_file_id": temp_file_id,
                    "filename": file.filename,
                    "total_pages": total_pages,
                    "pages_text": pages_text,
                    "preview_url": pdf_url
                }
        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)
    
    @staticmethod
    async def move_pdf_to_permanent(temp_file_id: str, lecture_id: str) -> str:
        """임시 저장된 PDF를 영구 저장소로 이동"""
        # 임시 파일 경로
        temp_files = supabase.storage.from_(settings.STORAGE_BUCKET).list("temp")
        file_path = None
        
        for file in temp_files:
            if file["name"].startswith(temp_file_id):
                file_path = f"temp/{file['name']}"
                break
        
        if not file_path:
            raise ValueError(f"임시 파일을 찾을 수 없습니다: {temp_file_id}")
        
        # 새 경로로 파일 복사
        suffix = Path(file_path).suffix
        new_path = f"lectures/{lecture_id}{suffix}"
        
        # 임시 파일 다운로드
        res = supabase.storage.from_(settings.STORAGE_BUCKET).download(file_path)
        
        # 새 경로에 업로드
        supabase.storage.from_(settings.STORAGE_BUCKET).upload(
            new_path,
            res
        )
        
        # 임시 파일 삭제
        supabase.storage.from_(settings.STORAGE_BUCKET).remove([file_path])
        
        # 영구 URL 반환
        return supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(new_path)
