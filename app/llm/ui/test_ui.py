"""
SRAGA AI 테스트 UI
"""
import os
import sys
import json
import tempfile
import time
import uuid
import datetime
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from typing import Dict, List, Any, Optional, Union

# 상위 디렉토리 추가하여 wisespeak_ai 모듈 임포트 가능하게 함
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# wisespeak_ai 임포트
from wisespeak_ai.processors.pdf.text_extractor import TextExtractor
from wisespeak_ai.processors.pdf.image_extractor import ImageExtractor
from wisespeak_ai.processors.pdf.table_extractor import TableExtractor
from wisespeak_ai.processors.document.document_chunker import DocumentChunker
from wisespeak_ai.embeddings.embedding_pipeline import EmbeddingPipeline
from wisespeak_ai.rag.rag_engine import RAGEngine
from wisespeak_ai.agents.lecture_agent import LectureAgent
from wisespeak_ai.agents.qa_agent import QAAgent
from wisespeak_ai.services.vector_db import VectorDBService
from wisespeak_ai.services.speech.tts_service import TTSService
from wisespeak_ai.services.speech.stt_service import STTService
from wisespeak_ai.utils.logger import get_logger
from wisespeak_ai.config import config

# 로깅 설정
logger = get_logger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="SRAGA AI 테스트 UI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 추가
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1E3A8A;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #2563EB;
    }
    .info-box {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #ECFDF5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #10B981;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFFBEB;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #F59E0B;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #FEE2E2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #EF4444;
        margin-bottom: 1rem;
    }
    .log-container {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #E5E7EB;
        border-radius: 0.5rem;
        padding: 0.5rem;
        background-color: #F9FAFB;
        font-family: monospace;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6B7280;
    }
    .tab-content {
        padding: 1rem;
        border: 1px solid #E5E7EB;
        border-radius: 0.5rem;
        background-color: #FFFFFF;
        margin-top: 0.5rem;
    }
    .speech-button {
        background-color: #2563EB;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        width: 100%;
    }
    .record-pulse {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(220, 38, 38, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(220, 38, 38, 0);
        }
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화"""
    if "pdf_path" not in st.session_state:
        st.session_state.pdf_path = None
    if "extracted_text" not in st.session_state:
        st.session_state.extracted_text = {}
    if "document_id" not in st.session_state:
        st.session_state.document_id = None
    if "collection_name" not in st.session_state:
        st.session_state.collection_name = None
    if "chunked_document" not in st.session_state:
        st.session_state.chunked_document = {"chunks": []}
    if "lecture_data" not in st.session_state:
        st.session_state.lecture_data = {}
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = bool(os.environ.get("OPENAI_API_KEY", ""))
    if "tab_selection" not in st.session_state:
        st.session_state.tab_selection = "시작 화면"
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    if "vector_db" not in st.session_state:
        st.session_state.vector_db = None
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = None
    if "lecture_agent" not in st.session_state:
        st.session_state.lecture_agent = None
    if "qa_agent" not in st.session_state:
        st.session_state.qa_agent = None
    if "audio_paths" not in st.session_state:
        st.session_state.audio_paths = {}
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    if "prompt_templates" not in st.session_state:
        st.session_state.prompt_templates = {
            "qa": {
                "system": "당신은 학습 자료에 대한 질의응답을 도와주는 챗봇입니다. "
                       "주어진 컨텍스트를 바탕으로 사용자의 질문에 정확하게 답변하세요. "
                       "컨텍스트에 없는 내용은 '제공된 자료에서 해당 정보를 찾을 수 없습니다'라고 답변하세요. "
                       "답변은 친절하고 도움이 되도록 작성하세요.",
                "user": "컨텍스트:\
{context}\
\
사용자: {question}\
\
어시스턴트:"
            },
            "lecture": {
                "system": "당신은 교육 콘텐츠 전문가입니다. 주어진 텍스트를 바탕으로 강의 스크립트를 생성하세요. "
                       "스크립트는 교육적이고, 명확하며, 학습자가 이해하기 쉽게 작성하세요. "
                       "원본 텍스트의 중요한 내용은 모두 포함하되, 더 자세한 설명과 예시를 추가하세요.",
                "user": "페이지 내용:\
{page_content}\
\
이 내용을 바탕으로 강의 스크립트를 생성해주세요."
            }
        }
    if "chunking_config" not in st.session_state:
        st.session_state.chunking_config = {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "chunking_strategy": "sentence"
        }
    if "embedding_config" not in st.session_state:
        st.session_state.embedding_config = {
            "model": "text-embedding-3-small",
            "batch_size": 10
        }
    if "test_results" not in st.session_state:
        st.session_state.test_results = {
            "rag_tests": [],
            "tts_tests": [],
            "stt_tests": [],
            "qa_tests": []
        }
    if "processing_times" not in st.session_state:
        st.session_state.processing_times = {
            "extraction": [],
            "chunking": [],
            "embedding": [],
            "rag_query": [],
            "qa_response": [],
            "lecture_generation": []
        }

# 로깅 메시지 추가
def add_log(message: str, level: str = "info"):
    """로그 메시지 추가
    
    Args:
        message (str): 로그 메시지
        level (str, optional): 로그 레벨 (info, warning, error, debug)
    """
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.log_messages.append({
        "timestamp": timestamp, 
        "message": message, 
        "level": level
    })
    
    # 실제 로깅도 수행
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.debug(message)

# API 키 설정
def set_api_key():
    """API 키 설정"""
    api_key = st.sidebar.text_input("OpenAI API 키", type="password")
    if st.sidebar.button("API 키 설정"):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state.api_key_set = True
            add_log("OpenAI API 키가 설정되었습니다")
            st.sidebar.success("API 키가 설정되었습니다!")
        else:
            st.sidebar.error("API 키를 입력해주세요")

# 타임스탬프 생성
def get_timestamp():
    """현재 시간 타임스탬프 생성"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 측정 시간 추가
def add_timing(category: str, duration: float):
    """처리 시간 기록
    
    Args:
        category (str): 측정 카테고리
        duration (float): 소요 시간(초)
    """
    if category in st.session_state.processing_times:
        st.session_state.processing_times[category].append({
            "timestamp": time.time(),
            "duration": duration
        })
        if st.session_state.debug_mode:
            add_log(f"{category} 작업 소요 시간: {duration:.2f}초", "debug")

# 시작 화면
def show_start_screen():
    """시작 화면 표시"""
    st.markdown('<div class="main-header">SRAGA AI 테스트 UI</div>', unsafe_allow_html=True)
    
    # 프로젝트 정보
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    **SRAGA AI**는 PDF 문서를 기반으로 강의 생성 및 챗봇 서비스를 제공하는 RAG(Retrieval-Augmented Generation) 시스템입니다.
    
    이 테스트 UI는 SRAGA AI의 모든 기능을 테스트하고 개발하기 위한 인터페이스를 제공합니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 기능 개요
    st.markdown('<div class="sub-header">테스트 기능 목록</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**문서 처리**")
        st.markdown("""
        - PDF 텍스트 추출 및 분석
        - 문서 청크화 및 임베딩
        - 벡터 DB 저장 및 검색
        """)
        
        st.markdown("**강의 생성**")
        st.markdown("""
        - 강의 스크립트 생성
        - 음성 변환 (TTS)
        - 다국어 지원
        """)
    
    with col2:
        st.markdown("**질의응답**")
        st.markdown("""
        - 문서 기반 질의응답
        - 음성 질의응답 (STT+TTS)
        - 대화 이력 관리
        """)
        
        st.markdown("**개발 도구**")
        st.markdown("""
        - 프롬프트 템플릿 관리
        - 청킹 및 임베딩 설정
        - 성능 분석 및 로깅
        """)
    
    # 시작하기
    st.markdown('<div class="sub-header">시작하기</div>', unsafe_allow_html=True)
    
    # 기본 워크플로우 안내
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.markdown("""
    **기본 워크플로우:**
    1. 사이드바에서 OpenAI API 키를 설정합니다.
    2. PDF 파일을 업로드하고 텍스트를 추출합니다.
    3. 문서를 청크화하고 임베딩합니다.
    4. 강의 생성이나 질의응답 기능을 테스트합니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 바로가기 버튼들
    st.markdown("**바로가기:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 PDF 업로드", key="goto_pdf_upload", help="PDF 파일 업로드 및 처리"):
            st.session_state.tab_selection = "PDF 업로드"
            st.experimental_rerun()
    
    with col2:
        if st.button("🔍 챗봇 테스트", key="goto_chatbot", help="질의응답 테스트"):
            st.session_state.tab_selection = "질의응답 테스트"
            st.experimental_rerun()
    
    with col3:
        if st.button("🎓 강의 생성", key="goto_lecture", help="강의 스크립트 생성"):
            st.session_state.tab_selection = "강의 생성"
            st.experimental_rerun()
    
    with col4:
        if st.button("⚙️ 개발 설정", key="goto_dev_settings", help="개발 설정 및 도구"):
            st.session_state.tab_selection = "개발 설정"
            st.experimental_rerun()
    
    # AI 기능 구현 상태
    st.markdown('<div class="sub-header">AI 구현 상태</div>', unsafe_allow_html=True)
    
    # 칸반 기반 AI 구현 상태
    kanban_items = [
        {"번호": "1", "기능": "PDF 텍스트 추출", "상태": "완료", "설명": "PDF에서 텍스트 및 구조 추출"},
        {"번호": "2", "기능": "문서 청킹", "상태": "완료", "설명": "문서를 의미 단위로 분할"},
        {"번호": "3", "기능": "임베딩 생성", "상태": "완료", "설명": "텍스트 청크의 벡터 임베딩 생성"},
        {"번호": "4", "기능": "벡터 DB 저장", "상태": "완료", "설명": "ChromaDB에 임베딩 저장"},
        {"번호": "5", "기능": "의미 기반 검색", "상태": "완료", "설명": "쿼리와 유사한 문서 검색"},
        {"번호": "6", "기능": "RAG 컨텍스트 생성", "상태": "완료", "설명": "검색 결과로 컨텍스트 생성"},
        {"번호": "7", "기능": "질의응답", "상태": "완료", "설명": "문서 기반 질문 답변"},
        {"번호": "8", "기능": "대화 이력 관리", "상태": "완료", "설명": "사용자와의 대화 기록 유지"},
        {"번호": "9", "기능": "강의 스크립트 생성", "상태": "완료", "설명": "페이지별 강의 내용 생성"},
        {"번호": "10", "기능": "강의 개요 생성", "상태": "완료", "설명": "전체 문서 기반 개요 생성"},
        {"번호": "11", "기능": "음성 합성 (TTS)", "상태": "완료", "설명": "텍스트를 음성으로 변환"},
        {"번호": "12", "기능": "음성 인식 (STT)", "상태": "완료", "설명": "음성을 텍스트로 변환"},
        {"번호": "13", "기능": "다국어 지원", "상태": "완료", "설명": "여러 언어로 강의 및 질의응답"},
        {"번호": "14", "기능": "쿼리 개선", "상태": "완료", "설명": "사용자 질문을 검색에 최적화"},
        {"번호": "15", "기능": "음성 질의응답", "상태": "완료", "설명": "음성으로 질문하고 답변 듣기"}
    ]
    
    # DataFrame으로 변환
    df = pd.DataFrame(kanban_items)
    
    # 상태에 따른 색상 설정
    def highlight_status(val):
        if val == "완료":
            return 'background-color: #DCFCE7; color: #166534'
        elif val == "진행중":
            return 'background-color: #FEF9C3; color: #854D0E'
        elif val == "계획":
            return 'background-color: #E0E7FF; color: #3730A3'
        else:
            return ''
    
    # 스타일링된 DataFrame 표시
    st.dataframe(df.style.applymap(highlight_status, subset=['상태']), height=400)

# PDF 업로드 및 처리
def handle_pdf_upload():
    """PDF 업로드 및 처리"""
    st.markdown('<div class="main-header">PDF 업로드 및 처리</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    PDF 파일을 업로드하고 텍스트, 이미지, 표를 추출합니다.
    추출된 내용은 이후 청크화, 임베딩, RAG에 사용됩니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 파일 업로드
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    
    if uploaded_file is not None:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        st.session_state.pdf_path = tmp_path
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(f"**파일 업로드 완료:** {uploaded_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        add_log(f"PDF 파일 업로드 완료: {uploaded_file.name}")
        
        # 문서 정보 가져오기
        try:
            text_extractor = TextExtractor()
            doc_info = text_extractor.get_document_info(tmp_path)
            
            st.markdown('<div class="sub-header">문서 정보</div>', unsafe_allow_html=True)
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.markdown(f"**파일명:** {doc_info.get('file_name', '알 수 없음')}")
                st.markdown(f"**총 페이지 수:** {doc_info.get('total_pages', 0)}")
                st.markdown(f"**파일 크기:** {doc_info.get('file_size', 0) / 1024:.1f} KB")
            
            with info_col2:
                st.markdown(f"**제목:** {doc_info.get('title', '없음')}")
                st.markdown(f"**저자:** {doc_info.get('author', '없음')}")
                st.markdown(f"**생성 도구:** {doc_info.get('creator', '알 수 없음')}")
        except Exception as e:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.markdown(f"**문서 정보 가져오기 오류:** {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
            add_log(f"문서 정보 가져오기 오류: {e}", "error")
        
        # PDF 처리 옵션
        st.markdown('<div class="sub-header">처리 옵션</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            extract_text = st.checkbox("텍스트 추출", value=True)
        with col2:
            extract_images = st.checkbox("이미지 추출", value=False)
        with col3:
            extract_tables = st.checkbox("표 추출", value=False)
        
        # 처리 시작 버튼
        if st.button("PDF 처리 시작", type="primary"):
            with st.spinner("PDF 처리 중..."):
                start_time = time.time()
                
                try:
                    # 텍스트 추출
                    if extract_text:
                        add_log("텍스트 추출 시작")
                        text_extractor = TextExtractor()
                        extracted_text = text_extractor.extract_text_from_pdf(tmp_path)
                        st.session_state.extracted_text = extracted_text
                        add_log(f"텍스트 추출 완료: {len(extracted_text)}페이지")
                    
                    # 이미지 추출
                    if extract_images:
                        add_log("이미지 추출 시작")
                        image_extractor = ImageExtractor()
                        temp_dir = tempfile.mkdtemp()
                        image_paths = image_extractor.pdf_to_images(tmp_path, temp_dir)
                        add_log(f"이미지 추출 완료: {len(image_paths)}개 이미지")
                        
                        # 세션에 이미지 경로 저장
                        st.session_state.image_paths = image_paths
                    
                    # 표 추출
                    if extract_tables:
                        add_log("표 추출 시작")
                        try:
                            table_extractor = TableExtractor()
                            extracted_tables = table_extractor.extract_tables_from_pdf(tmp_path)
                            
                            # 표가 있으면 세션에 저장
                            if extracted_tables:
                                st.session_state.extracted_tables = extracted_tables
                                num_tables = sum(len(tables) for tables in extracted_tables.values())
                                add_log(f"표 추출 완료: {num_tables}개 표")
                            else:
                                add_log("추출된 표가 없습니다", "warning")
                        except Exception as e:
                            add_log(f"표 추출 중 오류 발생: {e}", "error")
                    
                    # 문서 ID 생성
                    document_id = f"doc_{Path(uploaded_file.name).stem}"
                    st.session_state.document_id = document_id
                    
                    # 컬렉션 이름 생성
                    collection_name = f"sraga_{Path(uploaded_file.name).stem}"
                    st.session_state.collection_name = collection_name
                    
                    # 처리 시간 기록
                    extraction_time = time.time() - start_time
                    add_timing("extraction", extraction_time)
                    
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown(f"**PDF 처리가 완료되었습니다!** (소요 시간: {extraction_time:.2f}초)")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    add_log(f"PDF 처리 완료 (소요 시간: {extraction_time:.2f}초)")
                
                except Exception as e:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**PDF 처리 중 오류 발생:** {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    add_log(f"PDF 처리 중 오류 발생: {e}", "error")
        
        # 추출된 콘텐츠 표시
        if st.session_state.extracted_text:
            show_extracted_text()
        
        if hasattr(st.session_state, "image_paths") and st.session_state.image_paths:
            show_extracted_images()
        
        if hasattr(st.session_state, "extracted_tables") and st.session_state.extracted_tables:
            show_extracted_tables()
        
        # 다음 단계 버튼
        if st.session_state.extracted_text:
            if st.button("다음 단계: 문서 청크화 및 임베딩", type="primary"):
                st.session_state.tab_selection = "청크화 및 임베딩"
                st.experimental_rerun()

# 추출된 텍스트 표시
def show_extracted_text():
    """추출된 텍스트 표시"""
    st.markdown('<div class="sub-header">추출된 텍스트</div>', unsafe_allow_html=True)
    
    # 페이지 선택
    page_nums = sorted(st.session_state.extracted_text.keys())
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_page = st.selectbox("페이지 선택", page_nums)
    
    with col2:
        if selected_page:
            total_chars = len(st.session_state.extracted_text[selected_page])
            total_words = len(st.session_state.extracted_text[selected_page].split())
            st.markdown(f"**페이지 {selected_page}:** {total_chars}자, {total_words}단어")
    
    if selected_page:
        text = st.session_state.extracted_text[selected_page]
        st.text_area("페이지 내용", text, height=300)

# 추출된 이미지 표시
def show_extracted_images():
    """추출된 이미지 표시"""
    st.markdown('<div class="sub-header">추출된 이미지</div>', unsafe_allow_html=True)
    
    # 이미지 선택
    image_indices = list(range(len(st.session_state.image_paths)))
    selected_image = st.selectbox("이미지 선택", image_indices, format_func=lambda x: f"이미지 {x+1}")
    
    if selected_image is not None:
        image_path = st.session_state.image_paths[selected_image]
        st.image(image_path, caption=f"이미지 {selected_image+1}")

# 추출된 표 표시
def show_extracted_tables():
    """추출된 표 표시"""
    st.markdown('<div class="sub-header">추출된 표</div>', unsafe_allow_html=True)
    
    # 페이지 선택
    page_nums = sorted(st.session_state.extracted_tables.keys())
    selected_page = st.selectbox("페이지 선택", page_nums, key="table_page_select")
    
    if selected_page:
        tables = st.session_state.extracted_tables[selected_page]
        
        # 표 선택
        table_indices = list(range(len(tables)))
        selected_table = st.selectbox("표 선택", table_indices, format_func=lambda x: f"표 {x+1}", key="table_select")
        
        if selected_table is not None:
            table = tables[selected_table]
            st.dataframe(table)

# 문서 청크화 및 임베딩
def handle_chunking_and_embedding():
    """문서 청크화 및 임베딩 처리"""
    st.markdown('<div class="main-header">문서 청크화 및 임베딩</div>', unsafe_allow_html=True)
    
    if not st.session_state.extracted_text:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**텍스트가 추출되지 않았습니다.** PDF 처리를 먼저 진행해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("PDF 처리 페이지로 이동"):
            st.session_state.tab_selection = "PDF 업로드"
            st.experimental_rerun()
        return
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    추출된 텍스트를 의미 단위로 분할(청크화)하고, 각 청크의 벡터 임베딩을 생성하여 벡터 데이터베이스에 저장합니다.
    청크 크기와 겹침 설정은 검색 성능에 중요한 영향을 미칩니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 청크화 설정
    st.markdown('<div class="sub-header">청크화 설정</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chunk_size = st.number_input(
            "청크 크기", 
            min_value=100, 
            max_value=4000, 
            value=st.session_state.chunking_config["chunk_size"], 
            step=100,
            help="각 청크의 최대 문자 수 (OpenAI 모델 컨텍스트 고려)"
        )
    
    with col2:
        chunk_overlap = st.number_input(
            "청크 겹침", 
            min_value=0, 
            max_value=1000, 
            value=st.session_state.chunking_config["chunk_overlap"], 
            step=50,
            help="연속된 청크 간 겹치는 문자 수 (컨텍스트 유지)"
        )
    
    with col3:
        chunking_strategy = st.selectbox(
            "청크화 전략", 
            ["sentence", "paragraph", "character"], 
            index=["sentence", "paragraph", "character"].index(st.session_state.chunking_config["chunking_strategy"]),
            format_func=lambda x: {
                "sentence": "문장 단위", 
                "paragraph": "단락 단위", 
                "character": "문자 단위"
            }.get(x),
            help="청크 분할 기준 (문장이 가장 효과적)"
        )
    
    # 청크화 설정 저장
    if st.button("청크화 설정 저장", key="save_chunking_config"):
        st.session_state.chunking_config = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunking_strategy": chunking_strategy
        }
        st.success("청크화 설정이 저장되었습니다.")
        add_log(f"청크화 설정 저장: 크기={chunk_size}, 겹침={chunk_overlap}, 전략={chunking_strategy}")
    
    # 청크화 버튼
    if st.button("문서 청크화", type="primary"):
        with st.spinner("문서 청크화 중..."):
            start_time = time.time()
            add_log("문서 청크화 시작")
            
            try:
                chunker = DocumentChunker(
                    chunk_size=st.session_state.chunking_config["chunk_size"],
                    chunk_overlap=st.session_state.chunking_config["chunk_overlap"],
                    chunking_strategy=st.session_state.chunking_config["chunking_strategy"]
                )
                
                chunked_document = chunker.chunk_document(st.session_state.extracted_text)
                st.session_state.chunked_document = chunked_document
                
                # 처리 시간 기록
                chunking_time = time.time() - start_time
                add_timing("chunking", chunking_time)
                
                add_log(f"문서 청크화 완료: {len(chunked_document['chunks'])}개 청크 ({chunking_time:.2f}초)")
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"**문서 청크화가 완료되었습니다!** {len(chunked_document['chunks'])}개 청크 생성 (소요 시간: {chunking_time:.2f}초)")
                st.markdown('</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.markdown(f"**문서 청크화 중 오류 발생:** {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
                add_log(f"문서 청크화 중 오류 발생: {e}", "error")
    
    # 청크 표시
    if st.session_state.chunked_document["chunks"]:
        st.markdown('<div class="sub-header">생성된 청크</div>', unsafe_allow_html=True)
        
        # 청크 통계
        chunks = st.session_state.chunked_document["chunks"]
        chunk_lengths = [len(chunk["text"]) for chunk in chunks]
        avg_length = sum(chunk_lengths) / len(chunk_lengths)
        
        # 통계 표시
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(chunks)}</div><div class="metric-label">총 청크 수</div></div>', unsafe_allow_html=True)
        
        with stats_col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_length:.1f}</div><div class="metric-label">평균 청크 길이 (자)</div></div>', unsafe_allow_html=True)
        
        with stats_col3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{max(chunk_lengths)}</div><div class="metric-label">최장 청크 길이 (자)</div></div>', unsafe_allow_html=True)
        
        # 청크 길이 히스토그램
        fig, ax = plt.subplots()
        ax.hist(chunk_lengths, bins=10, color='#3B82F6')
        ax.set_xlabel("청크 길이 (자)")
        ax.set_ylabel("청크 수")
        ax.set_title("청크 길이 분포")
        st.pyplot(fig)
        
        # 청크 샘플
        st.markdown('<div class="sub-header">청크 샘플</div>', unsafe_allow_html=True)
        
        # 샘플 청크 선택
        sample_idx = st.slider(
            "샘플 청크 선택", 
            min_value=0, 
            max_value=max(0, len(chunks)-1),
            value=0
        )
        
        if sample_idx < len(chunks):
            chunk = chunks[sample_idx]
            
            # 청크 메타데이터
            metadata = chunk["metadata"]
            st.markdown(f"**청크 {sample_idx+1}/{len(chunks)}** (페이지: {metadata.get('page_number', '알 수 없음')})")
            
            # 청크 내용
            st.text_area("청크 내용", chunk["text"], height=200)
    
    # 임베딩 설정
    st.markdown('<div class="sub-header">임베딩 설정</div>', unsafe_allow_html=True)
    
    if st.session_state.chunked_document["chunks"]:
        embed_col1, embed_col2 = st.columns(2)
        
        with embed_col1:
            embedding_model = st.selectbox(
                "임베딩 모델", 
                ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
                index=["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"].index(st.session_state.embedding_config["model"]),
                help="OpenAI 임베딩 모델 (large가 품질 높음, small이 경제적)"
            )
        
        with embed_col2:
            batch_size = st.number_input(
                "배치 크기", 
                min_value=1, 
                max_value=100, 
                value=st.session_state.embedding_config["batch_size"], 
                step=1,
                help="임베딩 생성 시 한 번에 처리할 청크 수"
            )
        
        # 임베딩 설정 저장
        if st.button("임베딩 설정 저장", key="save_embedding_config"):
            st.session_state.embedding_config = {
                "model": embedding_model,
                "batch_size": batch_size
            }
            st.success("임베딩 설정이 저장되었습니다.")
            add_log(f"임베딩 설정 저장: 모델={embedding_model}, 배치 크기={batch_size}")
        
        # 임베딩 버튼
        if st.button("임베딩 및 벡터 DB 저장", type="primary"):
            if not st.session_state.api_key_set:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.markdown("**OpenAI API 키가 설정되지 않았습니다.** 사이드바에서 API 키를 설정해주세요.")
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            with st.spinner("임베딩 및 벡터 DB 저장 중..."):
                start_time = time.time()
                
                try:
                    # 임베딩 파이프라인 초기화
                    add_log("임베딩 및 벡터 DB 저장 시작")
                    embedding_pipeline = EmbeddingPipeline(
                        batch_size=st.session_state.embedding_config["batch_size"],
                        embedding_model=st.session_state.embedding_config["model"]
                    )
                    
                    # 각 청크에 문서 ID 추가
                    document_id = st.session_state.document_id
                    collection_name = st.session_state.collection_name
                    
                    chunks = st.session_state.chunked_document["chunks"]
                    for chunk in chunks:
                        chunk["metadata"]["document_id"] = document_id
                    
                    # 벡터 DB에 저장
                    success = embedding_pipeline.process_chunks(chunks, collection_name)
                    
                    # 처리 시간 기록
                    embedding_time = time.time() - start_time
                    add_timing("embedding", embedding_time)
                    
                    if success:
                        add_log(f"임베딩 및 벡터 DB 저장 완료: {len(chunks)}개 청크 ({embedding_time:.2f}초)")
                        
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown(f"**임베딩 및 벡터 DB 저장이 완료되었습니다!** {len(chunks)}개 청크 저장 (소요 시간: {embedding_time:.2f}초)")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Vector DB 객체 초기화
                        st.session_state.vector_db = VectorDBService()
                        st.session_state.rag_engine = RAGEngine()
                        st.session_state.lecture_agent = LectureAgent()
                        st.session_state.qa_agent = QAAgent()
                        
                        # 다음 단계 버튼 표시
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("질의응답 테스트로 이동", type="primary"):
                                st.session_state.tab_selection = "질의응답 테스트"
                                st.experimental_rerun()
                        
                        with col2:
                            if st.button("강의 생성으로 이동", type="primary"):
                                st.session_state.tab_selection = "강의 생성"
                                st.experimental_rerun()
                    else:
                        add_log("임베딩 및 벡터 DB 저장 실패", "error")
                        
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.markdown("**임베딩 및 벡터 DB 저장에 실패했습니다.**")
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    add_log(f"임베딩 및 벡터 DB 저장 중 오류 발생: {e}", "error")
                    
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**오류 발생:** {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("문서 청크화를 먼저 진행해주세요.")

# 질의응답 테스트
def handle_qa_testing():
    """질의응답 테스트"""
    st.markdown('<div class="main-header">질의응답 테스트</div>', unsafe_allow_html=True)
    
    if not st.session_state.rag_engine or not st.session_state.qa_agent:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**RAG 엔진이 초기화되지 않았습니다.** 문서 임베딩을 먼저 완료해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("임베딩 페이지로 이동"):
            st.session_state.tab_selection = "청크화 및 임베딩"
            st.experimental_rerun()
        return
    
    if not st.session_state.api_key_set:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown("**OpenAI API 키가 설정되지 않았습니다.** 사이드바에서 API 키를 설정해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    업로드한 문서를 기반으로 질의응답을 테스트합니다.
    텍스트로 질문하거나 음성으로 질문할 수 있으며, 답변을 음성으로 받을 수도 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 질의응답 방식 선택
    qa_mode = st.radio(
        "질의응답 방식", 
        ["텍스트", "음성"],
        horizontal=True,
        help="텍스트: 입력창에 질문을 작성하여 답변 받기, 음성: 마이크로 질문하여 답변 받기"
    )
    
    # 대화 이력 표시
    st.markdown('<div class="sub-header">대화 이력</div>', unsafe_allow_html=True)
    
    conversation_container = st.container()
    
    with conversation_container:
        for i, entry in enumerate(st.session_state.conversation_history):
            if "user" in entry:
                st.markdown(f"**🧑 질문:**")
                st.markdown(f"{entry['user']}")
            if "assistant" in entry:
                st.markdown(f"**🤖 답변:**")
                st.markdown(f"{entry['assistant']}")
                if "audio_response_path" in entry:
                    st.audio(entry["audio_response_path"])
                st.markdown("---")
    
    # 텍스트 질문 입력
    if qa_mode == "텍스트":
        st.markdown('<div class="sub-header">텍스트로 질문하기</div>', unsafe_allow_html=True)
        
        user_input = st.text_area("질문을 입력하세요", height=100)
        generate_audio_response = st.checkbox("음성으로 답변 받기", value=False)
        
        if st.button("질문하기", type="primary") and user_input:
            with st.spinner("답변 생성 중..."):
                start_time = time.time()
                
                try:
                    add_log(f"질문 처리 중: {user_input[:30]}...")
                    
                    # 답변 생성
                    result = st.session_state.qa_agent.answer_question(
                        question=user_input,
                        collection_name=st.session_state.collection_name,
                        document_id=st.session_state.document_id,
                        conversation_history=st.session_state.conversation_history
                    )
                    
                    # 음성 응답 생성 (선택적)
                    if generate_audio_response:
                        audio_path = st.session_state.qa_agent.tts_service.generate_speech(
                            text=result["answer"],
                            filename=f"response_{uuid.uuid4().hex[:8]}"
                        )
                        
                        if audio_path:
                            result["audio_response_path"] = audio_path
                    
                    # 대화 이력 업데이트
                    st.session_state.conversation_history.append({"user": user_input})
                    st.session_state.conversation_history.append({
                        "assistant": result["answer"],
                        **({
                            "audio_response_path": result["audio_response_path"]
                        } if "audio_response_path" in result else {})
                    })
                    
                    # 처리 시간 기록
                    qa_time = time.time() - start_time
                    add_timing("qa_response", qa_time)
                    
                    # 테스트 결과 기록
                    st.session_state.test_results["qa_tests"].append({
                        "timestamp": time.time(),
                        "question": user_input,
                        "answer": result["answer"],
                        "duration": qa_time,
                        "has_audio": generate_audio_response
                    })
                    
                    add_log(f"답변 생성 완료 (소요 시간: {qa_time:.2f}초)")
                    st.experimental_rerun()
                except Exception as e:
                    add_log(f"답변 생성 중 오류 발생: {e}", "error")
                    
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**오류 발생:** {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # 음성 질문 입력
    else:  # 음성 모드
        st.markdown('<div class="sub-header">음성으로 질문하기</div>', unsafe_allow_html=True)
        
        st.markdown("""
        마이크를 사용하여 질문을 녹음합니다. 
        음성 감지 모드를 활성화하면 말하기 시작할 때 자동으로 녹음이 시작됩니다.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider(
                "녹음 시간 (초)", 
                min_value=3, 
                max_value=30, 
                value=5,
                help="음성 감지 비활성화 시 녹음할 시간"
            )
        
        with col2:
            detect_speech = st.checkbox(
                "음성 감지 모드", 
                value=True, 
                help="활성화: 음성 감지 시 녹음 시작/종료, 비활성화: 지정 시간 동안 녹음"
            )
            generate_audio_response = st.checkbox(
                "음성으로 답변 받기", 
                value=True,
                help="활성화: TTS로 음성 답변 생성"
            )
        
        record_col1, record_col2 = st.columns([3, 1])
        
        with record_col1:
            recording_status = st.empty()
        
        with record_col2:
            if st.button("녹음 시작", type="primary", use_container_width=True):
                recording_status.markdown('<div class="record-pulse" style="background-color: #DC2626; color: white; padding: 1rem; border-radius: 0.5rem; text-align: center;">녹음 중...</div>', unsafe_allow_html=True)
                
                with st.spinner("녹음 중..."):
                    try:
                        add_log("음성 녹음 시작")
                        start_time = time.time()
                        
                        # 녹음 및 처리
                        result = st.session_state.qa_agent.record_and_process(
                            collection_name=st.session_state.collection_name,
                            document_id=st.session_state.document_id,
                            conversation_history=st.session_state.conversation_history,
                            duration=duration,
                            detect_speech=detect_speech,
                            generate_audio_response=generate_audio_response
                        )
                        
                        if "error" in result:
                            add_log(f"녹음 또는 처리 중 오류 발생: {result['error']}", "error")
                            
                            recording_status.markdown('<div style="background-color: #FEE2E2; padding: 1rem; border-radius: 0.5rem; text-align: center;">녹음 실패</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="error-box">', unsafe_allow_html=True)
                            st.markdown(f"**오류 발생:** {result['error']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                            return
                        
                        # 녹음 결과 처리
                        if "recording" in result and result["recording"]:
                            recording = result["recording"]
                            transcription = recording["transcription"]
                            
                            if transcription:
                                add_log(f"음성 인식 결과: {transcription}")
                                
                                # 대화 이력 업데이트
                                st.session_state.conversation_history.append({"user": transcription})
                                st.session_state.conversation_history.append({
                                    "assistant": result["answer"],
                                    **({
                                        "audio_response_path": result["audio_response_path"]
                                    } if "audio_response_path" in result else {})
                                })
                                
                                # 처리 시간 기록
                                qa_time = time.time() - start_time
                                add_timing("qa_response", qa_time)
                                
                                # 테스트 결과 기록
                                st.session_state.test_results["qa_tests"].append({
                                    "timestamp": time.time(),
                                    "question": transcription,
                                    "answer": result["answer"],
                                    "duration": qa_time,
                                    "has_audio": generate_audio_response
                                })
                                
                                # STT 테스트 결과 기록
                                st.session_state.test_results["stt_tests"].append({
                                    "timestamp": time.time(),
                                    "audio_file": recording["file_path"],
                                    "transcription": transcription,
                                    "duration": qa_time
                                })
                                
                                add_log(f"음성 질문 처리 완료 (소요 시간: {qa_time:.2f}초)")
                                recording_status.markdown('<div style="background-color: #ECFDF5; padding: 1rem; border-radius: 0.5rem; text-align: center;">녹음 완료</div>', unsafe_allow_html=True)
                                st.experimental_rerun()
                            else:
                                add_log("음성 인식 실패", "warning")
                                recording_status.markdown('<div style="background-color: #FFFBEB; padding: 1rem; border-radius: 0.5rem; text-align: center;">음성 인식 실패</div>', unsafe_allow_html=True)
                                
                                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                                st.markdown("**음성 인식에 실패했습니다.** 다시 시도해주세요.")
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            add_log("녹음 실패", "error")
                            recording_status.markdown('<div style="background-color: #FEE2E2; padding: 1rem; border-radius: 0.5rem; text-align: center;">녹음 실패</div>', unsafe_allow_html=True)
                            
                            st.markdown('<div class="error-box">', unsafe_allow_html=True)
                            st.markdown("**녹음에 실패했습니다.** 다시 시도해주세요.")
                            st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        add_log(f"음성 처리 중 오류 발생: {e}", "error")
                        recording_status.markdown('<div style="background-color: #FEE2E2; padding: 1rem; border-radius: 0.5rem; text-align: center;">오류 발생</div>', unsafe_allow_html=True)
                        
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.markdown(f"**오류 발생:** {e}")
                        st.markdown('</div>', unsafe_allow_html=True)
    
    # 대화 이력 관리
    if st.session_state.conversation_history:
        st.markdown('<div class="sub-header">대화 이력 관리</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("대화 이력 초기화", type="secondary", use_container_width=True):
                st.session_state.conversation_history = []
                add_log("대화 이력 초기화 완료")
                st.experimental_rerun()
        
        with col2:
            if st.button("대화 이력 저장", type="secondary", use_container_width=True):
                try:
                    # 현재 시간으로 파일명 생성
                    timestamp = get_timestamp()
                    filename = f"conversation_{timestamp}"
                    
                    output_path = st.session_state.qa_agent.save_conversation(
                        st.session_state.conversation_history,
                        output_path=os.path.join(config.OUTPUT_DIR, "conversations", f"{filename}.json")
                    )
                    
                    if output_path:
                        add_log(f"대화 이력 저장 완료: {output_path}")
                        
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown(f"**대화 이력이 저장되었습니다:** {output_path}")
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    add_log(f"대화 이력 저장 중 오류 발생: {e}", "error")
                    
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**오류 발생:** {e}")
                    st.markdown('</div>', unsafe_allow_html=True)

# 강의 생성
def handle_lecture_generation():
    """강의 생성"""
    st.markdown('<div class="main-header">강의 생성</div>', unsafe_allow_html=True)
    
    if not st.session_state.vector_db or not st.session_state.rag_engine or not st.session_state.lecture_agent:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**RAG 엔진이 초기화되지 않았습니다.** 문서 임베딩을 먼저 완료해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("임베딩 페이지로 이동"):
            st.session_state.tab_selection = "청크화 및 임베딩"
            st.experimental_rerun()
        return
    
    if not st.session_state.api_key_set:
        st.markdown('<div class="error-box">', unsafe_allow_html=True)
        st.markdown("**OpenAI API 키가 설정되지 않았습니다.** 사이드바에서 API 키를 설정해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    업로드한 문서를 기반으로 강의 스크립트를 생성합니다.
    페이지별로 스크립트가 생성되며, 옵션에 따라 강의 음성도 생성할 수 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 강의 설정
    st.markdown('<div class="sub-header">강의 설정</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        lecture_title = st.text_input("강의 제목", value="SRAGA 강의", help="생성될 강의 제목")
    
    with col2:
        lecture_description = st.text_area("강의 설명 (선택)", height=100, help="강의 설명 또는 개요")
    
    # 고급 설정
    with st.expander("고급 설정", expanded=True):
        adv_col1, adv_col2, adv_col3 = st.columns(3)
        
        with adv_col1:
            target_language = st.selectbox(
                "강의 언어", 
                ["ko", "en", "ja", "zh"],
                format_func=lambda x: {
                    "ko": "한국어", 
                    "en": "영어", 
                    "ja": "일본어", 
                    "zh": "중국어"
                }.get(x),
                index=0,
                help="강의 스크립트 언어"
            )
        
        with adv_col2:
            style = st.selectbox(
                "강의 스타일", 
                ["educational", "conversational", "formal"],
                format_func=lambda x: {
                    "educational": "교육적", 
                    "conversational": "대화체", 
                    "formal": "격식체"
                }.get(x),
                index=0,
                help="강의 스크립트 말투 및 스타일"
            )
        
        with adv_col3:
            generate_audio = st.checkbox("오디오 생성", value=True, help="TTS로 강의 오디오 생성")
            if generate_audio:
                audio_voice = st.selectbox(
                    "음성 선택", 
                    ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    index=4,
                    help="OpenAI TTS 음성 종류"
                )
    
    # 강의 생성 버튼
    if st.button("강의 생성", type="primary"):
        with st.spinner("강의 생성 중..."):
            start_time = time.time()
            
            try:
                add_log("강의 생성 시작")
                
                # 강의 생성
                lecture_data = st.session_state.lecture_agent.generate_full_lecture(
                    document_content=st.session_state.extracted_text,
                    document_id=st.session_state.document_id,
                    collection_name=st.session_state.collection_name,
                    lecture_title=lecture_title,
                    lecture_description=lecture_description,
                    target_language=target_language,
                    style=style,
                    generate_audio=generate_audio,
                    audio_voice=audio_voice if generate_audio else "nova"
                )
                
                # 세션에 저장
                st.session_state.lecture_data = lecture_data
                
                # 오디오 경로 저장
                if generate_audio:
                    audio_paths = {}
                    for page_num, script in lecture_data["scripts"].items():
                        if "audio_path" in script:
                            audio_paths[page_num] = script["audio_path"]
                    st.session_state.audio_paths = audio_paths
                    
                    # TTS 테스트 결과 기록
                    for page_num, audio_path in audio_paths.items():
                        st.session_state.test_results["tts_tests"].append({
                            "timestamp": time.time(),
                            "text": lecture_data["scripts"][page_num]["script"],
                            "audio_file": audio_path,
                            "voice": audio_voice
                        })
                
                # 처리 시간 기록
                lecture_gen_time = time.time() - start_time
                add_timing("lecture_generation", lecture_gen_time)
                
                add_log(f"강의 생성 완료: {len(lecture_data['scripts'])}페이지 스크립트 (소요 시간: {lecture_gen_time:.2f}초)")
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"**강의 생성이 완료되었습니다!** (소요 시간: {lecture_gen_time:.2f}초)")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 강의 데이터 저장
                try:
                    # 현재 시간으로 파일명 생성
                    timestamp = get_timestamp()
                    filename = f"lecture_{timestamp}"
                    
                    output_path = st.session_state.lecture_agent.save_lecture_to_json(
                        lecture_data,
                        output_path=os.path.join(config.OUTPUT_DIR, "lectures", f"{filename}.json")
                    )
                    
                    if output_path:
                        add_log(f"강의 데이터 저장 완료: {output_path}")
                        
                        st.markdown('<div class="info-box">', unsafe_allow_html=True)
                        st.markdown(f"**강의 데이터가 저장되었습니다:** {output_path}")
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    add_log(f"강의 데이터 저장 중 오류 발생: {e}", "warning")
                
                # 탭 변경
                st.session_state.tab_selection = "강의 보기"
                st.experimental_rerun()
            except Exception as e:
                add_log(f"강의 생성 중 오류 발생: {e}", "error")
                
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.markdown(f"**오류 발생:** {e}")
                st.markdown('</div>', unsafe_allow_html=True)

# 강의 보기
def view_lecture():
    """강의 보기"""
    st.markdown('<div class="main-header">강의 보기</div>', unsafe_allow_html=True)
    
    if not st.session_state.lecture_data:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**생성된 강의가 없습니다.** 강의 생성을 먼저 진행해주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("강의 생성 페이지로 이동"):
            st.session_state.tab_selection = "강의 생성"
            st.experimental_rerun()
        return
    
    lecture_data = st.session_state.lecture_data
    
    # 강의 정보
    st.markdown(f'<div class="sub-header">{lecture_data["title"]}</div>', unsafe_allow_html=True)
    
    if lecture_data.get("description"):
        st.markdown(lecture_data["description"])
    
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.markdown(f"**언어:** {lecture_data['language']}")
    
    with info_col2:
        st.markdown(f"**스타일:** {lecture_data['style']}")
    
    with info_col3:
        st.markdown(f"**총 페이지:** {lecture_data['total_pages']}")
    
    # 강의 개요
    st.markdown('<div class="sub-header">강의 개요</div>', unsafe_allow_html=True)
    
    with st.expander("강의 개요 보기", expanded=True):
        st.markdown(lecture_data["outline"]["outline"])
    
    # 페이지별 스크립트
    st.markdown('<div class="sub-header">페이지별 스크립트</div>', unsafe_allow_html=True)
    
    # 페이지 선택
    page_nums = sorted(lecture_data["scripts"].keys())
    
    # 슬라이더로 페이지 선택
    selected_page = st.select_slider(
        "페이지 선택", 
        options=page_nums,
        format_func=lambda x: f"페이지 {x}"
    )
    
    if selected_page:
        script_data = lecture_data["scripts"][selected_page]
        
        # 페이지 내용 및 스크립트
        st.markdown(f'<div class="sub-header">페이지 {selected_page} 컨텐츠</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**원본 텍스트**")
            if selected_page in st.session_state.extracted_text:
                st.text_area(
                    "원본 내용", 
                    st.session_state.extracted_text[selected_page], 
                    height=250
                )
            else:
                st.info("원본 텍스트가 없습니다.")
        
        with col2:
            st.markdown("**생성된 스크립트**")
            st.text_area(
                "스크립트", 
                script_data["script"], 
                height=250
            )
            st.caption(f"단어 수: {script_data['word_count']}")
        
        # 오디오 재생 (있는 경우)
        if "audio_path" in script_data:
            st.markdown('<div class="sub-header">강의 오디오</div>', unsafe_allow_html=True)
            
            audio_path = script_data["audio_path"]
            st.audio(audio_path)
            
            # 오디오 정보 표시
            import os
            if os.path.exists(audio_path):
                audio_size = os.path.getsize(audio_path) / 1024  # KB
                st.caption(f"오디오 파일: {os.path.basename(audio_path)} ({audio_size:.1f} KB)")
    
    # 퀴즈 (있는 경우)
    if "quiz" in lecture_data:
        st.markdown('<div class="sub-header">퀴즈</div>', unsafe_allow_html=True)
        
        quiz_data = lecture_data["quiz"]["quiz"]
        questions = quiz_data.get("questions", [])
        
        if not questions:
            st.info("퀴즈가 생성되지 않았습니다.")
        else:
            st.markdown(f"**총 {len(questions)}개의 문제**")
            
            for i, question in enumerate(questions):
                with st.expander(f"문제 {i+1}: {question['question']}"):
                    options = question["options"]
                    answer_idx = int(question["answer"])
                    
                    # 선택지
                    for j, option in enumerate(options):
                        is_answer = j == answer_idx
                        if is_answer:
                            st.markdown(f"✅ **{option}** (정답)")
                        else:
                            st.markdown(f"- {option}")
                    
                    # 해설
                    st.markdown(f"**해설:** {question['explanation']}")
    
    # 강의 내보내기
    st.markdown('<div class="sub-header">강의 내보내기</div>', unsafe_allow_html=True)
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if st.button("강의 데이터 저장", type="secondary", use_container_width=True):
            try:
                # 현재 시간으로 파일명 생성
                timestamp = get_timestamp()
                filename = f"lecture_{timestamp}"
                
                output_path = st.session_state.lecture_agent.save_lecture_to_json(
                    lecture_data,
                    output_path=os.path.join(config.OUTPUT_DIR, "lectures", f"{filename}.json")
                )
                
                if output_path:
                    add_log(f"강의 데이터 저장 완료: {output_path}")
                    
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown(f"**강의 데이터가 저장되었습니다:** {output_path}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                add_log(f"강의 데이터 저장 중 오류 발생: {e}", "error")
                
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.markdown(f"**오류 발생:** {e}")
                st.markdown('</div>', unsafe_allow_html=True)
    
    with export_col2:
        if st.button("새 강의 생성", type="secondary", use_container_width=True):
            st.session_state.tab_selection = "강의 생성"
            st.experimental_rerun()

# 개발 설정
def handle_dev_settings():
    """개발 설정"""
    st.markdown('<div class="main-header">개발 설정</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("""
    개발 및 테스트 설정을 관리합니다.
    프롬프트 템플릿, 청킹 전략, 로깅 등을 설정할 수 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 탭 생성
    settings_tab, prompts_tab, chunking_tab, testing_tab = st.tabs([
        "기본 설정", "프롬프트 템플릿", "청킹 전략", "테스트 결과"
    ])
    
    # 기본 설정 탭
    with settings_tab:
        st.markdown('<div class="sub-header">기본 설정</div>', unsafe_allow_html=True)
        
        # 디버그 모드
        debug_mode = st.checkbox(
            "디버그 모드", 
            value=st.session_state.debug_mode,
            help="활성화 시 더 자세한 로그 기록"
        )
        
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            add_log(f"디버그 모드: {'활성화' if debug_mode else '비활성화'}")
        
        # OpenAI 모델 설정
        st.markdown("#### OpenAI 모델 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            llm_model = st.selectbox(
                "LLM 모델", 
                ["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
                index=0,
                help="텍스트 생성에 사용할 OpenAI 모델"
            )
        
        with col2:
            embedding_model = st.selectbox(
                "임베딩 모델", 
                ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
                index=["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"].index(st.session_state.embedding_config["model"]),
                help="벡터 임베딩에 사용할 OpenAI 모델"
            )
        
        st.markdown("#### TTS/STT 설정")
        
        tts_col1, tts_col2 = st.columns(2)
        
        with tts_col1:
            tts_model = st.selectbox(
                "TTS 모델", 
                ["tts-1", "tts-1-hd"],
                index=0,
                help="음성 합성에 사용할 OpenAI 모델"
            )
        
        with tts_col2:
            stt_model = st.selectbox(
                "STT 모델", 
                ["whisper-1"],
                index=0,
                help="음성 인식에 사용할 OpenAI 모델"
            )
        
        # 설정 저장 버튼
        if st.button("기본 설정 저장", type="primary"):
            # 임베딩 설정 업데이트
            st.session_state.embedding_config["model"] = embedding_model
            
            # 추가 설정들 (실제로는 이 프로토타입에서 활용되지 않음)
            add_log(f"설정 저장: LLM={llm_model}, 임베딩={embedding_model}, TTS={tts_model}, STT={stt_model}")
            
            st.success("설정이 저장되었습니다.")
    
    # 프롬프트 템플릿 탭
    with prompts_tab:
        st.markdown('<div class="sub-header">프롬프트 템플릿 관리</div>', unsafe_allow_html=True)
        
        st.markdown("""
        프롬프트 템플릿을 수정하여 AI 모델의 답변 품질과 스타일을 조정할 수 있습니다.
        각 템플릿에는 시스템 메시지와 사용자 메시지 템플릿이 포함됩니다.
        """)
        
        # 템플릿 선택
        template_type = st.selectbox(
            "템플릿 종류", 
            ["qa", "lecture"],
            format_func=lambda x: {
                "qa": "질의응답 템플릿", 
                "lecture": "강의 생성 템플릿"
            }.get(x),
            help="수정할 프롬프트 템플릿 종류"
        )
        
        # 선택된 템플릿 표시 및 수정
        if template_type:
            system_prompt = st.text_area(
                "시스템 메시지", 
                value=st.session_state.prompt_templates[template_type]["system"],
                height=150,
                help="AI 모델의 역할과 전반적인 지시사항 정의"
            )
            
            user_prompt = st.text_area(
                "사용자 메시지 템플릿", 
                value=st.session_state.prompt_templates[template_type]["user"],
                height=150,
                help="실제 요청 형식 (변수는 {변수명} 형태로 포함)"
            )
            
            # 변수 안내
            st.markdown("**템플릿 변수:**")
            if template_type == "qa":
                st.markdown("- `{context}`: RAG에서 검색된 문서 컨텍스트")
                st.markdown("- `{question}`: 사용자 질문")
            elif template_type == "lecture":
                st.markdown("- `{page_content}`: 페이지 원본 내용")
            
            # 템플릿 저장
            if st.button("템플릿 저장", type="primary"):
                st.session_state.prompt_templates[template_type] = {
                    "system": system_prompt,
                    "user": user_prompt
                }
                
                add_log(f"{template_type} 프롬프트 템플릿 업데이트")
                st.success("프롬프트 템플릿이 저장되었습니다.")
    
    # 청킹 전략 탭
    with chunking_tab:
        st.markdown('<div class="sub-header">청킹 전략 관리</div>', unsafe_allow_html=True)
        
        st.markdown("""
        문서 청킹 전략을 관리하고 실험합니다.
        청크 크기와 전략은 RAG 시스템의 성능에 큰 영향을 미칩니다.
        """)
        
        # 청킹 설정
        chunk_col1, chunk_col2, chunk_col3 = st.columns(3)
        
        with chunk_col1:
            chunk_size = st.number_input(
                "청크 크기", 
                min_value=100, 
                max_value=4000, 
                value=st.session_state.chunking_config["chunk_size"], 
                step=100,
                help="각 청크의 최대 문자 수"
            )
        
        with chunk_col2:
            chunk_overlap = st.number_input(
                "청크 겹침", 
                min_value=0, 
                max_value=1000, 
                value=st.session_state.chunking_config["chunk_overlap"], 
                step=50,
                help="연속된 청크 간 겹치는 문자 수"
            )
        
        with chunk_col3:
            chunking_strategy = st.selectbox(
                "청크화 전략", 
                ["sentence", "paragraph", "character"], 
                index=["sentence", "paragraph", "character"].index(st.session_state.chunking_config["chunking_strategy"]),
                format_func=lambda x: {
                    "sentence": "문장 단위", 
                    "paragraph": "단락 단위", 
                    "character": "문자 단위"
                }.get(x),
                help="청크 분할 기준"
            )
        
        # 청킹 설정 저장
        if st.button("청킹 설정 저장", key="save_chunking_settings", type="primary"):
            st.session_state.chunking_config = {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "chunking_strategy": chunking_strategy
            }
            
            add_log(f"청킹 설정 업데이트: 크기={chunk_size}, 겹침={chunk_overlap}, 전략={chunking_strategy}")
            st.success("청킹 설정이 저장되었습니다.")
        
        # 청킹 전략 설명
        st.markdown("#### 청킹 전략 설명")
        
        st.markdown("""
        **문장 단위 (sentence)**
        - 문장 경계를 유지하며 청크를 생성합니다.
        - 문맥 이해도가 높지만, 너무 긴 문장이 있으면 청크 크기를 초과할 수 있습니다.
        - 일반적인 문서에 가장 적합합니다.
        
        **단락 단위 (paragraph)**
        - 단락 경계를 유지하며 청크를 생성합니다.
        - 관련 내용이 함께 유지되지만, 단락이 너무 길면 중요 정보가 손실될 수 있습니다.
        - 명확한 단락 구조가 있는 문서에 적합합니다.
        
        **문자 단위 (character)**
        - 지정된 문자 수에 따라 단순히 텍스트를 분할합니다.
        - 구조를 무시하므로 문맥 이해도가 낮을 수 있습니다.
        - 구조가 불분명한 문서에 적합합니다.
        """)
        
        # 청크 크기 권장사항
        st.markdown("#### 청크 크기 권장사항")
        
        st.markdown("""
        **작은 청크 (300-500자)**
        - 더 정확한 검색 결과
        - 특정 정보를 찾는 데 유리
        - 문맥이 제한적일 수 있음
        
        **중간 청크 (800-1200자)**
        - 검색 정확도와 문맥의 균형
        - 대부분의 일반 문서에 적합
        - 일반적인 질의응답에 권장
        
        **큰 청크 (1500-4000자)**
        - 더 넓은 문맥 제공
        - 복잡한 개념이나 관계 이해에 유리
        - 검색 정확도가 낮아질 수 있음
        
        **청크 겹침**은 일반적으로 청크 크기의 10-20%로 설정하는 것이 좋습니다.
        """)
    
    # 테스트 결과 탭
    with testing_tab:
        st.markdown('<div class="sub-header">테스트 결과 분석</div>', unsafe_allow_html=True)
        
        st.markdown("""
        지금까지 수행한 테스트의 결과를 분석합니다.
        각 기능별 성능과 처리 시간을 확인할 수 있습니다.
        """)
        
        # 처리 시간 시각화
        st.markdown("#### 처리 시간 분석")
        
        # 각 카테고리별 평균 처리 시간 계산
        processing_times = st.session_state.processing_times
        avg_times = {}
        
        for category, times in processing_times.items():
            if times:
                avg_times[category] = sum(item["duration"] for item in times) / len(times)
            else:
                avg_times[category] = 0
        
        # 평균 처리 시간 차트
        if any(avg_times.values()):
            # 데이터 준비
            chart_data = pd.DataFrame({
                "카테고리": list(avg_times.keys()),
                "평균 처리 시간 (초)": list(avg_times.values())
            })
            
            # 카테고리 이름 변환
            category_names = {
                "extraction": "텍스트 추출",
                "chunking": "문서 청크화",
                "embedding": "임베딩 생성",
                "rag_query": "RAG 검색",
                "qa_response": "질의응답",
                "lecture_generation": "강의 생성"
            }
            
            chart_data["카테고리"] = chart_data["카테고리"].map(lambda x: category_names.get(x, x))
            
            # 차트 생성
            fig = px.bar(
                chart_data,
                x="카테고리",
                y="평균 처리 시간 (초)",
                title="기능별 평균 처리 시간",
                color="카테고리",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            # 차트 레이아웃 설정
            fig.update_layout(
                xaxis_title="기능 카테고리",
                yaxis_title="평균 처리 시간 (초)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("아직 처리 시간 데이터가 없습니다.")
        
        # 테스트 결과 분석
        st.markdown("#### 테스트 결과 통계")
        
        test_results = st.session_state.test_results
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(test_results["qa_tests"])}</div><div class="metric-label">질의응답 테스트</div></div>', unsafe_allow_html=True)
        
        with stats_col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(test_results["tts_tests"])}</div><div class="metric-label">TTS 테스트</div></div>', unsafe_allow_html=True)
        
        with stats_col3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(test_results["stt_tests"])}</div><div class="metric-label">STT 테스트</div></div>', unsafe_allow_html=True)
        
        with stats_col4:
            total_tests = sum(len(tests) for tests in test_results.values())
            st.markdown(f'<div class="metric-card"><div class="metric-value">{total_tests}</div><div class="metric-label">총 테스트</div></div>', unsafe_allow_html=True)
        
        # 테스트 세부 결과
        test_type = st.selectbox(
            "테스트 종류",
            ["질의응답 (QA)", "음성 합성 (TTS)", "음성 인식 (STT)"],
            index=0
        )
        
        if test_type == "질의응답 (QA)":
            show_qa_test_results()
        elif test_type == "음성 합성 (TTS)":
            show_tts_test_results()
        elif test_type == "음성 인식 (STT)":
            show_stt_test_results()

# 질의응답 테스트 결과 표시
def show_qa_test_results():
    """질의응답 테스트 결과 표시"""
    qa_tests = st.session_state.test_results["qa_tests"]
    
    if not qa_tests:
        st.info("질의응답 테스트 결과가 없습니다.")
        return
    
    st.markdown("##### 질의응답 테스트 결과")
    
    # 테스트 선택
    test_indices = list(range(len(qa_tests)))
    selected_test = st.selectbox(
        "테스트 선택", 
        test_indices, 
        format_func=lambda x: f"테스트 {x+1} - {qa_tests[x]['question'][:30]}..."
    )
    
    if selected_test is not None:
        test = qa_tests[selected_test]
        
        # 테스트 정보 표시
        st.markdown(f"**질문:** {test['question']}")
        st.markdown(f"**답변:** {test['answer']}")
        st.markdown(f"**소요 시간:** {test['duration']:.2f}초")
        
        if test.get('has_audio', False):
            st.markdown("**음성 답변 생성됨**")

# TTS 테스트 결과 표시
def show_tts_test_results():
    """음성 합성 테스트 결과 표시"""
    tts_tests = st.session_state.test_results["tts_tests"]
    
    if not tts_tests:
        st.info("음성 합성(TTS) 테스트 결과가 없습니다.")
        return
    
    st.markdown("##### 음성 합성(TTS) 테스트 결과")
    
    # 테스트 선택
    test_indices = list(range(len(tts_tests)))
    selected_test = st.selectbox(
        "테스트 선택", 
        test_indices, 
        format_func=lambda x: f"테스트 {x+1} - {tts_tests[x]['text'][:30]}..."
    )
    
    if selected_test is not None:
        test = tts_tests[selected_test]
        
        # 테스트 정보 표시
        st.markdown(f"**원본 텍스트:** {test['text'][:200]}...")
        st.markdown(f"**음성 모델:** {test['voice']}")
        
        # 오디오 재생
        if 'audio_file' in test and test['audio_file']:
            st.audio(test['audio_file'])

# STT 테스트 결과 표시
def show_stt_test_results():
    """음성 인식 테스트 결과 표시"""
    stt_tests = st.session_state.test_results["stt_tests"]
    
    if not stt_tests:
        st.info("음성 인식(STT) 테스트 결과가 없습니다.")
        return
    
    st.markdown("##### 음성 인식(STT) 테스트 결과")
    
    # 테스트 선택
    test_indices = list(range(len(stt_tests)))
    selected_test = st.selectbox(
        "테스트 선택", 
        test_indices, 
        format_func=lambda x: f"테스트 {x+1} - {stt_tests[x]['transcription'][:30]}..."
    )
    
    if selected_test is not None:
        test = stt_tests[selected_test]
        
        # 테스트 정보 표시
        st.markdown(f"**인식 결과:** {test['transcription']}")
        st.markdown(f"**소요 시간:** {test['duration']:.2f}초")
        
        # 오디오 재생
        if 'audio_file' in test and test['audio_file']:
            st.audio(test['audio_file'])
            st.caption(f"음성 파일: {os.path.basename(test['audio_file'])}")

# 로그 내용 표시
def show_logs():
    """로그 내용 표시"""
    st.markdown('<div class="sub-header">로그</div>', unsafe_allow_html=True)
    
    log_messages = st.session_state.log_messages
    
    if not log_messages:
        st.info("로그 메세지가 없습니다.")
        return
    
    # 로그 레벨 필터
    log_level = st.radio(
        "로그 레벨", 
        ["전체", "info", "warning", "error", "debug"],
        horizontal=True
    )
    
    # 필터링된 로그 가져오기
    if log_level == "전체":
        filtered_logs = log_messages
    else:
        filtered_logs = [log for log in log_messages if log["level"] == log_level]
    
    # 로그 표시
    st.markdown('<div class="log-container">', unsafe_allow_html=True)
    
    for log in filtered_logs:
        timestamp = log["timestamp"]
        message = log["message"]
        level = log["level"]
        
        # 로그 레벨에 따른 스타일 적용
        if level == "info":
            st.markdown(f"<span style='color: #3B82F6;'>[{timestamp}] [INFO]</span> {message}", unsafe_allow_html=True)
        elif level == "warning":
            st.markdown(f"<span style='color: #F59E0B;'>[{timestamp}] [WARNING]</span> {message}", unsafe_allow_html=True)
        elif level == "error":
            st.markdown(f"<span style='color: #EF4444;'>[{timestamp}] [ERROR]</span> {message}", unsafe_allow_html=True)
        elif level == "debug":
            st.markdown(f"<span style='color: #6B7280;'>[{timestamp}] [DEBUG]</span> {message}", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 로그 저장 버튼
    if st.button("로그 저장", type="secondary"):
        try:
            # 현재 시간으로 파일명 생성
            timestamp = get_timestamp()
            filename = f"log_{timestamp}.txt"
            
            # 로그 내용 작성
            log_content = "\n".join([f"[{log['timestamp']}] [{log['level'].upper()}] {log['message']}" for log in log_messages])
            
            # 파일 저장
            log_dir = os.path.join(config.OUTPUT_DIR, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, filename)
            
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            
            add_log(f"로그 저장 완료: {log_path}")
            
            st.success(f"로그가 저장되었습니다: {log_path}")
        except Exception as e:
            add_log(f"로그 저장 중 오류 발생: {e}", "error")
            st.error(f"오류 발생: {e}")

# 사이드바 표시
def show_sidebar():
    """사이드바 표시"""
    st.sidebar.markdown('<div class="main-header">테스트 메뉴</div>', unsafe_allow_html=True)
    
    # API 키 설정
    if not st.session_state.api_key_set:
        set_api_key()
    else:
        st.sidebar.success("OpenAI API 키가 설정되었습니다.")
        if st.sidebar.button("API 키 변경"):
            st.session_state.api_key_set = False
            st.experimental_rerun()
    
    st.sidebar.markdown("---")
    
    # 탭 선택
    st.sidebar.markdown("### 페이지 선택")
    
    tabs = [
        "시작 화면", 
        "PDF 업로드", 
        "청크화 및 임베딩", 
        "질의응답 테스트", 
        "강의 생성", 
        "강의 보기", 
        "개발 설정",
        "로그"
    ]
    
    for tab in tabs:
        if st.sidebar.button(tab, key=f"sidebar_{tab}", use_container_width=True):
            st.session_state.tab_selection = tab
            st.experimental_rerun()
    
    st.sidebar.markdown("---")
    
    # 직접 설정 변경 옵션 (개발용)
    st.sidebar.markdown("### 개발자 기능")
    
    # 디버그 모드
    debug_mode = st.sidebar.checkbox("디버그 모드", value=st.session_state.debug_mode)
    if debug_mode != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_mode
        add_log(f"디버그 모드: {'\ud65c\uc131\ud654' if debug_mode else '\ube44\ud65c\uc131\ud654'}")
    
    # 상태 초기화
    if st.sidebar.button("세션 초기화", help="모든 테스트 데이터와 상태를 초기화합니다."):
        for key in list(st.session_state.keys()):
            if key not in ['api_key_set', 'debug_mode']:
                if key in st.session_state:
                    del st.session_state[key]
        
        # 세션 초기화
        init_session_state()
        add_log("세션 상태가 초기화되었습니다.")
        st.sidebar.success("세션이 초기화되었습니다!")
        st.experimental_rerun()
    
    # 가장 최근 로그
    if st.session_state.log_messages:
        st.sidebar.markdown("### 최근 로그")
        
        logs_to_show = st.session_state.log_messages[-5:]
        for log in reversed(logs_to_show):
            level = log["level"]
            timestamp = log["timestamp"]
            
            if level == "error":
                st.sidebar.error(f"[{timestamp}] {log['message'][:50]}..." if len(log['message']) > 50 else f"[{timestamp}] {log['message']}")
            elif level == "warning":
                st.sidebar.warning(f"[{timestamp}] {log['message'][:50]}..." if len(log['message']) > 50 else f"[{timestamp}] {log['message']}")
            else:
                st.sidebar.info(f"[{timestamp}] {log['message'][:50]}..." if len(log['message']) > 50 else f"[{timestamp}] {log['message']}")

# 메인 함수
def main():
    """메인 함수"""
    # 세션 초기화
    init_session_state()
    
    # 사이드바 표시
    show_sidebar()
    
    # 탭 선택에 따른 페이지 표시
    if st.session_state.tab_selection == "시작 화면":
        show_start_screen()
    elif st.session_state.tab_selection == "PDF 업로드":
        handle_pdf_upload()
    elif st.session_state.tab_selection == "청크화 및 임베딩":
        handle_chunking_and_embedding()
    elif st.session_state.tab_selection == "질의응답 테스트":
        handle_qa_testing()
    elif st.session_state.tab_selection == "강의 생성":
        handle_lecture_generation()
    elif st.session_state.tab_selection == "강의 보기":
        view_lecture()
    elif st.session_state.tab_selection == "개발 설정":
        handle_dev_settings()
    elif st.session_state.tab_selection == "로그":
        show_logs()

# 엔트리 포인트
if __name__ == "__main__":
    main()
