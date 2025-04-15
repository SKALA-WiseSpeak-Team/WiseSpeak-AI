from typing import List, Dict, Any
import re
from app.db.session import supabase
from app.services.openai_service import OpenAIService

class RAGService:
    @staticmethod
    async def find_relevant_context(lecture_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
        """질문과 관련된 페이지 찾기 (MVP에서는 단순 키워드 매칭 사용)"""
        # 강의의 모든 페이지 가져오기
        pages = supabase.table("pages") \
            .select("id, page_number, content") \
            .eq("lecture_id", lecture_id) \
            .execute()
        
        pages_data = pages.data
        
        if not pages_data:
            return {
                "context": "",
                "sources": []
            }
        
        # MVP에서는 단순 키워드 매칭으로 관련 페이지 찾기
        # 실제 시스템에서는 임베딩과 벡터 검색 사용
        query_keywords = re.sub(r'[^\w\s]', '', query.lower()).split()
        
        relevance_scores = []
        for page in pages_data:
            if not page["content"]:
                continue
                
            content_lower = page["content"].lower()
            score = sum(1 for keyword in query_keywords if keyword in content_lower)
            relevance_scores.append((page, score))
        
        # 관련성 점수로 정렬하고 상위 k개 선택
        relevance_scores.sort(key=lambda x: x[1], reverse=True)
        top_pages = relevance_scores[:top_k]
        
        # 결과에 페이지 번호만 없는 경우(모든 스코어가 0) 처리
        if not top_pages or all(score == 0 for _, score in top_pages):
            # 대안: 첫 페이지 포함
            context = pages_data[0]["content"] if pages_data[0]["content"] else ""
            sources = [pages_data[0]["page_number"]]
        else:
            # 관련 컨텍스트 구성
            context_parts = []
            sources = []
            
            for page, _ in top_pages:
                if page["content"] and _ > 0:  # 스코어가 0보다 큰 경우만 포함
                    context_parts.append(f"[페이지 {page['page_number']}] {page['content']}")
                    sources.append(page["page_number"])
            
            context = "\n\n".join(context_parts)
        
        return {
            "context": context,
            "sources": sources
        }
    
    @staticmethod
    async def generate_chat_response(lecture_id: str, query: str) -> Dict[str, Any]:
        """RAG를 사용한 챗봇 응답 생성"""
        # 강의 정보 가져오기
        lecture = supabase.table("lectures") \
            .select("title, language") \
            .eq("id", lecture_id) \
            .single() \
            .execute()
        
        lecture_data = lecture.data
        
        if not lecture_data:
            return {
                "response": "해당 강의를 찾을 수 없습니다.",
                "sources": []
            }
        
        # 관련 컨텍스트 찾기
        relevant_context = await RAGService.find_relevant_context(lecture_id, query)
        
        # 시스템 프롬프트 구성
        system_prompt = f"""당신은 '{lecture_data['title']}' 강의에 대한 질문에 답변하는 도우미입니다.
다음 규칙을 따르세요:
1. 제공된 컨텍스트 내에서만 답변하세요.
2. 컨텍스트에 없는 정보는 '제공된 자료에는 해당 정보가 없습니다.'라고 답변하세요.
3. 답변은 명확하고 간결하게 작성하세요.
4. 답변 마지막에 참고한 페이지 번호를 언급하지 마세요.
5. 강의 내용에 관련된 질문에만 답변하고, 부적절한 요청은 정중히 거절하세요."""
        
        # 챗봇 응답 생성
        response = await OpenAIService.chat_completion(
            system_prompt=system_prompt,
            user_prompt=query,
            context=relevant_context["context"]
        )
        
        return {
            "response": response,
            "sources": relevant_context["sources"]
        }
