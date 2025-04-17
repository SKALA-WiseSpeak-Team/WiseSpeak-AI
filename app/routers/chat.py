from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.services.rag_service import RAGService
from datetime import datetime

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_lecture(
    request: ChatRequest
):
    """챗봇에 질문 전송 및 응답 수신"""
    try:
        # 대화 기록 초기화 또는 업데이트
        history = request.history or []
        
        # 사용자 메시지 추가
        user_message = ChatMessage(
            role="user",
            content=request.query,
            timestamp=datetime.now()
        )
        history.append(user_message)
        
        # RAG 서비스를 사용하여 응답 생성
        response = await RAGService.generate_chat_response(
            lecture_id=request.lecture_id,
            query=request.query,
            history=history
        )
        
        # AI 응답 메시지 추가
        ai_message = ChatMessage(
            role="assistant",
            content=response["response"],
            timestamp=datetime.now()
        )
        history.append(ai_message)
        
        return {
            "response": response["response"],
            "sources": response["sources"],
            "history": history
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 응답 생성 중 오류 발생: {str(e)}"
        )
