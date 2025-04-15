from typing import Optional
from pydantic import BaseModel

# 파일 업로드 응답 스키마
class UploadResponse(BaseModel):
    temp_file_id: str
    filename: str
    total_pages: int
    preview_url: Optional[str] = None

# 처리 응답 스키마
class ProcessResponse(BaseModel):
    lecture_id: str
    job_id: str
    status: str = "processing"
