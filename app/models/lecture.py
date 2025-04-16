from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# 강의 생성 요청 스키마
class LectureCreate(BaseModel):
    title: str
    description: Optional[str] = None
    pdf_url: str
    total_pages: int
    

# 강의 처리 요청 스키마
class LectureProcess(BaseModel):
    temp_file_id: str
    title: str
    description: Optional[str] = None
    pdf_url: str
    total_pages: int
    

# 강의 응답 스키마
class LectureResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    pdf_url: str
    total_pages: int

# 강의 목록 응답 스키마
class LecturesResponse(BaseModel):
    data: List[LectureResponse]
    total: int
    limit: int
    offset: int
