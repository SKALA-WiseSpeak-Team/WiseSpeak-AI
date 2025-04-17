# setup.py
# 설치 스크립트 - 프로젝트 설치를 위한 설정

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lecture_rag_system",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="PDF 기반 다국어 강의 생성 및 질의응답 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lecture_rag_system",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11.9",
    install_requires=[
        "python-dotenv>=1.0.0",
        "openai>=1.12.0",
        "chromadb>=0.4.22",
        "pypdf2>=3.0.1",
        "pdf2image>=1.16.3",
        "pytesseract>=0.3.10",
        "pillow>=10.2.0",
        "langchain>=0.1.9",
        "langchain-openai>=0.0.5",
        "langdetect>=1.0.9",
        "supabase>=2.3.0",
        "numpy>=1.26.0",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.6",
        "fastapi>=0.109.0",
        "uvicorn>=0.25.0",
        "pydub>=0.25.1"  # 오디오 처리용 추가 라이브러리
    ],
    entry_points={
        "console_scripts": [
            "lecture-rag=app.main:main",
        ],
    },
)