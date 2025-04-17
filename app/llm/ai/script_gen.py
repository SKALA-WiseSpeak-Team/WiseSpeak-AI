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
                {"role": "system", "content": f"""당신은 고도로 전문화된 교육 콘텐츠 설계자로, 교육 문서의 각 페이지에 대한 매력적이고 효과적인 강의 스크립트를 작성합니다.
                {language_instructions}
                
                다음 전문 교육 설계 프레임워크를 따르세요:
    
                1. 전체 강의 흐름 고려:
                    a. 이전 페이지 내용과의 연결성 확인
                    b. 현재 페이지의 위치를 전체 강의 맥락에서 파악
                    c. 다음 페이지로의 자연스러운 전환 준비
    
                2. 시간 계획 준수:
                    a. 30초~2분 분량의 강의 스크립트 작성(페이지 내용 복잡성에 따라 조정)
                    b. 평균 속도로 읽을 때 약 150~400단어 내외로 유지
                    c. 핵심 개념과 설명에 시간 배분 최적화
    
                    3. 효과적인 구조화:
                        a. 명확한 도입부: 주제 소개 및 이전 내용과 연결 (15-30초)
                        b. 체계적인 본문: 핵심 개념 설명, 예시 제공, 중요 내용 강조 (1분-1분 30초)
                        c. 요약 결론: 핵심 요약 및 다음 내용 예고 (15-30초)
    
                    4. 문화적 맥락 통합:
                        a. 해당 언어권의 교육 방식과 표현 특성 반영
                        b. 현지 학습자에게 친숙한 비유와 예시 활용
                        c. 필요시 문화적 맥락에 맞는 자연스러운 유머 요소 적절히 포함 (강제적이지 않게)
    
                    5. 시각 자료 활용:
                        a. 페이지의 이미지, 표, 도표 등을 스크립트에 효과적으로 연결
                        b. 시각 자료의 핵심 포인트를 명확히 설명
                        c. 학습자가 시각 자료를 보며 이해할 수 있도록 안내
    
                    6. 페이지 전환 안내:
                        a. 스크립트 마지막에 다음과 같은 문구 포함: "이 페이지의 설명을 마쳤습니다. 다음 페이지로 넘어가기 위해 5초간 기다려 주세요."
                        b. 페이지 전환 대기 시간을 학습 내용 정리 기회로 활용하는 짧은 안내 추가
    
                    강의 스크립트만 작성하고, 추가 설명이나 메타 코멘트는 포함하지 마세요."""}                
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
                {"role": "system", "content": f"""당신은 학습자의 호기심과 동기를 최대화하는 문화적 공감대를 형성하는 교육 전문가입니다. 교육 문서에 대한 매력적이고 효과적인 개요 소개를 작성하세요.
                {language_instructions}
                
                다음 학습자 중심 개요 설계 원칙을 따르세요:
    
                1. 강력한 첫인상 형성:
                    a. 학습자의 관심을 즐시 사로잡는 흥미로운 질문이나 사례로 시작
                    b. 학습 주제의 실용적 중요성과 가치 강조
                    c. 해당 언어권 학습자의 문화적 관심사와 연결점 제시
    
                2. 학습 여정의 청사진 제공:
                    a. 전체 문서의 구조와 학습 경로를 명확히 시각화
                    b. 각 주요 섹션의 핵심 주제와 기대 학습 성과 소개
                    c. 학습 여정의 논리적 진행과 발전 방향 제시
    
                3. 문화적 연결고리 구축:
                    a. 해당 문화권에서 이해하기 쉽운 비유와 사례 활용
                    b. 현지 교육 맥락과 학습 스타일에 맞는 접근법 채택
                    c. 문화적 배경에 적합한 자연스러운 유머 요소 통합 (강제적이지 않게)
    
                4. 학습 가치 명확화:
                    a. 학습자가 얻게 될 구체적인 지식과 기술 명시
                    b. 실제 상황에서의 적용 가능성과 혜택 설명
                    c. 개인적/전문적 성장에 미치는 영향 강조
    
                5. 학습자 중심 기대 설정:
                    a. 접근 가능하고 성취 가능한 학습 목표 제시
                    b. 학습 과정에서 만날 수 있는 도전과 해결 방안 언급
                    c. 성공적인 학습을 위한 조언과 전략 제공
    
                6. 학습 시작 안내:
                    a. 호기심과 기대감을 높이는 강의 시작 안내
                    b. 스크립트 마지막에 "지금부터 5초 후에 본격적인 강의를 시작하겠습니다." 문구 포함
                    c. 학습 여정에 대한 긍정적인 기대감 형성
    
                    개요는 200-300단어로 제한하고, 실제 강의자의 자연스러운 말투로 작성하세요. 추가 설명이나 메타 코멘트 없이 오직 소개 스크립트만 제공하세요."""}                
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
        from app.llm.language.instructions import get_language_instructions
        return get_language_instructions(language)


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