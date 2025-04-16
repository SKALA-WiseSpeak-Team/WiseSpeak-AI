from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.db.session import supabase
from app.models.lecture import LectureResponse, LecturesResponse, LectureCreate
from app.models.page import PageResponse
import json

router = APIRouter()

@router.get("/lectures", response_model=LecturesResponse)
async def get_lectures(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None
):
    """모든 강의 목록 조회"""
    query = supabase.table("lectures").select("*")
    
    # 검색어 필터링
    if search:
        query = query.ilike("title", f"%{search}%")
    
    # 총 개수 조회 (필터링 적용)
    count_query = query
    count_result = count_query.execute()
    total = len(count_result.data)
    
    # 페이지네이션 적용
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    
    return {
        "data": result.data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/lectures/{lecture_id}", response_model=LectureResponse)
async def get_lecture(
    lecture_id: str = Path(..., description="강의 ID")
):
    """특정 강의 상세 정보 조회"""
    result = supabase.table("lectures").select("*").eq("id", lecture_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")
    
    return result.data

@router.post("/lectures", response_model=LectureResponse)
async def create_lecture(
    lecture: LectureCreate
):
    """새로운 강의 생성"""
    from uuid import uuid4
    json_data = {
        "id": str(uuid4()),
        "title": lecture.title,
        "description": lecture.description,
        "pdf_url": lecture.pdf_url,
        "total_pages": lecture.total_pages
    }

    result = supabase.table("lectures").insert(json_data).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="강의 생성에 실패했습니다")

    return result.data[0]



@router.get("/lectures/{lecture_id}/pages/{page_number}", response_model=PageResponse)
async def get_lecture_page(
    lecture_id: str = Path(..., description="강의 ID"),
    page_number: int = Path(..., description="페이지 번호", ge=1)
):
    """특정 강의의 특정 페이지 정보 조회"""
    result = supabase.table("pages") \
        .select("*") \
        .eq("lecture_id", lecture_id) \
        .eq("page_number", page_number) \
        .single() \
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")
    
    return result.data

@router.get("/lectures/{lecture_id}/pages", response_model=List[PageResponse])
async def get_lecture_pages(
    lecture_id: str = Path(..., description="강의 ID")
):
    """특정 강의의 모든 페이지 정보 조회"""
    result = supabase.table("pages") \
        .select("*") \
        .eq("lecture_id", lecture_id) \
        .order("page_number", desc=False) \
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="페이지를 찾을 수 없습니다")
    
    return result.data