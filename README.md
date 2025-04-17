# 🎓 WiseSpeak-AI

## 📚 프로젝트 소개

---
## 🚀 시작하기
### 1️⃣ 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 패키지 설치
pip install -r requirements.txt
```

### API 키 설정 방법
#### `.env` 파일 사용 
프로젝트 app 디렉토리에 `.env.example` 파일을 참고하여 .env로 생성하고 API 키를 저장하세요.

### 2️⃣ 실행 방법
프로젝트 루트 디렉토리에서 실행
```bash
# 백엔드 서버 실행
python run.py
```

서버가 시작되면 `http://localhost:8000`에서 접속할 수 있습니다.
API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 📂 추가 정보
### 📁 디렉토리 구조
```
WiseSpeak-AI/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 환경 설정
│   │   └── logger.py          # 로깅 설정
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py         # 데이터베이스 연결
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── process_common_data.py  # 공통 데이터 처리
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── openai_client.py    # OpenAI API 클라이언트
│   │   │   ├── rag.py             # RAG 시스템 구현
│   │   │   └── script_gen.py      # 스크립트 생성
│   │   ├── vector_db/            # 벡터 데이터베이스 저장소
│   │   ├── pdf/                  # PDF 파일 저장소
│   │   ├── audio/               # 오디오 파일 저장소
│   │   └── language/            # 언어 관련 데이터
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py              # 채팅 관련 모델
│   │   ├── course.py            # 강의 관련 모델
│   │   ├── lecture.py           # 강의 관련 모델
│   │   └── page.py              # 페이지 관련 모델
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py              # 채팅 API 엔드포인트
│   │   ├── course.py            # 강의 API 엔드포인트
│   │   └── lectures.py          # 강의 API 엔드포인트
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lecture_service.py     # 강의 관련 비즈니스 로직
│   │   ├── lecture_rag_service.py # RAG 관련 비즈니스 로직
│   │   ├── openai_service.py      # OpenAI API 연동
│   │   ├── pdf_service.py         # PDF 처리 로직
│   │   └── voice_service.py       # 음성 처리 로직
│   │
│   ├── data/                    # 데이터 저장소
│   │   ├── pdf/                 # PDF 파일 저장
│   │   ├── audio/               # 오디오 파일 저장
│   │   └── vector_db/           # 벡터 데이터베이스
│   │
│   ├── uploads/                 # 업로드된 파일 임시 저장
│   │
│   ├── __init__.py
│   └── main.py                  # FastAPI 앱 설정 및 실행
│
├── .env.example                 # 환경 변수 예시
├── .gitignore                   # Git 제외 파일
├── db_init.sql                  # 데이터베이스 초기화 스크립트
├── requirements.txt             # 패키지 의존성
├── setup.py                     # 설치 스크립트
├── run.py                       # 실행 스크립트
└── README.md                    # 프로젝트 문서
```