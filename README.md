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
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 API 키를 저장하세요.
```
OPENAI_API_KEY="your_openai_api_key_here"
```

### 2️⃣ 실행 방법
프로젝트 루트 디렉토리에서 실행
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📂 추가 정보
### 📁 디렉토리 구조
> 현재 구조 기준. 디렉토리 구조 수정 할 때 변경 필요.
```
WiseSpeak-AI/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 설정 관련 모듈
│   │   └── utils.py         # 유틸리티 함수 모음
│   ├── cruds                # 데이터 CRUD 관련 모듈(Supabase 접근)
│   │   └── __init__.py
│   ├── models/              # 데이터 모델 정의
│   │   └── __init__.py 
│   └── routers/             # 라우트 처리 모듈 디렉토리
│       └── __init__.py
├── .env                     # 환경 변수 설정 파일
├── requirements.txt         # 의존성 목록
└── README.md                # 프로젝트 설명서
```
