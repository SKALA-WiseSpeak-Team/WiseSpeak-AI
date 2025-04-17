# app/ai/script_gen.py
# 스크립트 생성 로직 - 페이지별 강의 스크립트 생성

import os
from typing import Dict, List, Any, Optional, Union
import logging
import json
from pathlib import Path

from app.llm.ai.openai_client import get_openai_client
from app.llm.vector_db.embeddings import get_embedder, chunk_document
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """강의 스크립트 생성 클래스"""
    
    def __init__(self, namespace: str = "default"):
        """
        초기화
        
        Args:
            namespace: 벡터 DB 네임스페이스
        """
        self.openai_client = get_openai_client()
        self.embedder = get_embedder()
        self.namespace = namespace
    
    def generate_page_script(self, page_data: Dict[str, Any], language: str = "en") -> str:
        """
        페이지 데이터를 기반으로 강의 스크립트 생성
        
        Args:
            page_data: 페이지 데이터
            language: 언어 코드 (예: 'en', 'ko')
        
        Returns:
            생성된 스크립트
        """
        try:
            # 페이지 데이터에서 필요한 정보 추출
            page_number = page_data.get("page_number", 0)
            text = page_data.get("text", "")
            titles = page_data.get("titles", [])
            subtitles = page_data.get("subtitles", [])
            tables = page_data.get("tables", [])
            has_image = page_data.get("has_image", False)
            
            # 가장 관련성 높은 벡터 DB 데이터 검색
            similar_docs = []
            if text:
                similar_docs = self.embedder.query_similar(text[:1000], n_results=3, namespace=self.namespace)
            
            # 표 텍스트 추출
            table_text = ""
            for table in tables:
                table_rows = []
                for row in table:
                    table_rows.append(" | ".join(row))
                table_text += "\n".join(table_rows) + "\n\n"
            
            # 페이지 정보 요약
            newline = '\n'  # 백슬래시 문제 해결을 위해 변수 사용
            page_summary = f"Page {page_number}"
            if titles:
                page_summary += f"{newline}Main title: {titles[0]}"
            if subtitles:
                page_summary += f"{newline}Subtitles: {', '.join(subtitles[:3])}"
            if has_image:
                page_summary += f"{newline}This page contains images"
            if tables:
                page_summary += f"{newline}This page contains {len(tables)} tables"
            
            # 컨텍스트 구성
            table_content = f'Table content:{newline}{table_text}' if table_text else ''
            
            related_info = ''
            if similar_docs:
                related_info = 'Related information from previous knowledge:' 
                for doc in similar_docs:
                    related_info += f"{newline}- {doc['text'][:300]}..."
            
            context = f"""
            {page_summary}
            
            Page content:
            {text}
            
            {table_content}
            
            {related_info}
            """
            
            # 프롬프트 준비 (언어에 따라 다르게)
            language_instructions = self._get_language_instructions(language)
            
            prompt = [
                {"role": "system", "content": f"""You are an expert educator who creates professional lecture scripts. 
                Your task is to create an engaging and informative lecture script for a specific page from an educational document.
                {language_instructions}
                
                Follow these guidelines:
                1. Focus on the main topics and concepts presented on this page
                2. Explain complex ideas clearly and provide context
                3. Refer to any images, tables, or diagrams that are mentioned on the page
                4. Structure the lecture in a logical flow
                5. Use an engaging, educational tone
                6. Keep the script concise but comprehensive
                7. The script should be between 300-500 words
                
                Create only the lecture script, without any additional explanations or meta-commentary."""}
            ]
            
            # 페이지 컨텍스트 추가
            newline = '\n'
            user_content = f"Here is the content for page {page_number}:{newline}{newline}{context}{newline}{newline}Please create a lecture script for this page."
            prompt.append({"role": "user", "content": user_content})
            
            # OpenAI API 호출
            response = self.openai_client.chat_completion(
                messages=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            script = response.get("text", "")
            logger.info(f"페이지 {page_number} 스크립트 생성 완료: {len(script)} 자")
            
            return script
        except Exception as e:
            logger.error(f"스크립트 생성 실패: {str(e)}")
            return f"Script generation error for page {page_data.get('page_number', 0)}: {str(e)}"
    
    def generate_full_script(self, parsed_document: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        문서 전체에 대한 강의 스크립트 생성
        
        Args:
            parsed_document: 파싱된 문서 데이터
            language: 언어 코드
        
        Returns:
            페이지별 스크립트를 포함한 결과 딕셔너리
        """
        try:
            filename = parsed_document.get("filename", "document")
            pages = parsed_document.get("pages", [])
            
            # 결과 구성
            result = {
                "filename": filename,
                "language": language,
                "page_count": len(pages),
                "page_scripts": []
            }
            
            # 각 페이지별 스크립트 생성
            all_scripts = []
            for page_data in pages:
                page_number = page_data.get("page_number", 0)
                script = self.generate_page_script(page_data, language)
                
                result["page_scripts"].append({
                    "page_number": page_number,
                    "script": script
                })
                all_scripts.append(script)
            
            # 모든 페이지 스크립트를 하나로 연결
            full_script = "\n\n".join(all_scripts)
            result["full_script"] = full_script
            
            return result
        except Exception as e:
            logger.error(f"전체 스크립트 생성 실패: {str(e)}")
            return {"filename": parsed_document.get("filename", "document"), "language": language, "page_count": 0, "page_scripts": [], "full_script": f"Error: {str(e)}"}
            
    def _generate_document_overview(self, parsed_document: Dict[str, Any], language: str = "en") -> str:
        """
        문서 전체에 대한 개요 생성
        
        Args:
            parsed_document: 파싱된 문서 데이터
            language: 언어 코드
        
        Returns:
            문서 개요 스크립트
        """
        try:
            filename = parsed_document.get("filename", "document")
            pages = parsed_document.get("pages", [])
            document_structure = parsed_document.get("document_structure", {})
            
            # 문서 제목 추출
            main_title = document_structure.get("main_title", filename)
            
            # 섹션 정보 추출
            sections = document_structure.get("sections", [])
            newline = '\n'
            section_info_items = []
            for section in sections[:5]:
                section_info_items.append(f"- {section.get('title', 'Section')} (Page {section.get('page', '?')})")
            section_info = newline.join(section_info_items)
            
            # 첫 번째 페이지 텍스트 (요약용)
            first_page_text = pages[0].get("text", "") if pages else ""
            
            # 컨텍스트 구성
            context = f"""
            Document: {filename}
            Main Title: {main_title}
            
            Main Sections:
            {section_info}
            
            Document introduction:
            {first_page_text[:500]}...
            """
            
            # 프롬프트 준비 (언어에 따라 다르게)
            language_instructions = self._get_language_instructions(language)
            
            prompt = [
                {"role": "system", "content": f"""You are an expert educator who creates professional lecture introductions.
                Your task is to create an engaging overview introduction for an educational document.
                {language_instructions}
                
                Follow these guidelines:
                1. Create a clear and engaging introduction to the document/lecture
                2. Mention the main topics that will be covered
                3. Explain why this content is important or relevant
                4. Set expectations for what learners will gain
                5. Keep the introduction between 200-300 words
                
                Create only the introduction script, without any additional explanations or meta-commentary."""}
            ]
            
            # 문서 컨텍스트 추가
            user_content = f"Here is information about the document:{newline}{newline}{context}{newline}{newline}Please create an engaging introduction script for this document/lecture."
            prompt.append({"role": "user", "content": user_content})
            
            # OpenAI API 호출
            response = self.openai_client.chat_completion(
                messages=prompt,
                temperature=0.7,
                max_tokens=600
            )
            
            script = response.get("text", "")
            logger.info(f"문서 개요 생성 완료: {len(script)} 자")
            
            return script
        except Exception as e:
            logger.error(f"문서 개요 생성 실패: {str(e)}")
            return f"Overview generation error: {str(e)}"
    
    def _get_language_instructions(self, language: str) -> str:
        """
        언어별 지침 생성
        
        Args:
            language: 언어 코드
        
        Returns:
            언어 지침
        """
        language = language.lower()
        
        # 지원하지 않는 언어인 경우 영어로 기본 설정
        if language not in settings.SUPPORTED_LANGUAGES:
            logger.warning(f"지원하지 않는 언어: {language}, 영어로 대체합니다")
            language = "en"
        
        instructions = {
            "en": "Create the script in English using natural, clear language.",
            "ko": "Create the script in Korean (한국어). Use natural, idiomatic Korean expressions.",
            "ja": "Create the script in Japanese (日本語). Use natural, idiomatic Japanese expressions.",
            "zh": "Create the script in Chinese (中文). Use natural, idiomatic Chinese expressions.",
            "es": "Create the script in Spanish. Use natural, idiomatic Spanish expressions.",
            "fr": "Create the script in French. Use natural, idiomatic French expressions.",
            "de": "Create the script in German. Use natural, idiomatic German expressions."
        }
        
        return instructions.get(language, instructions["en"])


def generate_script(parsed_document: Dict[str, Any], language: str = "en", namespace: str = "default") -> Dict[str, Any]:
    """
    강의 스크립트 생성 헬퍼 함수
    
    Args:
        parsed_document: 파싱된 문서 데이터
        language: 언어 코드
        namespace: 벡터 DB 네임스페이스
    
    Returns:
        생성된 스크립트 데이터
    """
    generator = ScriptGenerator(namespace)
    return generator.generate_full_script(parsed_document, language)