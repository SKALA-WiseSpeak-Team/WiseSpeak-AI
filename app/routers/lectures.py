from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from app.db.session import supabase
from app.models.lecture import LectureResponse, LecturesResponse
import os
import uuid
from PyPDF2 import PdfReader
import io
import logging

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/lectures", response_model=LecturesResponse)
async def get_lectures(request: Request):
    """모든 강의 목록 조회"""
    try:
        # 클라이언트 정보 로깅
        client_ip = request.client.host
        logger.info(f"클라이언트 접속 - IP: {client_ip}")
        
        query = supabase.table("lectures").select("*")
        result = query.execute()
        
        return {
            "data": result.data
        }
        
    except Exception as e:
        # 클라이언트 IP와 함께 에러 로깅
        client_ip = request.client.host
        error_msg = f"강의 목록 조회 중 오류 발생 - 클라이언트 IP: {client_ip}, 에러: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "강의 목록을 불러오는 중 오류가 발생했습니다",
                "error": str(e),
                "client_ip": client_ip
            }
        )

@router.post("/lectures", response_model=LectureResponse)
def create_lecture(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None)
):
    """새로운 강의 생성"""
    try:
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")
        
        # PDF 파일 읽기
        file_content = file.file.read()
        
        # PDF 페이지 수 계산
        pdf_reader = PdfReader(io.BytesIO(file_content))
        total_pages = len(pdf_reader.pages)
        
        # PDF 파일 저장을 위한 고유 ID 생성
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_name = f"{file_id}{file_extension}"
        
        # Storage에 파일 업로드
        storage_path = f"lectures/{file_name}"
        storage_response = supabase.storage.from_("wisespeak").upload(
            storage_path,
            file_content,
            {"content-type": "application/pdf"}
        )
        
        if not storage_response:
            raise HTTPException(status_code=400, detail="PDF 파일 업로드에 실패했습니다")
        
        # 업로드된 파일의 공개 URL 가져오기
        pdf_url = supabase.storage.from_("wisespeak").get_public_url(storage_path)
        
        # 강의 데이터 생성
        lecture_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "pdf_url": pdf_url,
            "total_pages": total_pages
        }

        # 강의 데이터 저장
        result = supabase.table("lectures").insert(lecture_data).execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="강의 생성에 실패했습니다")

        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 파일 핸들러 닫기
        file.file.close()