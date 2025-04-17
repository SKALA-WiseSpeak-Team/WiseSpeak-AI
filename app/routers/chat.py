from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
router = APIRouter()
@router.post("/chat", response_model=ChatResponse)
async def chat_with_lecture(request: ChatRequest):
    """챗봇에 질문 전송 및 응답 수신"""
    try:
        # RAG 서비스를 사용하여 응답 생성
        response = await RAGService.generate_chat_response(
            lecture_id=request.lecture_id,
            query=request.query
        )
        return {
            "response": response["response"],
            "sources": response["sources"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 응답 생성 중 오류 발생: {str(e)}"
        )