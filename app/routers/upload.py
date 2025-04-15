import uuid
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from app.db.session import supabase
from app.models.upload import UploadResponse, ProcessResponse
from app.services.pdf_service import PDFService
from app.services.audio_service import AudioService

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """PDF 파일 업로드 및 텍스트 추출"""
    # 파일 확장자 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")
    
    # PDF 파일 처리
    result = await PDFService.extract_text_from_pdf(file)
    
    return {
        "temp_file_id": result["temp_file_id"],
        "filename": result["filename"],
        "total_pages": result["total_pages"],
        "preview_url": result["preview_url"]
    }

async def process_lecture_task(
    temp_file_id: str,
    title: str,
    description: str,
    language: str,
    voice_type: str,
    pages_text: dict,
    total_pages: int
):
    """백그라운드 작업: 강의 처리 및 오디오 생성"""
    try:
        # 새 강의 레코드 생성
        lecture_id = str(uuid.uuid4())
        
        # PDF 파일을 영구 저장소로 이동
        pdf_url = await PDFService.move_pdf_to_permanent(temp_file_id, lecture_id)
        
        # 강의 데이터 저장
        supabase.table("lectures").insert({
            "id": lecture_id,
            "title": title,
            "description": description,
            "language": language,
            "pdf_url": pdf_url,
            "total_pages": total_pages,
            "voice_type": voice_type
        }).execute()
        
        # 각 페이지 처리 및 오디오 생성
        for page_num, text in pages_text.items():
            # 텍스트가 있는 경우만 오디오 생성
            audio_url = None
            if text and text.strip():
                audio_url = await AudioService.generate_audio_for_text(
                    text, 
                    lecture_id, 
                    int(page_num),
                    voice_type
                )
            
            # 페이지 데이터 저장
            supabase.table("pages").insert({
                "id": str(uuid.uuid4()),
                "lecture_id": lecture_id,
                "page_number": int(page_num),
                "content": text,
                "audio_url": audio_url
            }).execute()
    
    except Exception as e:
        # 에러 로깅 (실제 구현에서는 로깅 시스템 사용)
        print(f"강의 처리 중 오류 발생: {str(e)}")
        # 실패 상태 업데이트 (실제 구현에서는 작업 상태 테이블 사용)

@router.post("/process", response_model=ProcessResponse)
async def process_lecture(
    background_tasks: BackgroundTasks,
    temp_file_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    language: str = Form("ko"),
    voice_type: str = Form("female_adult")
):
    """PDF 처리 및 강의 생성 시작"""
    # 임시 저장된 PDF 정보 조회 (실제로는 DB 또는 캐시에서 가져와야 함)
    # MVP에서는 다시 PDF 처리를 수행
    
    # 기존에 추출한 파일 찾기 (간단한 구현)
    temp_files = supabase.storage.from_("wisespeak").list("temp")
    file_path = None
    
    for file in temp_files:
        if file["name"].startswith(temp_file_id):
            file_path = f"temp/{file['name']}"
            break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="임시 파일을 찾을 수 없습니다")
    
    # 파일 다운로드
    pdf_content = supabase.storage.from_("wisespeak").download(file_path)
    
    # PDF 텍스트 추출 (실제 구현에서는 캐시된 결과 사용)
    import PyPDF2
    import io
    
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    total_pages = len(pdf_reader.pages)
    
    pages_text = {}
    for i in range(total_pages):
        page = pdf_reader.pages[i]
        pages_text[i+1] = page.extract_text()
    
    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    lecture_id = str(uuid.uuid4())
    
    # 백그라운드 작업 시작
    background_tasks.add_task(
        process_lecture_task,
        temp_file_id,
        title,
        description,
        language,
        voice_type,
        pages_text,
        total_pages
    )
    
    return {
        "lecture_id": lecture_id,
        "job_id": job_id,
        "status": "processing"
    }
