from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# 강의 응답 스키마
class CourseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    pdf_url: str
    voice_url: str
    total_pages: int