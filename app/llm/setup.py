"""
SRAGA AI 설치 스크립트
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wisespeak_ai",
    version="0.1.0",
    author="SRAGA Team",
    author_email="contact@example.com",
    description="AI 기반 PDF 강의 및 챗봇 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/sraga_ai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyPDF2>=3.0.1",
        "pdfplumber>=0.10.3",
        "camelot-py>=0.11.0",
        "tabula-py>=2.9.0",
        "pdf2image>=1.17.0",
        "pytesseract>=0.3.10",
        "opencv-python>=4.8.1.78",
        "chromadb>=0.4.22",
        "openai>=1.12.0",
        "langchain>=0.1.4",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.13",
        "langdetect>=1.0.9",
        "googletrans>=4.0.0-rc1",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
        "loguru>=0.7.2",
        "numpy>=1.26.3",
        "pandas>=2.1.4",
    ],
)
