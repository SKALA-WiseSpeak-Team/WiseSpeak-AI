from fastapi import FastAPI

# routers 디렉토리에서 정의한 라우터 import
# from routers import upload


app = FastAPI()

# 테스트를 위한 라우터 -> 나중에 삭제
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI server!"}

@app.get("/hello")
async def hello():
    return {"message": "hello world!"}


# routers 디렉토리에서 정의한 라우터 사용
# app.include_router(upload.router)


# CORS settings
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)