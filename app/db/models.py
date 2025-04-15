from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid

# 강의 모델
class Lecture(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    pdf_url: str
    total_pages: int
    language: str = "ko"

# 페이지 모델
class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lecture_id: str
    page_number: int
    content: Optional[str] = None
    audio_url: Optional[str] = None

# 챗봇 대화 모델
class ChatMessage(BaseModel):
    lecture_id: str
    query: str
    response: Optional[str] = None
    sources: Optional[List[int]] = None
