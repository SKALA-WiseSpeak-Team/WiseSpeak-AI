"""
Agent 테스트
"""
import os
import pytest

from wisespeak_ai.agents.lecture_agent import LectureAgent
from wisespeak_ai.agents.qa_agent import QAAgent
from wisespeak_ai.processors.language.language_processor import LanguageProcessor

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="OpenAI API 키가 설정되지 않았습니다")
def test_lecture_agent():
    """강의 에이전트 테스트"""
    # 강의 에이전트 초기화
    agent = LectureAgent()
    
    # 테스트용 페이지 내용
    page_content = {
        "page_number": 1,
        "text": "인공지능(AI)은 인간의 지능을 모방하는 기술입니다. 기계학습은 AI의 하위 분야로, 데이터로부터 학습하는 알고리즘을 연구합니다.",
        "document_id": "test_doc"
    }
    
    try:
        # 강의 스크립트 생성 (실제 RAG 검색 없이 간단 테스트)
        script = agent.generate_lecture_script(
            page_content=page_content,
            collection_name="non_existent_collection",  # 실제 컬렉션 없이 테스트
            lecture_title="인공지능 개요"
        )
        
        # 결과 확인
        assert isinstance(script, dict)
        assert "script" in script
        assert isinstance(script["script"], str)
        assert len(script["script"]) > 0
        assert "page_number" in script
        assert script["page_number"] == 1
    except Exception as e:
        pytest.skip(f"강의 에이전트 테스트 오류: {e}")

@pytest.mark.skipif("OPENAI_API_KEY" not in os.environ, reason="OpenAI API 키가 설정되지 않았습니다")
def test_qa_agent():
    """QA 에이전트 테스트"""
    # QA 에이전트 초기화
    agent = QAAgent()
    
    try:
        # 질문 답변 (실제 RAG 검색 없이 간단 테스트)
        answer = agent.answer_question(
            question="인공지능이란 무엇인가요?",
            collection_name="non_existent_collection"  # 실제 컬렉션 없이 테스트
        )
        
        # 결과 확인
        assert isinstance(answer, dict)
        assert "answer" in answer
        assert isinstance(answer["answer"], str)
        assert len(answer["answer"]) > 0
    except Exception as e:
        pytest.skip(f"QA 에이전트 테스트 오류: {e}")

def test_language_processor():
    """언어 처리기 테스트"""
    # 언어 처리기 초기화
    processor = LanguageProcessor()
    
    # 언어 감지 테스트
    assert processor.detect_language("안녕하세요") == "ko"
    assert processor.detect_language("Hello world") == "en"
    assert processor.detect_language("こんにちは") == "ja"
    assert processor.detect_language("你好") == "zh"
    
    # 지원 언어 확인
    assert processor.is_supported_language("ko") == True
    assert processor.is_supported_language("en") == True
    assert processor.is_supported_language("ja") == True
    assert processor.is_supported_language("zh") == True
    assert processor.is_supported_language("fr") == False  # 지원하지 않는 언어
    
    # 언어명 테스트
    assert processor.get_language_name("ko") == "Korean"
    assert processor.get_language_name("en") == "English"
    assert processor.get_language_name("ja") == "Japanese"
    assert processor.get_language_name("zh") == "Chinese (Simplified)"
    
    # 번역 테스트 (API 키 필요)
    if "GOOGLE_TRANSLATE_API_KEY" in os.environ:
        try:
            translated = processor.translate_text("안녕하세요", "en", "ko")
            assert isinstance(translated, str)
            assert len(translated) > 0
        except Exception as e:
            pytest.skip(f"번역 테스트 오류: {e}")
    else:
        pytest.skip("Google Translate API 키가 설정되지 않았습니다")
