# SRAGA AI (Smart Retrieval-Augmented Generation Assistant)

SRAGA AI는 PDF 문서를 기반으로 강의 생성 및 질의응답 서비스를 제공하는 고급 RAG(Retrieval-Augmented Generation) 시스템입니다. 음성 인식(STT)과 음성 합성(TTS) 기능을 통합하여 완전한 멀티모달 상호작용을 지원합니다.

## 프로젝트 아키텍처

![SRAGA AI 아키텍처](https://imgur.com/placeholder.png)

SRAGA AI는 다음과 같은 모듈식 구조로 설계되었습니다:

```
wisespeak_ai/
├── agents/                  # 에이전트 모듈
│   ├── lecture_agent.py     # 강의 생성 에이전트
│   └── qa_agent.py          # 질의응답 에이전트
├── config/                  # 환경 설정
│   └── config.py            # 설정 파일
├── embeddings/              # 임베딩 처리
│   └── embedding_pipeline.py# 임베딩 파이프라인
├── processors/              # 데이터 처리
│   ├── document/            # 문서 처리
│   │   └── document_chunker.py # 문서 청킹
│   ├── language/            # 언어 처리
│   │   └── language_processor.py # 언어 처리
│   └── pdf/                 # PDF 처리
│       ├── image_extractor.py # 이미지 추출
│       ├── ocr_processor.py # OCR 처리
│       ├── table_extractor.py # 표 추출
│       └── text_extractor.py # 텍스트 추출
├── rag/                     # RAG 엔진
│   └── rag_engine.py        # RAG 검색 및 생성
├── services/                # 서비스 모듈
│   ├── openai_service.py    # OpenAI API 서비스
│   ├── speech/              # 음성 서비스
│   │   ├── stt_service.py   # 음성-텍스트 변환
│   │   └── tts_service.py   # 텍스트-음성 변환
│   └── vector_db.py         # 벡터 데이터베이스 서비스
├── ui/                      # 사용자 인터페이스
│   ├── app.py               # 메인 애플리케이션 UI
│   └── test_ui.py           # 테스트 및 개발 UI
└── utils/                   # 유틸리티
    ├── file_utils.py        # 파일 처리 유틸리티
    └── logger.py            # 로깅 유틸리티
```

## 주요 기능

### 1. PDF 처리 및 정보 추출
- **텍스트 추출**: PyPDF2와 pdfplumber를 사용한 고정밀 텍스트 추출
- **이미지 추출**: PDF 내 이미지 추출 및 처리
- **표 추출**: camelot-py 및 tabula-py를 활용한 표 구조 인식 및 추출
- **OCR 처리**: pytesseract를 활용한 스캔 문서 텍스트 인식

### 2. 문서 처리 및 청킹
- **다중 청킹 전략**: 문장, 단락, 문자 단위 청킹 지원
- **페이지 간 컨텍스트 유지**: 페이지 경계를 넘는 청킹으로 문맥 보존
- **최적 청크 크기 설정**: 검색 정확도와 컨텍스트 균형 조정

### 3. 임베딩 및 벡터 검색
- **고급 임베딩 모델**: OpenAI text-embedding-3-large/small 모델 지원
- **배치 처리**: 대용량 문서의 효율적인 임베딩 처리
- **ChromaDB 통합**: 벡터 데이터베이스 저장 및 검색 최적화

### 4. 고급 RAG 시스템
- **쿼리 확장**: 검색 품질 향상을 위한 쿼리 개선
- **재순위화**: 검색 결과 정확도 향상을 위한 재순위화
- **컨텍스트 압축**: 최적 컨텍스트 생성을 위한 압축 기법
- **다국어 지원**: 여러 언어로 검색 및 응답 생성

### 5. 강의 생성
- **강의 스크립트 생성**: PDF 내용 기반 교육용 강의 스크립트 생성
- **강의 개요 및 구조화**: 핵심 개념 중심의 강의 개요 생성
- **퀴즈 자동 생성**: 학습 자료 기반 퀴즈 문제 및 해설 생성
- **다양한 강의 스타일**: 교육적, 대화형, 격식체 등 다양한 스타일 지원

### 6. 질의응답
- **문서 기반 정확한 응답**: RAG를 활용한 정확한 정보 제공
- **대화 이력 관리**: 문맥을 고려한 연속 대화 처리
- **출처 제공**: 응답의 출처 페이지 및 관련도 정보 제공
- **음성 인터페이스**: 음성으로 질문하고 음성으로 답변 받기

### 7. 음성 처리
- **텍스트-음성 변환(TTS)**: OpenAI TTS API 활용 자연스러운 음성 생성
- **음성-텍스트 변환(STT)**: OpenAI Whisper 또는 Google STT 활용 정확한 음성 인식
- **실시간 음성 처리**: 마이크 입력을 통한 실시간 대화 지원
- **다국어 음성 처리**: 여러 언어의 음성 인식 및 합성 지원

### 8. 개발 및 테스트 도구
- **포괄적인 테스트 UI**: 모든 기능을 통합 테스트할 수 있는 Streamlit 기반 인터페이스
- **성능 메트릭 모니터링**: 처리 시간 및 품질 지표 수집
- **로깅 시스템**: 상세한 개발 및 디버깅 로깅 지원
- **설정 관리**: 다양한 파라미터 조정 및 실험 지원

## 설치 및 설정

### 필수 요구사항
- Python 3.9 이상
- 충분한 디스크 공간 (벡터 DB 및 처리된 파일 저장용)
- OpenAI API 키
- (선택) Tesseract OCR 설치 (OCR 처리용)

### 설치 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/your-repo/sraga_ai.git
   cd sraga_ai
   ```

2. 가상환경 설정
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. 의존성 설치
   ```bash
   pip install -r wisespeak_ai/requirements.txt
   ```

4. 환경 변수 설정
   ```bash
   cp wisespeak_ai/.env.example wisespeak_ai/.env
   # .env 파일을 편집하여 다음 값들을 설정:
   # - OPENAI_API_KEY: OpenAI API 키
   # - OPENAI_MODEL: 사용할 OpenAI 모델 (기본값: gpt-4o)
   # - OPENAI_EMBEDDING_MODEL: 임베딩 모델 (기본값: text-embedding-3-large)
   # - CHROMA_DB_DIR: 벡터 DB 저장 경로
   # - TESSERACT_PATH: Tesseract 실행 파일 경로 (OCR 처리용)
   ```

5. 개발 모드로 설치
   ```bash
   pip install -e .
   ```

6. Tesseract OCR 설치 (선택, OCR 처리를 위해 필요)
   - Windows: [Tesseract 다운로드](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - Mac: `brew install tesseract`

### 테스트 UI 실행

1. Streamlit 테스트 UI 실행
   ```bash
   cd wisespeak_ai
   streamlit run ui/test_ui.py
   ```

2. 웹 브라우저에서 테스트 UI 접속
   ```
   http://localhost:8501
   ```

## 개발 및 테스트 가이드

### 테스트 UI 사용 방법

테스트 UI를 통해 SRAGA AI의 다양한 기능을 쉽게 테스트하고 개발할 수 있습니다:

1. **PDF 업로드 및 처리**
   - PDF 파일을 업로드하고 텍스트, 이미지, 표 추출
   - 추출된 내용 확인 및 검증

2. **청크화 및 임베딩**
   - 문서 청크화 전략 및 파라미터 설정
   - 임베딩 생성 및 벡터 DB 저장
   - 청크 품질 검토

3. **질의응답 테스트**
   - 텍스트 입력 또는 음성 입력으로 질문
   - 응답 품질 및 정확도 평가
   - 음성 답변 생성 테스트

4. **강의 생성**
   - 페이지별 강의 스크립트 생성
   - 강의 개요 및 퀴즈 생성
   - TTS를 통한 강의 오디오 생성

5. **개발 설정**
   - 프롬프트 템플릿 관리 및 최적화
   - 청킹 전략 실험 및 비교
   - 성능 메트릭 수집 및 분석

### 프롬프트 최적화

RAG 시스템과 생성 결과의 품질을 향상시키기 위한 프롬프트 최적화:

1. **질의응답 프롬프트**
   - 컨텍스트 활용 지시 명확화
   - 답변 형식 및 스타일 가이드 제공
   - 불확실성 처리 방법 정의

2. **강의 생성 프롬프트**
   - 교육 목표 및 대상 명시
   - 강의 스타일 및 톤 가이드
   - 핵심 개념 강조 방법 정의

### 청킹 전략 실험

최적의 RAG 성능을 위한 청킹 전략 테스트:

1. **청크 크기 실험**
   - 작은 청크 (300-500자): 검색 정확도 향상, 컨텍스트 제한
   - 중간 청크 (800-1200자): 균형적인 성능
   - 큰 청크 (1500-4000자): 넓은 컨텍스트, 검색 정확도 감소

2. **청킹 전략 비교**
   - 문장 기반: 의미 단위 보존, 일반 문서 적합
   - 단락 기반: 관련 내용 유지, 구조화된 문서 적합
   - 문자 기반: 정확한 크기 제어, 특수 문서 적합

3. **청크 겹침 최적화**
   - 청크 크기의 10-20% 겹침 실험
   - 페이지 간 컨텍스트 유지 실험

## API 참조

### 주요 클래스 및 메소드

#### TextExtractor
```python
# PDF에서 텍스트 추출
text_extractor = TextExtractor()
extracted_text = text_extractor.extract_text_from_pdf("sample.pdf")
```

#### DocumentChunker
```python
# 문서 청크화
chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200, chunking_strategy="sentence")
chunked_document = chunker.chunk_document(extracted_text)
```

#### EmbeddingPipeline
```python
# 청크 임베딩 및 저장
embedding_pipeline = EmbeddingPipeline(batch_size=10)
embedding_pipeline.process_chunks(chunked_document["chunks"], "collection_name")
```

#### RAGEngine
```python
# RAG 검색 및 생성
rag_engine = RAGEngine()
results = rag_engine.rag_query(
    query="질문 내용",
    collection_name="collection_name",
    n_results=5
)
```

#### QAAgent
```python
# 질의응답
qa_agent = QAAgent()
answer = qa_agent.answer_question(
    question="질문 내용",
    collection_name="collection_name",
    document_id="doc_id"
)

