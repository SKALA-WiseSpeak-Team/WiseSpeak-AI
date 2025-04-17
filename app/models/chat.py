from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# 챗봇 질의 요청 스키마
class ChatRequest(BaseModel):
    lecture_id: str
    query: str
    language: str
    voice_style:str

# 챗봇 응답 스키마
class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[int]] = None  # 참조된 페이지 번호
