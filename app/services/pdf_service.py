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
    async def upload_raw_pdf(file: UploadFile) -> dict:
        """PDF 파일을 Supabase Storage에 업로드하고 페이지 수 반환"""
        temp_file_id = str(uuid.uuid4())
        suffix = Path(file.filename).suffix

        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 페이지 수 추출
            with open(tmp_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)

            # Supabase Storage 업로드
            with open(tmp_path, 'rb') as f:
                file_path = f"temp/{temp_file_id}{suffix}"
                supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                    file_path,
                    f.read()
                )

            pdf_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)

            return {
                "temp_file_id": temp_file_id,
                "filename": file.filename,
                "total_pages": total_pages,
                "preview_url": pdf_url
            }
        finally:
            os.unlink(tmp_path)

