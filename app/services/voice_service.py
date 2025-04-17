import os
from fastapi import UploadFile
from tempfile import NamedTemporaryFile
from pathlib import Path
from app.db.session import supabase
from app.core.config import settings

class VoiceService:
    @staticmethod
    async def upload_script(text: bytes, course_id: str, voice_style: str, language: str) -> dict:
        """txt 파일을 Supabase Storage에 업로드하고 링크 반환"""
        # 파일명 구성
        suffix = ".txt"
        file_name = f"{course_id}_{language}_{voice_style}{suffix}"
        file_path = f"scripts/{file_name}"
        
        # 임시 파일 저장
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(text.encode("utf-8"))
            tmp_path = tmp.name
        
        try:
            # Supabase Storage에 업로드
            try:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    content = f.read().encode("utf-8")  # 문자열 → 바이트

                supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                    file_path,
                    content,
                    {"content-type": "text/plain"}
                )

            except Exception as e:
                if "Duplicate" in str(e):
                    # 이미 파일이 존재하면 기존 URL 반환
                    script_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
                    return {
                        "script_file_name": file_name,
                        "script_url": script_url
                    }
                else:
                    raise  # 다른 오류는 다시 발생시키기

            
            # URL 생성
            script_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)

            return {
                "script_file_name": file_name,
                "script_url": script_url
            }
        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)
    
    @staticmethod
    async def upload_voice(audio: UploadFile, course_id: str, voice_style: str, language: str) -> dict:
        """Audio 파일을 Supabase Storage에 업로드하고 링크 반환"""
        # 파일명 구성
        suffix = ".mp3"
        file_name = f"{course_id}_{language}_{voice_style}{suffix}"
        file_path = f"voices/{file_name}"
        
        # 임시 파일 저장
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = audio
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Supabase Storage에 업로드
            try:
                with open(tmp_path, "rb") as f:
                    supabase.storage.from_(settings.STORAGE_BUCKET).upload(
                        file_path,
                        f.read(),
                        {"content-type": "audio/mpeg"}
                    )
            except Exception as e:
                if e.args[0]["error"] == "Duplicate":
                    # 이미 파일이 존재하면 기존 URL 반환
                    voice_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
                    return {
                        "voice_file_name": file_name,
                        "voice_url": voice_url
                    }
                else:
                    raise  # 다른 오류는 다시 발생시키기

            
            # URL 생성
            voice_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)

            return {
                "voice_file_name": file_name,
                "voice_url": voice_url
            }
        finally:
            # 임시 파일 삭제
            os.unlink(tmp_path)
