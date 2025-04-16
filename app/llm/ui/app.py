"""
SRAGA AI Streamlit 앱
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import time
import base64
import logging
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

# 세션 상태 초기화
def init_session_state():
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
        st.session_state.tab_selection = "업로드 및 PDF 처리"
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

# 로깅 메시지 추가
def add_log(message: str, level: str = "info"):
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.log_messages.append({"timestamp": timestamp, "message": message, "level": level})
    
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
    api_key = st.sidebar.text_input("OpenAI API 키", type="password")
    if st.sidebar.button("API 키 설정"):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state.api_key_set = True
            add_log("OpenAI API 키가 설정되었습니다")
            st.sidebar.success("API 키가 설정되었습니다!")
        else:
            st.sidebar.error("API 키를 입력해주세요")

# PDF 업로드 처리
def handle_pdf_upload():
    st.header("PDF 업로드 및 처리")
    
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    
    if uploaded_file is not None:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        st.session_state.pdf_path = tmp_path
        
        st.success(f"파일 업로드 완료: {uploaded_file.name}")
        add_log(f"PDF 파일 업로드 완료: {uploaded_file.name}")
        
        # 문서 정보 가져오기
        text_extractor = TextExtractor()
        doc_info = text_extractor.get_document_info(tmp_path)
        
        st.subheader("문서 정보")
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.write(f"**파일명:** {doc_info.get('file_name', '알 수 없음')}")
            st.write(f"**총 페이지 수:** {doc_info.get('total_pages', 0)}")
            st.write(f"**파일 크기:** {doc_info.get('file_size', 0) / 1024:.1f} KB")
        
        with info_col2:
            st.write(f"**제목:** {doc_info.get('title', '없음')}")
            st.write(f"**저자:** {doc_info.get('author', '없음')}")
            st.write(f"**생성 도구:** {doc_info.get('creator', '알 수 없음')}")
        
        # PDF 처리 옵션
        st.subheader("처리 옵션")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            extract_text = st.checkbox("텍스트 추출", value=True)
        with col2:
            extract_images = st.checkbox("이미지 추출", value=False)
        with col3:
            extract_tables = st.checkbox("표 추출", value=False)
        
        # 처리 시작 버튼
        if st.button("PDF 처리 시작"):
            with st.spinner("PDF 처리 중..."):
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
                
                st.success("PDF 처리가 완료되었습니다!")
                add_log("PDF 처리 완료")
                
                # 탭 변경
                st.session_state.tab_selection = "문서 청크화 및 임베딩"
                st.experimental_rerun()

# 추출된 텍스트 표시
def show_extracted_text():
    st.subheader("추출된 텍스트")
    
    if not st.session_state.extracted_text:
        st.info("텍스트가 추출되지 않았습니다. PDF 처리를 먼저 진행해주세요.")
        return
    
    # 페이지 선택
    page_nums = sorted(st.session_state.extracted_text.keys())
    selected_page = st.selectbox("페이지 선택", page_nums)
    
    if selected_page:
        text = st.session_state.extracted_text[selected_page]
        st.text_area("페이지 내용", text, height=300)

# 추출된 이미지 표시
def show_extracted_images():
    st.subheader("추출된 이미지")
    
    if not hasattr(st.session_state, "image_paths") or not st.session_state.image_paths:
        st.info("이미지가 추출되지 않았습니다.")
        return
    
    # 이미지 선택
    image_indices = list(range(len(st.session_state.image_paths)))
    selected_image = st.selectbox("이미지 선택", image_indices, format_func=lambda x: f"이미지 {x+1}")
    
    if selected_image is not None:
        image_path = st.session_state.image_paths[selected_image]
        st.image(image_path, caption=f"이미지 {selected_image+1}")

# 추출된 표 표시
def show_extracted_tables():
    st.subheader("추출된 표")
    
    if not hasattr(st.session_state, "extracted_tables") or not st.session_state.extracted_tables:
        st.info("표가 추출되지 않았습니다.")
        return
    
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
    st.header("문서 청크화 및 임베딩")
    
    if not st.session_state.extracted_text:
        st.warning("텍스트가 추출되지 않았습니다. PDF 처리를 먼저 진행해주세요.")
        return
    
    st.subheader("청크화 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chunk_size = st.number_input("청크 크기", min_value=100, max_value=4000, value=1000, step=100)
    
    with col2:
        chunk_overlap = st.number_input("청크 겹침", min_value=0, max_value=1000, value=200, step=50)
    
    with col3:
        chunking_strategy = st.selectbox(
            "청크화 전략", 
            ["sentence", "paragraph", "character"], 
            format_func=lambda x: {
                "sentence": "문장 단위", 
                "paragraph": "단락 단위", 
                "character": "문자 단위"
            }.get(x)
        )
    
    # 청크화 버튼
    if st.button("문서 청크화"):
        with st.spinner("문서 청크화 중..."):
            add_log("문서 청크화 시작")
            
            chunker = DocumentChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=chunking_strategy
            )
            
            chunked_document = chunker.chunk_document(st.session_state.extracted_text)
            st.session_state.chunked_document = chunked_document
            
            add_log(f"문서 청크화 완료: {len(chunked_document['chunks'])}개 청크")
            st.success(f"문서 청크화가 완료되었습니다! {len(chunked_document['chunks'])}개 청크 생성.")
    
    # 청크 표시
    if st.session_state.chunked_document["chunks"]:
        st.subheader("생성된 청크")
        
        # 청크 통계
        chunks = st.session_state.chunked_document["chunks"]
        chunk_lengths = [len(chunk["text"]) for chunk in chunks]
        avg_length = sum(chunk_lengths) / len(chunk_lengths)
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("총 청크 수", len(chunks))
        with stat_col2:
            st.metric("평균 청크 길이", f"{avg_length:.1f}자")
        with stat_col3:
            st.metric("최장 청크 길이", max(chunk_lengths))
        
        # 청크 길이 히스토그램
        fig, ax = plt.subplots()
        ax.hist(chunk_lengths, bins=10)
        ax.set_xlabel("청크 길이")
        ax.set_ylabel("청크 수")
        ax.set_title("청크 길이 분포")
        st.pyplot(fig)
        
        # 청크 예시
        st.subheader("청크 샘플")
        
        sample_chunks = chunks[:min(3, len(chunks))]
        for i, chunk in enumerate(sample_chunks):
            with st.expander(f"청크 {i+1} (페이지 {chunk['metadata'].get('page_number')})"):
                st.text_area(f"내용", chunk["text"], height=150, key=f"chunk_{i}")
    
    # 임베딩 설정
    st.subheader("임베딩 설정")
    
    if st.session_state.chunked_document["chunks"]:
        embed_col1, embed_col2 = st.columns(2)
        
        with embed_col1:
            embedding_model = st.selectbox(
                "임베딩 모델", 
                ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
                index=0
            )
        
        with embed_col2:
            batch_size = st.number_input("배치 크기", min_value=1, max_value=100, value=10, step=1)
        
        # 임베딩 버튼
        if st.button("임베딩 및 벡터 DB 저장"):
            if not st.session_state.api_key_set:
                st.error("OpenAI API 키가 설정되지 않았습니다. 사이드바에서 API 키를 설정해주세요.")
                return
            
            with st.spinner("임베딩 및 벡터 DB 저장 중..."):
                try:
                    # 임베딩 파이프라인 초기화
                    add_log("임베딩 및 벡터 DB 저장 시작")
                    embedding_pipeline = EmbeddingPipeline(batch_size=batch_size)
                    
                    # 각 청크에 문서 ID 추가
                    document_id = st.session_state.document_id
                    collection_name = st.session_state.collection_name
                    
                    chunks = st.session_state.chunked_document["chunks"]
                    for chunk in chunks:
                        chunk["metadata"]["document_id"] = document_id
                    
                    # 벡터 DB에 저장
                    success = embedding_pipeline.process_chunks(chunks, collection_name)
                    
                    if success:
                        add_log(f"임베딩 및 벡터 DB 저장 완료: {len(chunks)}개 청크")
                        st.success(f"임베딩 및 벡터 DB 저장이 완료되었습니다! {len(chunks)}개 청크 저장.")
                        
                        # Vector DB 객체 초기화
                        st.session_state.vector_db = VectorDBService()
                        st.session_state.rag_engine = RAGEngine()
                        st.session_state.lecture_agent = LectureAgent()
                        st.session_state.qa_agent = QAAgent()
                        
                        # 탭 변경
                        st.session_state.tab_selection = "강의 생성"
                        st.experimental_rerun()
                    else:
                        add_log("임베딩 및 벡터 DB 저장 실패", "error")
                        st.error("임베딩 및 벡터 DB 저장에 실패했습니다.")
                except Exception as e:
                    add_log(f"임베딩 및 벡터 DB 저장 중 오류 발생: {e}", "error")
                    st.error(f"오류 발생: {e}")
    else:
        st.info("문서 청크화를 먼저 진행해주세요.")

# 강의 생성
def handle_lecture_generation():
    st.header("강의 생성")
    
    if not st.session_state.vector_db or not st.session_state.rag_engine or not st.session_state.lecture_agent:
        st.warning("임베딩 및 벡터 DB 저장을 먼저 완료해주세요.")
        return
    
    if not st.session_state.api_key_set:
        st.error("OpenAI API 키가 설정되지 않았습니다. 사이드바에서 API 키를 설정해주세요.")
        return
    
    st.subheader("강의 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lecture_title = st.text_input("강의 제목", value="SRAGA 강의")
    
    with col2:
        lecture_description = st.text_area("강의 설명 (선택)", height=100)
    
    # 고급 설정
    with st.expander("고급 설정"):
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
                index=0
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
                index=0
            )
        
        with adv_col3:
            generate_audio = st.checkbox("오디오 생성", value=False)
            if generate_audio:
                audio_voice = st.selectbox(
                    "음성 선택", 
                    ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    index=4
                )
    
    # 강의 생성 버튼
    if st.button("강의 생성"):
        with st.spinner("강의 생성 중..."):
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
                
                add_log(f"강의 생성 완료: {len(lecture_data['scripts'])}페이지 스크립트")
                st.success("강의 생성이 완료되었습니다!")
                
                # 강의 데이터 저장
                try:
                    output_path = st.session_state.lecture_agent.save_lecture_to_json(lecture_data)
                    if output_path:
                        add_log(f"강의 데이터 저장 완료: {output_path}")
                        st.info(f"강의 데이터가 저장되었습니다: {output_path}")
                except Exception as e:
                    add_log(f"강의 데이터 저장 중 오류 발생: {e}", "warning")
                
                # 탭 변경
                st.session_state.tab_selection = "강의 보기"
                st.experimental_rerun()
            except Exception as e:
                add_log(f"강의 생성 중 오류 발생: {e}", "error")
                st.error(f"오류 발생: {e}")

# 강의 보기
def view_lecture():
    st.header("강의 보기")
    
    if not st.session_state.lecture_data:
        st.warning("생성된 강의가 없습니다. 강의 생성을 먼저 진행해주세요.")
        return
    
    lecture_data = st.session_state.lecture_data
    
    # 강의 정보
    st.subheader(lecture_data["title"])
    if lecture_data.get("description"):
        st.write(lecture_data["description"])
    
    st.write(f"**언어:** {lecture_data['language']}")
    st.write(f"**스타일:** {lecture_data['style']}")
    st.write(f"**총 페이지:** {lecture_data['total_pages']}")
    
    # 강의 개요
    with st.expander("강의 개요", expanded=True):
        st.markdown(lecture_data["outline"]["outline"])
    
    # 페이지별 스크립트
    st.subheader("페이지별 스크립트")
    
    # 페이지 선택
    page_nums = sorted(lecture_data["scripts"].keys())
    selected_page = st.selectbox("페이지 선택", page_nums)
    
    if selected_page:
        script_data = lecture_data["scripts"][selected_page]
        
        # 페이지 내용 및 스크립트
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"페이지 {selected_page} 원본")
            if selected_page in st.session_state.extracted_text:
                st.text_area("내용", st.session_state.extracted_text[selected_page], height=300)
            else:
                st.info("원본 텍스트가 없습니다.")
        
        with col2:
            st.subheader("생성된 스크립트")
            st.text_area("스크립트", script_data["script"], height=300)
            st.write(f"단어 수: {script_data['word_count']}")
        
        # 오디오 재생 (있는 경우)
        if "audio_path" in script_data:
            st.subheader("오디오")
            
            audio_path = script_data["audio_path"]
            st.audio(audio_path)
    
    # 퀴즈 (있는 경우)
    if "quiz" in lecture_data:
        st.subheader("퀴즈")
        
        quiz_data = lecture_data["quiz"]["quiz"]
        questions = quiz_data.get("questions", [])
        
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
                        st.write(f"- {option}")
                
                # 해설
                st.markdown(f"**해설:** {question['explanation']}")

# 챗봇 대화
def handle_chatbot():
    st.header("챗봇 대화")
    
    if not st.session_state.vector_db or not st.session_state.rag_engine or not st.session_state.qa_agent:
        st.warning("임베딩 및 벡터 DB 저장을 먼저 완료해주세요.")
        return
    
    if not st.session_state.api_key_set:
        st.error("OpenAI API 키가 설정되지 않았습니다. 사이드바에서 API 키를 설정해주세요.")
        return
    
    # 대화 이력
    st.subheader("대화")
    
    # 대화 이력 표시
    for entry in st.session_state.conversation_history:
        if "user" in entry:
            st.markdown(f"#### 🧑 **질문**")
            st.markdown(entry["user"])
        if "assistant" in entry:
            st.markdown(f"#### 🤖 **답변**")
            st.markdown(entry["assistant"])
            if "audio_response_path" in entry:
                st.audio(entry["audio_response_path"])
            st.markdown("---")
    
    # 새 질문 입력
    st.subheader("새 질문")
    
    # 텍스트 입력 또는 음성 입력 선택
    input_type = st.radio("입력 방법", ["텍스트", "음성"], horizontal=True)
    
    if input_type == "텍스트":
        user_input = st.text_area("질문을 입력하세요", height=100)
        generate_audio_response = st.checkbox("음성으로 답변 받기", value=False)
        
        if st.button("질문하기") and user_input:
            with st.spinner("답변 생성 중..."):
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
                        **({"audio_response_path": result["audio_response_path"]} if "audio_response_path" in result else {})
                    })
                    
                    add_log("답변 생성 완료")
                    st.experimental_rerun()
                except Exception as e:
                    add_log(f"답변 생성 중 오류 발생: {e}", "error")
                    st.error(f"오류 발생: {e}")
    else:  # 음성 입력
        st.info("마이크를 사용하여 질문을 녹음합니다.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider("녹음 시간 (초)", min_value=3, max_value=30, value=5)
        
        with col2:
            detect_speech = st.checkbox("음성 감지 모드", value=True, 
                                        help="활성화 시 음성을 감지하면 녹음 시작, 비활성화 시 지정된 시간 동안 녹음")
            generate_audio_response = st.checkbox("음성으로 답변 받기", value=True)
        
        if st.button("녹음 시작"):
            with st.spinner("녹음 중..."):
                try:
                    add_log("음성 녹음 시작")
                    
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
                        st.error(f"오류 발생: {result['error']}")
                        return
                    
                    # 녹음 결과 표시
                    if "recording" in result and result["recording"]:
                        recording = result["recording"]
                        transcription = recording["transcription"]
                        
                        if transcription:
                            add_log(f"음성 인식 결과: {transcription}")
                            
                            # 대화 이력 업데이트
                            st.session_state.conversation_history.append({"user": transcription})
                            st.session_state.conversation_history.append({
                                "assistant": result["answer"],
                                **({"audio_response_path": result["audio_response_path"]} if "audio_response_path" in result else {})
                            })
                            
                            add_log("음성 질문 처리 완료")
                            st.experimental_rerun()
                        else:
                            add_log("음성 인식 실패", "warning")
                            st.warning("음성 인식에 실패했습니다. 다시 시도해주세요.")
                    else:
                        add_log("녹음 실패", "error")
                        st.error("녹음에 실패했습니다. 다시 시도해주세요.")
                except Exception as e:
                    add_log(f"음성 처리 중 오류 발생: {e}", "error")
                    st.error(f"오류 발생: {e}")
    
    # 대화 이력 관리
    if st.session_state.conversation_history:
        if st.button("대화 이력 초기화"):
            st.session_state.conversation_history = []
            add_log("대화 이력 초기화 완료")
            st.experimental_rerun()
        
        if st.button("대화 이력 저장"):
            try:
                output_path = st.session_state.qa_agent.save_conversation(
                    st.session_state.conversation_history
                )
                
                if output_path:
                    add_log(f"대화 이력 저장 완료: {output_path}")
                    st.success(f"대화 이력이 저장되었습니다: {output_path}")
            except Exception as e:
                add_log(f"대화 이력 저장 중 오류 발생: {e}", "error")
                st.error(f"오류 발생: {e}")

# 로그 및 디버깅
def show_logs():
    st.header("로그 및 디버깅")
    
    # 로그 메시지 표시
    st.subheader("로그 메시지")
    
    # 로그 레벨 필터
    log_levels = st.multiselect(
        "로그 레벨 필터", 
        ["info", "warning", "error", "debug"],
        default=["info", "warning", "error"]
    )
    
    # 필터링된 로그 표시
    filtered_logs = [log for log in st.session_state.log_messages if log["level"] in log_levels]
    
    if filtered_logs:
        log_df = pd.DataFrame(filtered_logs)
        
        # 색상 스타일 설정
        def color_level(val):
            colors = {
                "info": "lightblue",
                "warning": "orange",
                "error": "red",
                "debug": "lightgrey"
            }
            return f"background-color: {colors.get(val, 'white')}"
        
        st.dataframe(log_df.style.applymap(color_level, subset=["level"]), height=400)
    else:
        st.info("표시할 로그 메시지가 없습니다.")
    
    # 로그 초기화
    if st.button("로그 초기화"):
        st.session_state.log_messages = []
        st.success("로그가 초기화되었습니다.")
        st.experimental_rerun()
    
    # 벡터 DB 상태
    st.subheader("벡터 DB 상태")
    
    if st.session_state.vector_db:
        try:
            # 컬렉션 목록
            collections = st.session_state.vector_db.list_collections()
            st.write(f"**컬렉션 목록:** {', '.join(collections)}")
            
            # 현재 컬렉션의 문서 수
            if st.session_state.collection_name:
                doc_count = st.session_state.vector_db.count_documents(st.session_state.collection_name)
                st.write(f"**{st.session_state.collection_name} 문서 수:** {doc_count}")
        except Exception as e:
            st.error(f"벡터 DB 상태 조회 중 오류 발생: {e}")
    else:
        st.info("벡터 DB가 초기화되지 않았습니다.")

# 메인 앱
def main():
    # 세션 상태 초기화
    init_session_state()
    
    # 사이드바 메뉴
    st.sidebar.title("SRAGA AI 테스트 UI")
    
    # API 키 설정
    if not st.session_state.api_key_set:
        set_api_key()
    else:
        st.sidebar.success("✅ OpenAI API 키가 설정되었습니다")
    
    # 메뉴 선택
    menu_options = [
        "업로드 및 PDF 처리",
        "문서 청크화 및 임베딩",
        "강의 생성",
        "강의 보기",
        "챗봇 대화",
        "로그 및 디버깅"
    ]
    
    # 사이드바에서 선택한 메뉴로 세션 상태 업데이트
    selected_menu = st.sidebar.radio("메뉴", menu_options)
    if selected_menu != st.session_state.tab_selection:
        st.session_state.tab_selection = selected_menu
    
    # 선택된 메뉴에 따라 페이지 표시
    if st.session_state.tab_selection == "업로드 및 PDF 처리":
        handle_pdf_upload()
        
        # 추출된 콘텐츠 표시 (선택적)
        if st.session_state.extracted_text:
            show_extracted_text()
        
        if hasattr(st.session_state, "image_paths") and st.session_state.image_paths:
            show_extracted_images()
        
        if hasattr(st.session_state, "extracted_tables") and st.session_state.extracted_tables:
            show_extracted_tables()
            
    elif st.session_state.tab_selection == "문서 청크화 및 임베딩":
        handle_chunking_and_embedding()
        
    elif st.session_state.tab_selection == "강의 생성":
        handle_lecture_generation()
        
    elif st.session_state.tab_selection == "강의 보기":
        view_lecture()
        
    elif st.session_state.tab_selection == "챗봇 대화":
        handle_chatbot()
        
    elif st.session_state.tab_selection == "로그 및 디버깅":
        show_logs()
    
    # 푸터
    st.sidebar.markdown("---")
    st.sidebar.caption("SRAGA AI 테스트 UI v0.1")

if __name__ == "__main__":
    main()
