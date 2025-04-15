import uuid
from app.db.session import supabase
from app.core.config import settings
from app.services.openai_service import OpenAIService

class AudioService:
    @staticmethod
    async def generate_audio_for_text(text: str, lecture_id: str, page_number: int, voice_type: str = "female_adult") -> str:
        """텍스트에서 오디오 생성 및 저장"""
        # 빈 텍스트 처리
        if not text or text.strip() == "":
            return None
        
        # OpenAI TTS로 오디오 생성
        audio_content = await OpenAIService.generate_text_to_speech(text, voice_type)
        
        # 파일 이름 및 경로 생성
        file_name = f"{lecture_id}_page_{page_number}.mp3"
        file_path = f"audio/{file_name}"
        
        # Supabase Storage에 업로드
        supabase.storage.from_(settings.STORAGE_BUCKET).upload(
            file_path,
            audio_content
        )
        
        # 공개 URL 반환
        return supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
