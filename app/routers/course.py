from fastapi import APIRouter, HTTPException, Query
from app.db.session import supabase
from app.services.voice_service import VoiceService
from app.models.course import CourseResponse
import pathlib
import uuid

router = APIRouter()

@router.get("/course/{id}", response_model=CourseResponse)
async def get_course(
    id: str,
    voice_style: str = Query(None, description="음성 스타일"),
    language: str = Query(None, description="언어")
):

  # TODO 강의 생성하는 llm 반환 결과 받아와서 반환해줘야 함
  # 반환 값: 스크립트 txt 파일, 음성 mp3 파일
  
  # 강의 정보 supabase에서 가져오기
  course_info = supabase.table("lectures").select("*").eq("id", id).single().execute()
  
  if not course_info.data:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")
  
  # 기존 데이터 중복 체크
  if voice_style and language:  # voice_style과 language가 모두 있는 경우에만 중복 체크
      existing_text = supabase.table("text") \
          .select("*") \
          .eq("lecture_id", id) \
          .eq("language", language) \
          .eq("voice_type", voice_style) \
          .execute()
      
      if existing_text.data:
          raise HTTPException(
              status_code=400,
              detail={
                  "message": "이미 해당 언어와 음성 타입으로 생성된 강의가 있습니다",
                  "existing_data": existing_text.data[0]
              }
          )
  
  # llm에서 강의에서 받은 audio 넘겨야함
  # 임시로 갖고 있는 mp3 파일 넣었음
  base_dir = pathlib.Path(__file__).resolve().parent.parent
  file_path = base_dir / "uploads" / "openai-tts-output.mp3"

  with open(file_path, "rb") as f:
    audio_file = f.read()
  
  # audio_file supabase에 업로드
  audio_info = await VoiceService.upload_voice(audio_file, id, voice_style, language)

  # llm에서 받은 강의 스크립트 넘겨야 함
  # 임시로 갖고 있는 txt 파일 넣었음
  text_file_path = base_dir / "uploads" / "test.txt"
  
  with open(text_file_path, "r", encoding="utf-8") as f:
    text_file = f.read()
    
  script_info = await VoiceService.upload_script(text_file, id, voice_style, language)
  
  pdf_url = course_info.data["pdf_url"]
  voice_file_url = audio_info["voice_url"]
  script_file_url = script_info["script_url"]
  
  script_data = {
    "id": str(uuid.uuid4()),
    "lecture_id": id,
    "language": language,
    "voice_type": voice_style,
    "txt_url": script_file_url,
    "mp3_url": voice_file_url
  }
  
  result = supabase.table("text").insert(script_data).execute()
  
  return CourseResponse(
    id=id,
    title=course_info.data["title"],
    description=course_info.data["description"],
    created_at=course_info.data["created_at"],
    pdf_url=pdf_url,
    total_pages=course_info.data["total_pages"],
    language=language,
    voice_url=voice_file_url
  )