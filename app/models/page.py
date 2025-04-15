from typing import Optional
from pydantic import BaseModel

# 페이지 응답 스키마
class PageResponse(BaseModel):
    id: str
    lecture_id: str
    page_number: int
    content: Optional[str] = None
    audio_url: Optional[str] = None
