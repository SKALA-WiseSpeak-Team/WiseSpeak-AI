from openai import OpenAI
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OpenAIService:
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def generate_text_to_speech(text: str, voice_type: str = "alloy") -> bytes:
        """텍스트를 음성으로 변환"""
        # 음성 타입에 따른 OpenAI 음성 선택
        voice_map = {
            "female_adult": "nova",
            "male_adult": "onyx",
            "female_young": "alloy",
            "male_young": "echo",
        }
        
        voice = voice_map.get(voice_type, "alloy")
        
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        )
        
        # 바이너리 데이터 반환
        return response.content
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def generate_embedding(text: str):
        """텍스트의 임베딩 생성"""
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def chat_completion(system_prompt: str, user_prompt: str, context: str = ""):
        """GPT를 사용한 챗봇 응답 생성"""
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if context:
            messages.append({"role": "user", "content": f"컨텍스트: {context}"})
        
        messages.append({"role": "user", "content": user_prompt})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
