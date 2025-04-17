from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import lectures, chat, course
from pydantic import AnyHttpUrl
import json

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 설정 완전히 개방
origins = [
    "http://127.0.0.1:5173",  # 대체 로컬 프론트엔드
    "*",  # 모든 오리진 허용 (개발 환경에서만 사용)
]

# CORS 설정 개선
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# API 라우터 설정
app.include_router(lectures.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(course.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "WiseSpeak API"}