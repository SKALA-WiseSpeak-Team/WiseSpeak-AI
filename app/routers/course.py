from fastapi import APIRouter, HTTPException, Query
from app.db.session import supabase
import pathlib
import uuid
import os
from fastapi import UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile
import aiohttp
from io import BytesIO
from tempfile import NamedTemporaryFile
from app.services.voice_service import VoiceService
from app.models.course import CourseResponse
from app.services.lecture_service import LectureService
from tempfile import SpooledTemporaryFile

router = APIRouter()

@router.get("/course/{id}", response_model=CourseResponse)
async def get_course(
    id: str,
    voice_style: str = Query(None, description="음성 스타일"),
    language: str = Query(None, description="언어")
):
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
      
      if existing_text.data and len(existing_text.data) > 0:
          return CourseResponse(
                  id=id,
                  title=course_info.data["title"],
                  description=course_info.data["description"],
                  created_at=course_info.data["created_at"],
                  pdf_url=course_info.data["pdf_url"],
                  total_pages=course_info.data["total_pages"],
                  language=language,
                  voice_url=existing_text.data[0]["mp3_url"],
                  namespace=existing_text.data[0]["namespace"]
                )
  
  # pdf url에서 pdf 읽어오기
  raw_pdf = await get_uploadfile_from_url(course_info.data["pdf_url"])
  
  suffix = ".pdf"
  
  with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_pdf:
      content = await raw_pdf.read()
      tmp_pdf.write(content)
      tmp_path_pdf = tmp_pdf.name
  
  # llm에서 pdf 처리
  lecture_service = LectureService()
  llm_result = lecture_service.process_pdf(pdf_path = tmp_path_pdf, language = language, voice=voice_style)
  
  script_text = llm_result["script_text"]
  
  # script supabase에 업로드
  script_info = await VoiceService.upload_script(script_text, id, voice_style, language)
  
  audio_path = llm_result["audio_path"]
  
  with open(audio_path, "rb") as f:
    audio_file = f.read()
  
  # audio_file supabase에 업로드
  audio_info = await VoiceService.upload_voice(audio_file, id, voice_style, language)
  
  # 저장한 audio_path에 있는 파일 삭제
  print(audio_path)
  
  pdf_url = course_info.data["pdf_url"]
  voice_file_url = audio_info["voice_url"]
  script_file_url = script_info["script_url"]
  
  script_data = {
    "id": str(uuid.uuid4()),
    "lecture_id": id,
    "language": language,
    "voice_type": voice_style,
    "txt_url": script_file_url,
    "mp3_url": voice_file_url,
    "namespace": llm_result["namespace"]
  }
  
  result = supabase.table("text").insert(script_data).execute()
  
  os.unlink(tmp_path_pdf)
  
  return CourseResponse(
    id=id,
    title=course_info.data["title"],
    description=course_info.data["description"],
    created_at=course_info.data["created_at"],
    pdf_url=pdf_url,
    total_pages=course_info.data["total_pages"],
    language=language,
    voice_url=voice_file_url,
    namespace=llm_result["namespace"]
  )


async def get_uploadfile_from_url(pdf_url: str) -> StarletteUploadFile:
    async with aiohttp.ClientSession() as session:
        async with session.get(pdf_url) as resp:
            if resp.status == 200:
                content = await resp.read()
                filename = pdf_url.split("/")[-1] or "temp.pdf"

                # SpooledTemporaryFile에 content 저장
                spooled_file = SpooledTemporaryFile()
                spooled_file.write(content)
                spooled_file.seek(0)

                # content_type은 여기서만 지정 가능
                upload_file = StarletteUploadFile(filename=filename, file=spooled_file)
                return upload_file
            else:
                raise Exception(f"파일을 다운로드할 수 없습니다. 상태 코드: {resp.status}")

