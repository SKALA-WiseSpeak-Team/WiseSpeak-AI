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
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 설정 관련 모듈
│   │   └── logger.py        # 로그 형식 정의
│   ├── db
│   │   ├── __init__.py
│   │   └── session.py       # Supabase session 관리 모듈
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── chroma.py 
│   ├── models/              # 데이터 모델 정의
│   │   └── __init__.py 
│   └── routers/             # 라우트 처리 모듈 디렉토리
│       └── __init__.py
├── .env                     # 환경 변수 설정 파일
├── requirements.txt         # 의존성 목록
└── README.md                # 프로젝트 설명서
```
