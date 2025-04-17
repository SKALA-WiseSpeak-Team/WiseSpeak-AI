from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.lecture_rag_service import LectureRAGSystem
from app.db.session import supabase


router = APIRouter()
@router.post("/chat", response_model=ChatResponse)
async def chat_with_lecture(request: ChatRequest):
    """챗봇에 질문 전송 및 응답 수신"""

    # 강의 정보 supabase에서 가져오기
    course_info = supabase.table("text").select("*").eq("lecture_id", request.lecture_id).eq("language", request.language).eq("voice_type", request.voice_style).execute()
    
    if course_info.data and len(course_info.data) <= 0:
            raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")
    
    try:
        # RAG 서비스를 사용하여 응답 생성
        # llm에서 pdf 처리
        rag_service = LectureRAGSystem()
        response = rag_service.process_audio_query(
            audio_data=request.query,
            namespace=course_info.data[0]["namespace"],
            language=request.language
        )
        
        # 생성 텍스트 반환
        return {
            "chat_answer": response["answer"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 응답 생성 중 오류 발생: {str(e)}"
        )