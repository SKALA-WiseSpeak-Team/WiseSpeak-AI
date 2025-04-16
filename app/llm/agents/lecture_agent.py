"""
강의 스크립트 생성 Agent
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import json
import re
import os
from pathlib import Path

from ..config import config
from ..utils.logger import get_logger
from ..services.openai_service import OpenAIService
from ..rag.rag_engine import RAGEngine
from ..processors.language.language_processor import LanguageProcessor

# 음성 서비스 임포트 (추가)
from ..services.speech.tts_service import TTSService

logger = get_logger(__name__)

class LectureAgent:
    """강의 스크립트 생성 Agent 클래스"""
    
    def __init__(self, 
                openai_service: Optional[OpenAIService] = None,
                rag_engine: Optional[RAGEngine] = None,
                language_processor: Optional[LanguageProcessor] = None,
                tts_service: Optional[TTSService] = None):
        """강의 Agent 초기화
        
        Args:
            openai_service (Optional[OpenAIService], optional): OpenAI 서비스 객체
            rag_engine (Optional[RAGEngine], optional): RAG 엔진 객체
            language_processor (Optional[LanguageProcessor], optional): 언어 처리 객체
            tts_service (Optional[TTSService], optional): TTS 서비스 객체
        """
        self.openai_service = openai_service or OpenAIService()
        self.rag_engine = rag_engine or RAGEngine()
        self.language_processor = language_processor or LanguageProcessor()
        self.tts_service = tts_service or TTSService()
        
        logger.info("강의 스크립트 생성 Agent 초기화 완료")
    
    def generate_lecture_script(self, 
                            page_content: Dict[str, Any], 
                            collection_name: str,
                            lecture_title: str,
                            target_language: str = "ko",
                            style: str = "educational") -> Dict[str, Any]:
        """페이지 내용을 기반으로 강의 스크립트 생성
        
        Args:
            page_content (Dict[str, Any]): 페이지 내용 (텍스트, 이미지, 표 등)
            collection_name (str): 벡터 DB 컬렉션 이름
            lecture_title (str): 강의 제목
            target_language (str, optional): 대상 언어. 기본값은 "ko"
            style (str, optional): 강의 스타일 ('educational', 'conversational', 'formal'). 기본값은 "educational"
        
        Returns:
            Dict[str, Any]: 생성된 스크립트 정보
        """
        try:
            page_num = page_content.get("page_number", 0)
            page_text = page_content.get("text", "")
            
            # 표와 이미지 정보 추가
            tables = page_content.get("tables", [])
            images = page_content.get("images", [])
            
            logger.info(f"페이지 {page_num}의 강의 스크립트 생성 시작")
            
            # RAG 컨텍스트 검색
            filter_metadata = {"document_id": page_content.get("document_id")}
            rag_results = self.rag_engine.retrieve(
                query=f"강의: {lecture_title}, 페이지 {page_num}의 내용",
                collection_name=collection_name,
                filter_metadata=filter_metadata,
                n_results=3
            )
            
            # 컨텍스트 준비
            contexts = "\n\n".join([result["document"] for result in rag_results])
            
            # 표 정보 추가
            table_descriptions = []
            for i, table in enumerate(tables):
                table_text = f"표 {i+1}:\n{table}"
                table_descriptions.append(table_text)
            
            # 이미지 정보 추가
            image_descriptions = []
            for i, image in enumerate(images):
                image_content = image.get("content", "이미지")
                ocr_text = image.get("ocr_text", "")
                
                image_text = f"이미지 {i+1}: {image_content}"
                if ocr_text:
                    image_text += f"\n이미지 내 텍스트: {ocr_text}"
                
                image_descriptions.append(image_text)
            
            # 스타일에 따른 안내
            style_guide = {
                "educational": "교육적이고 명확한 설명 스타일. 전문 용어를 설명하고 개념을 잘 정의해주세요.",
                "conversational": "친근하고 대화체 스타일. 비유와 일상적인 예시를 활용하세요.",
                "formal": "격식 있고 학술적인 스타일. 정확한 표현과 엄밀한 용어를 사용하세요."
            }.get(style, "교육적이고 명확한 설명 스타일")
            
            # 시스템 메시지 생성
            system_message = (
                f"당신은 훌륭한 교육자이자 강의 스크립트 작성자입니다. "
                f"주어진 페이지 내용을 기반으로 {self.language_processor.get_language_name(target_language)} 강의 스크립트를 작성해주세요. "
                f"스크립트는 {style_guide} "
                f"내용은 PDF 페이지 텍스트, 표, 이미지 정보와 컨텍스트를 기반으로 작성하세요. "
                f"이미지나 표가 있다면 이에 대한 설명을 포함하세요. "
                f"학습자가 쉽게 이해할 수 있도록 명확하게 설명하세요."
            )
            
            # 프롬프트 생성
            prompt = (
                f"강의 제목: {lecture_title}\n"
                f"페이지 번호: {page_num}\n\n"
                f"페이지 내용:\n{page_text}\n\n"
            )
            
            # 표 정보 추가
            if table_descriptions:
                prompt += f"표 정보:\n" + "\n\n".join(table_descriptions) + "\n\n"
            
            # 이미지 정보 추가
            if image_descriptions:
                prompt += f"이미지 정보:\n" + "\n\n".join(image_descriptions) + "\n\n"
            
            # 추가 컨텍스트 추가
            if contexts:
                prompt += f"추가 컨텍스트:\n{contexts}\n\n"
            
            prompt += (
                f"위 내용을 기반으로, 이 페이지에 대한 강의 스크립트를 작성해주세요. "
                f"말하는 것처럼 자연스러운 문체로 작성하세요. "
                f"길이는 약 300~500단어 정도가 적당합니다."
            )
            
            # 스크립트 생성
            script = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            # 언어 변환 (필요한 경우)
            if target_language != "ko" and self.language_processor.detect_language(script) != target_language:
                script = self.language_processor.translate_text(script, target_language)
            
            # 결과 반환
            result = {
                "page_number": page_num,
                "script": script,
                "language": target_language,
                "word_count": len(re.findall(r'\w+', script)),
                "style": style
            }
            
            logger.info(f"페이지 {page_num}의 강의 스크립트 생성 완료 (약 {result['word_count']}단어)")
            return result
        except Exception as e:
            logger.error(f"강의 스크립트 생성 중 오류 발생: {e}")
            return {
                "page_number": page_content.get("page_number", 0),
                "script": f"스크립트 생성 중 오류가 발생했습니다: {str(e)}",
                "language": target_language,
                "error": str(e)
            }
    
    def generate_lecture_outline(self, 
                                document_content: Dict[int, str],
                                lecture_title: str,
                                lecture_description: Optional[str] = None,
                                target_language: str = "ko") -> Dict[str, Any]:
        """문서 전체를 기반으로 강의 개요 생성
        
        Args:
            document_content (Dict[int, str]): 페이지 번호를 키로 하는 문서 내용
            lecture_title (str): 강의 제목
            lecture_description (Optional[str], optional): 강의 설명
            target_language (str, optional): 대상 언어. 기본값은 "ko"
        
        Returns:
            Dict[str, Any]: 생성된 강의 개요
        """
        try:
            # 모든 페이지 내용을 결합
            combined_content = "\n\n--- 페이지 구분 ---\n\n".join(
                [f"페이지 {page_num}:\n{content}" for page_num, content in document_content.items()]
            )
            
            # 내용이 너무 길면 첫 페이지와 마지막 페이지 위주로 샘플링
            if len(combined_content) > 4000:
                # 페이지 번호 정렬
                page_nums = sorted(document_content.keys())
                
                # 첫 2페이지
                sampled_content = []
                
                # 첫 2페이지
                start_pages = page_nums[:min(2, len(page_nums))]
                for page_num in start_pages:
                    sampled_content.append(f"페이지 {page_num} (시작 부분):\n{document_content[page_num]}")
                
                # 중간 1페이지 (있는 경우)
                if len(page_nums) > 4:
                    mid_idx = len(page_nums) // 2
                    mid_page = page_nums[mid_idx]
                    sampled_content.append(f"페이지 {mid_page} (중간 부분):\n{document_content[mid_page]}")
                
                # 마지막 2페이지
                end_pages = page_nums[-2:] if len(page_nums) >= 2 else page_nums[-1:]
                for page_num in end_pages:
                    sampled_content.append(f"페이지 {page_num} (마지막 부분):\n{document_content[page_num]}")
                
                combined_content = "\n\n--- 페이지 구분 ---\n\n".join(sampled_content)
                
                # 샘플링 정보 추가
                combined_content = (
                    f"[참고: 이 문서는 총 {len(page_nums)}페이지이며, 내용이 너무 길어 일부 페이지만 샘플링했습니다.]\n\n" 
                    + combined_content
                )
            
            # 시스템 메시지 생성
            system_message = (
                f"당신은 교육 전문가이며 강의 개요 작성자입니다. "
                f"주어진 문서 내용을 분석하여 강의 개요를 생성해주세요. "
                f"개요는 {self.language_processor.get_language_name(target_language)}로 작성하고, 강의 목표, 핵심 주제, "
                f"학습 목표, 그리고 각 페이지별 주요 내용 요약을 포함해야 합니다. "
                f"문서의 실제 내용에 충실하게 개요를 작성하세요."
            )
            
            # 프롬프트 생성
            prompt = (
                f"강의 제목: {lecture_title}\n"
            )
            
            if lecture_description:
                prompt += f"강의 설명: {lecture_description}\n"
            
            prompt += (
                f"총 페이지 수: {len(document_content)}\n\n"
                f"문서 내용:\n{combined_content}\n\n"
                f"위 내용을 기반으로 다음 형식의 강의 개요를 작성해주세요:\n\n"
                f"1. 강의 개요 및 목표\n"
                f"2. 핵심 주제 (3-5개 항목)\n"
                f"3. 학습 목표 (학습자가 얻게 될 지식이나 기술)\n"
                f"4. 주요 내용 요약 (페이지별 주요 내용을 간략히 요약)\n"
                f"5. 강의 흐름 및 구조"
            )
            
            # 개요 생성
            outline = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            # 언어 변환 (필요한 경우)
            if target_language != "ko" and self.language_processor.detect_language(outline) != target_language:
                outline = self.language_processor.translate_text(outline, target_language)
            
            # 결과 반환
            result = {
                "title": lecture_title,
                "description": lecture_description,
                "outline": outline,
                "language": target_language,
                "total_pages": len(document_content)
            }
            
            logger.info(f"강의 '{lecture_title}'의 개요 생성 완료")
            return result
        except Exception as e:
            logger.error(f"강의 개요 생성 중 오류 발생: {e}")
            return {
                "title": lecture_title,
                "outline": f"개요 생성 중 오류가 발생했습니다: {str(e)}",
                "language": target_language,
                "error": str(e)
            }
    
    def generate_lecture_quiz(self, 
                            page_content: Dict[str, Any],
                            collection_name: str,
                            lecture_title: str,
                            num_questions: int = 3,
                            target_language: str = "ko") -> Dict[str, Any]:
        """페이지 내용을 기반으로 퀴즈 문제 생성
        
        Args:
            page_content (Dict[str, Any]): 페이지 내용
            collection_name (str): 벡터 DB 컬렉션 이름
            lecture_title (str): 강의 제목
            num_questions (int, optional): 생성할 문제 수. 기본값은 3
            target_language (str, optional): 대상 언어. 기본값은 "ko"
        
        Returns:
            Dict[str, Any]: 생성된 퀴즈 정보
        """
        try:
            page_num = page_content.get("page_number", 0)
            page_text = page_content.get("text", "")
            
            logger.info(f"페이지 {page_num}의 퀴즈 문제 {num_questions}개 생성 시작")
            
            # RAG 컨텍스트 검색
            filter_metadata = {"document_id": page_content.get("document_id")}
            rag_results = self.rag_engine.retrieve(
                query=f"강의: {lecture_title}, 페이지 {page_num}의 핵심 내용",
                collection_name=collection_name,
                filter_metadata=filter_metadata,
                n_results=3
            )
            
            # 컨텍스트 준비
            contexts = "\n\n".join([result["document"] for result in rag_results])
            
            # 시스템 메시지 생성
            system_message = (
                f"당신은 교육 평가 전문가입니다. "
                f"주어진 페이지 내용을 기반으로 {self.language_processor.get_language_name(target_language)} 퀴즈 문제를 작성해주세요. "
                f"각 문제는 페이지의 핵심 개념을 테스트해야 합니다. "
                f"문제는 다지선다형으로 작성하고, 각 문제에 대한 정답과 해설을 포함해야 합니다. "
                f"응답을 JSON 형식으로 제공하세요."
            )
            
            # 프롬프트 생성
            prompt = (
                f"강의 제목: {lecture_title}\n"
                f"페이지 번호: {page_num}\n\n"
                f"페이지 내용:\n{page_text}\n\n"
            )
            
            # 추가 컨텍스트 추가
            if contexts:
                prompt += f"추가 컨텍스트:\n{contexts}\n\n"
            
            prompt += (
                f"위 내용을 기반으로, 이 페이지에 대한 {num_questions}개의 퀴즈 문제를 작성해주세요. "
                f"각 문제는 다음 JSON 형식을 따라야 합니다:\n\n"
                f"{{\n"
                f"  \"questions\": [\n"
                f"    {{\n"
                f"      \"question\": \"문제 내용\",\n"
                f"      \"options\": [\"보기1\", \"보기2\", \"보기3\", \"보기4\"],\n"
                f"      \"answer\": \"정답 인덱스 (0부터 시작)\",\n"
                f"      \"explanation\": \"정답 해설\"\n"
                f"    }},\n"
                f"    ...\n"
                f"  ]\n"
                f"}}\n\n"
                f"페이지 내용에 충실하게 문제를 작성하고, 각 문제는 페이지의 핵심 개념을 테스트해야 합니다."
            )
            
            # 퀴즈 생성
            quiz_json = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            # JSON 파싱
            try:
                quiz_data = json.loads(quiz_json)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 정규식으로 추출 시도
                try:
                    json_match = re.search(r'(\{.*\})', quiz_json, re.DOTALL)
                    if json_match:
                        quiz_data = json.loads(json_match.group(1))
                    else:
                        raise ValueError("JSON 형식이 아닙니다")
                except Exception:
                    logger.error("JSON 추출 실패, 기본 포맷 사용")
                    quiz_data = {
                        "questions": [
                            {
                                "question": "퀴즈 생성 중 오류가 발생했습니다",
                                "options": ["오류", "오류", "오류", "오류"],
                                "answer": 0,
                                "explanation": "JSON 파싱 오류"
                            }
                        ]
                    }
            
            # 언어 변환 (필요한 경우)
            if target_language != "ko":
                questions = quiz_data.get("questions", [])
                for q in questions:
                    q["question"] = self.language_processor.translate_text(q["question"], target_language)
                    q["options"] = [
                        self.language_processor.translate_text(opt, target_language) 
                        for opt in q["options"]
                    ]
                    q["explanation"] = self.language_processor.translate_text(q["explanation"], target_language)
            
            # 결과 반환
            result = {
                "page_number": page_num,
                "quiz": quiz_data,
                "language": target_language,
                "lecture_title": lecture_title
            }
            
            logger.info(f"페이지 {page_num}의 퀴즈 문제 생성 완료 ({len(quiz_data.get('questions', []))}개 문제)")
            return result
        except Exception as e:
            logger.error(f"퀴즈 생성 중 오류 발생: {e}")
            return {
                "page_number": page_content.get("page_number", 0),
                "quiz": {
                    "questions": [
                        {
                            "question": f"퀴즈 생성 중 오류가 발생했습니다: {str(e)}",
                            "options": ["오류", "오류", "오류", "오류"],
                            "answer": 0,
                            "explanation": "오류 발생"
                        }
                    ]
                },
                "language": target_language,
                "error": str(e)
            }
    
    # 새로 추가된 메소드 (TTS 기능)
    def generate_lecture_audio(self, 
                            script_result: Dict[str, Any], 
                            output_format: str = "mp3",
                            voice: str = "nova") -> Dict[str, Any]:
        """강의 스크립트를 오디오로 변환
        
        Args:
            script_result (Dict[str, Any]): 스크립트 결과 (generate_lecture_script의 반환값)
            output_format (str, optional): 출력 파일 형식. 기본값은 "mp3"
            voice (str, optional): 음성 종류. 기본값은 "nova"
        
        Returns:
            Dict[str, Any]: 오디오 파일 정보가 추가된 결과
        """
        try:
            if "script" not in script_result:
                logger.error("스크립트가 없습니다")
                return script_result
            
            script = script_result["script"]
            page_num = script_result["page_number"]
            
            # 파일명 지정 (페이지 번호 포함)
            filename = f"lecture_page_{page_num}"
            
            logger.info(f"페이지 {page_num}의 스크립트를 오디오로 변환 중...")
            
            # TTS 변환
            audio_path = self.tts_service.generate_speech(
                text=script,
                output_format=output_format,
                filename=filename
            )
            
            if audio_path:
                # 결과에 오디오 정보 추가
                result = script_result.copy()
                result["audio_path"] = audio_path
                result["audio_format"] = output_format
                result["voice"] = voice
                
                logger.info(f"페이지 {page_num}의 오디오 생성 완료: {audio_path}")
                return result
            else:
                logger.error("오디오 생성 실패")
                script_result["audio_error"] = "오디오 생성에 실패했습니다"
                return script_result
                
        except Exception as e:
            logger.error(f"오디오 생성 중 오류 발생: {e}")
            script_result["audio_error"] = str(e)
            return script_result
    
    def generate_full_lecture(self, 
                            document_content: Dict[int, str],
                            document_id: str,
                            collection_name: str,
                            lecture_title: str,
                            lecture_description: Optional[str] = None,
                            target_language: str = "ko",
                            style: str = "educational",
                            generate_audio: bool = False,
                            audio_voice: str = "nova") -> Dict[str, Any]:
        """전체 강의 생성 (개요, 페이지별 스크립트, 오디오)
        
        Args:
            document_content (Dict[int, str]): 페이지 번호를 키로 하는 문서 내용
            document_id (str): 문서 ID
            collection_name (str): 벡터 DB 컬렉션 이름
            lecture_title (str): 강의 제목
            lecture_description (Optional[str], optional): 강의 설명
            target_language (str, optional): 대상 언어. 기본값은 "ko"
            style (str, optional): 강의 스타일. 기본값은 "educational"
            generate_audio (bool, optional): 오디오 생성 여부. 기본값은 False
            audio_voice (str, optional): 오디오 음성. 기본값은 "nova"
        
        Returns:
            Dict[str, Any]: 전체 강의 데이터
        """
        try:
            result = {
                "title": lecture_title,
                "description": lecture_description,
                "language": target_language,
                "style": style,
                "document_id": document_id,
                "total_pages": len(document_content)
            }
            
            # 1. 강의 개요 생성
            logger.info("1. 강의 개요 생성 중...")
            outline = self.generate_lecture_outline(
                document_content=document_content,
                lecture_title=lecture_title,
                lecture_description=lecture_description,
                target_language=target_language
            )
            result["outline"] = outline
            
            # 2. 페이지별 스크립트 생성
            logger.info("2. 페이지별 스크립트 생성 중...")
            page_scripts = {}
            
            for page_num, text in sorted(document_content.items()):
                logger.info(f"  - 페이지 {page_num}/{len(document_content)} 처리 중...")
                
                page_content = {
                    "page_number": page_num,
                    "text": text,
                    "document_id": document_id
                }
                
                script = self.generate_lecture_script(
                    page_content=page_content,
                    collection_name=collection_name,
                    lecture_title=lecture_title,
                    target_language=target_language,
                    style=style
                )
                
                # 3. 오디오 생성 (선택적)
                if generate_audio:
                    script = self.generate_lecture_audio(
                        script_result=script,
                        voice=audio_voice
                    )
                
                page_scripts[page_num] = script
            
            result["scripts"] = page_scripts
            
            # 4. 퀴즈 생성 (첫 페이지만)
            logger.info("4. 퀴즈 생성 중...")
            if document_content:
                first_page = min(document_content.keys())
                page_content = {
                    "page_number": first_page,
                    "text": document_content[first_page],
                    "document_id": document_id
                }
                
                quiz = self.generate_lecture_quiz(
                    page_content=page_content,
                    collection_name=collection_name,
                    lecture_title=lecture_title,
                    target_language=target_language
                )
                
                result["quiz"] = quiz
            
            logger.info(f"강의 '{lecture_title}' 생성 완료")
            return result
            
        except Exception as e:
            logger.error(f"전체 강의 생성 중 오류 발생: {e}")
            return {
                "title": lecture_title,
                "error": str(e)
            }
    
    # 강의 저장 메소드 추가
    def save_lecture_to_json(self, lecture_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """강의 데이터를 JSON으로 저장
        
        Args:
            lecture_data (Dict[str, Any]): 강의 데이터
            output_path (Optional[str], optional): 저장 경로. 기본값은 output/lectures 디렉토리
        
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 출력 경로 설정
            if not output_path:
                lecture_title = lecture_data.get("title", "unnamed_lecture")
                safe_title = re.sub(r'[^\w\s-]', '', lecture_title).strip().replace(' ', '_')
                output_dir = Path(config.OUTPUT_DIR) / "lectures"
                os.makedirs(output_dir, exist_ok=True)
                output_path = str(output_dir / f"{safe_title}.json")
            
            # JSON으로 저장
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lecture_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"강의 데이터가 JSON으로 저장되었습니다: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"강의 데이터 저장 중 오류 발생: {e}")
            return ""