# 음성 질의응답
result = qa_agent.record_and_process(
    collection_name="collection_name",
    document_id="doc_id",
    generate_audio_response=True
)
```

#### LectureAgent
```python
# 강의 생성
lecture_agent = LectureAgent()
lecture_data = lecture_agent.generate_full_lecture(
    document_content=extracted_text,
    document_id="doc_id",
    collection_name="collection_name",
    lecture_title="강의 제목",
    target_language="ko",
    generate_audio=True
)
```

## 성능 최적화

### 1. 벡터 DB 최적화
- ChromaDB 인덱스 최적화 설정
- 대규모 문서 처리를 위한 배치 처리 구현
- 메모리 사용량 모니터링 및 최적화

### 2. 검색 성능 향상
- 쿼리 확장 및 재순위화 파라미터 조정
- 컨텍스트 압축 전략 최적화
- n_results 값 실험을 통한 최적 검색 결과 수 설정

### 3. 응답 품질 개선
- 프롬프트 템플릿 세부 조정
- 도메인 특화 지식 통합
- 다국어 지원 품질 향상

## 알려진 제한사항 및 개선 계획

### 현재 제한사항

1. **PDF 처리**
   - 복잡한 레이아웃의 PDF 처리 정확도 제한
   - 스캔된 문서의 OCR 품질 의존성
   - 표 추출의 정확도 제한

2. **벡터 데이터베이스**
   - 현재 ChromaDB만 지원
   - 대용량 문서 처리 시 메모리 사용량 증가
   - 분산 처리 지원 부족

3. **모델 의존성**
   - OpenAI API에 대한 의존성
   - 로컬 LLM 실행 옵션 부재
   - API 비용 관리 메커니즘 부족

4. **음성 처리**
   - 잡음이 많은 환경에서의 STT 정확도 제한
   - 긴 오디오 처리 시 지연 발생
   - 특수 용어 및 전문 용어 인식 한계

### 개선 계획

1. **단기 개선 사항**
   - 더 많은 PDF 처리 엔진 통합 (PyMuPDF 등)
   - 표 추출 정확도 향상을 위한 알고리즘 개선
   - 다양한 벡터 데이터베이스 지원 (FAISS, Milvus, Pinecone 등)

2. **중기 개선 사항**
   - 다양한 LLM 지원 (Claude, Llama, Gemini 등)
   - 로컬 LLM 실행 옵션 추가
   - Self-RAG, HyDE, FLARE 등 최신 RAG 기법 통합
   - 멀티모달 입력 처리 (이미지, 음성, 텍스트 통합)

3. **장기 개선 사항**
   - RAG 성능 자동 최적화 시스템
   - 대화형 에이전트 고도화
   - 엔터프라이즈급 확장성 및 보안 기능
   - 실시간 협업 및 멀티유저 지원

## 기여 가이드라인

SRAGA AI 프로젝트에 기여하는 방법:

1. **이슈 제출**
   - 버그 보고
   - 기능 요청
   - 문서 개선 제안

2. **코드 기여**
   - 포크 및 클론
   - 개발 브랜치 생성
   - 코드 변경 및 테스트
   - 풀 리퀘스트 제출

3. **코딩 표준**
   - PEP 8 스타일 가이드 준수
   - 명확한 변수 및 함수 이름 사용
   - 모든 새 코드에 주석 및 문서화
   - 단위 테스트 작성

4. **프로젝트 구조**
   - 적절한 모듈에 코드 추가
   - 기존 API와 일관성 유지
   - 의존성 최소화

## 라이센스

이 프로젝트는 MIT 라이센스 하에 제공됩니다.

## 연락처

질문이나 피드백이 있으시면 다음으로 연락해 주세요:
- 이메일: your.email@example.com
- GitHub Issues: [이슈 제출](https://github.com/your-repo/sraga_ai/issues)
