from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.db.session import supabase
from app.services.voice_service import VoiceService
from app.models.course import CourseResponse
from app.core.config import settings
import pathlib

router = APIRouter()

@router.get("/api/course/{id}", response_model=CourseResponse)
async def get_course(
    id: str,
    voice_style: str = Query(None, description="음성 스타일"),
    language: str = Query(None, description="언어")
):

  # TODO 강의 생성하는 llm 반환 결과 받아와서 반환해줘야 함
  # 강의 정보 supabase에서 가져오기
  course_info = supabase.table("lectures").select("*").eq("id", id).single().execute()
  
  if not course_info.data:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")
  
  # llm에서 강의 오디오 파일 반환
  base_dir = pathlib.Path(__file__).resolve().parent.parent
  file_path = base_dir / "uploads" / "openai-tts-output.mp3"

  with open(file_path, "rb") as f:
    audio_file = f.read()
  
  # audio_file supabase에 업로드
  audio_info = await VoiceService.upload_voice(audio_file, id, voice_style, language)
  
  pdf_url = course_info.data["pdf_url"]
  voice_file_url = audio_info["voice_url"]
  
  result = {
      "id": id,
      "title": course_info.data["title"],
      "description": course_info.data["description"],
      "created_at" : course_info.data["created_at"],
      "pdf_url": pdf_url,
      "voice_url": voice_file_url
  }
  
  return result