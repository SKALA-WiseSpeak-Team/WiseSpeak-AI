"""
질의응답 Agent
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
import re
import os
from pathlib import Path

from ..config import config
from ..utils.logger import get_logger
from ..services.openai_service import OpenAIService
from ..rag.rag_engine import RAGEngine
from ..processors.language.language_processor import LanguageProcessor

# 음성 서비스 임포트 (추가)
from ..services.speech.stt_service import STTService
from ..services.speech.tts_service import TTSService

logger = get_logger(__name__)

class QAAgent:
    """질의응답 Agent 클래스"""
    
    def __init__(self, 
                openai_service: Optional[OpenAIService] = None,
                rag_engine: Optional[RAGEngine] = None,
                language_processor: Optional[LanguageProcessor] = None,
                stt_service: Optional[STTService] = None,
                tts_service: Optional[TTSService] = None):
        """질의응답 Agent 초기화
        
        Args:
            openai_service (Optional[OpenAIService], optional): OpenAI 서비스 객체
            rag_engine (Optional[RAGEngine], optional): RAG 엔진 객체
            language_processor (Optional[LanguageProcessor], optional): 언어 처리 객체
            stt_service (Optional[STTService], optional): STT 서비스 객체
            tts_service (Optional[TTSService], optional): TTS 서비스 객체
        """
        self.openai_service = openai_service or OpenAIService()
        self.rag_engine = rag_engine or RAGEngine()
        self.language_processor = language_processor or LanguageProcessor()
        self.stt_service = stt_service or STTService()
        self.tts_service = tts_service or TTSService()
        
        logger.info("질의응답 Agent 초기화 완료")
    
    def answer_question(self, 
                    question: str, 
                    collection_name: str,
                    document_id: Optional[str] = None,
                    conversation_history: Optional[List[Dict[str, str]]] = None,
                    stream: bool = False) -> Union[Dict[str, Any], Any]:
        """사용자 질문에 답변
        
        Args:
            question (str): 사용자 질문
            collection_name (str): 벡터 DB 컬렉션 이름
            document_id (Optional[str], optional): 문서 ID (필터링용)
            conversation_history (Optional[List[Dict[str, str]]], optional): 대화 이력
            stream (bool, optional): 스트리밍 응답 여부
        
        Returns:
            Union[Dict[str, Any], Any]: 답변 정보 또는 스트림 객체
        """
        try:
            # 언어 감지
            question_language = self.language_processor.detect_language(question)
            logger.info(f"질문 언어 감지: {question_language}")
            
            # 메타데이터 필터링 조건
            filter_metadata = {}
            if document_id:
                filter_metadata["document_id"] = document_id
            
            # RAG 검색
            rag_results = self.rag_engine.retrieve(
                query=question,
                collection_name=collection_name,
                filter_metadata=filter_metadata,
                n_results=5
            )
            
            # 컨텍스트 준비
            contexts = []
            for result in rag_results:
                document = result.get("document", "")
                metadata = result.get("metadata", {})
                
                # 페이지 정보 추가
                page_num = metadata.get("page_number", "알 수 없음")
                contexts.append(f"[페이지 {page_num}]\n{document}")
            
            combined_context = "\n\n---\n\n".join(contexts)
            
            # 대화 이력 처리
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # 최대 5개의 최근 대화만 포함
                recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                
                history_texts = []
                for entry in recent_history:
                    if "user" in entry:
                        history_texts.append(f"사용자: {entry['user']}")
                    if "assistant" in entry:
                        history_texts.append(f"어시스턴트: {entry['assistant']}")
                
                conversation_context = "최근 대화 이력:\n" + "\n".join(history_texts)
            
            # 시스템 메시지 생성
            system_message = (
                "당신은 학습 자료에 대한 질의응답을 도와주는 챗봇입니다. "
                "주어진 컨텍스트를 바탕으로 사용자의 질문에 정확하게 답변하세요. "
                "컨텍스트에 없는 내용은 '제공된 자료에서 해당 정보를 찾을 수 없습니다'라고 답변하세요. "
                "답변은 친절하고 도움이 되도록 작성하세요."
            )
            
            # 프롬프트 생성
            prompt = ""
            
            # 대화 이력 추가
            if conversation_context:
                prompt += f"{conversation_context}\n\n"
            
            # 컨텍스트 및 질문 추가
            prompt += (
                f"컨텍스트:\n{combined_context}\n\n"
                f"사용자: {question}\n\n"
                f"어시스턴트:"
            )
            
            # 스트리밍 모드인 경우
            if stream:
                stream_response = self.openai_service.generate_text(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=0.7,
                    stream=True
                )
                
                return stream_response
            
            # 일반 응답 생성
            response = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            # 응답에서 출처 추출
            sources = self._extract_sources(response, rag_results)
            
            # 결과 반환
            result = {
                "question": question,
                "answer": response,
                "language": question_language,
                "sources": sources,
                "conversation_id": str(uuid.uuid4()) if not conversation_history else None
            }
            
            logger.info(f"질문 '{question[:30]}...'에 대한 답변 생성 완료")
            return result
        except Exception as e:
            logger.error(f"질문 답변 중 오류 발생: {e}")
            
            if stream:
                # 스트리밍 모드에서 오류 발생 시 오류 메시지 반환
                def error_stream():
                    yield f"답변 생성 중 오류가 발생했습니다: {str(e)}"
                
                return error_stream()
            
            return {
                "question": question,
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "language": self.language_processor.detect_language(question),
                "error": str(e)
            }
    
    def _extract_sources(self, 
                        response: str, 
                        rag_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """응답에서 출처 정보 추출
        
        Args:
            response (str): 생성된 응답
            rag_results (List[Dict[str, Any]]): RAG 검색 결과
        
        Returns:
            List[Dict[str, Any]]: 출처 정보
        """
        sources = []
        
        # 페이지 번호 매핑
        page_nums = set()
        for result in rag_results:
            metadata = result.get("metadata", {})
            page_num = metadata.get("page_number")
            if page_num is not None:
                page_nums.add(page_num)
        
        # 중복 제거 및 정렬
        page_nums = sorted(list(page_nums))
        
        # 각 페이지에 대한 출처 정보 생성
        for page_num in page_nums:
            # 해당 페이지의 결과 찾기
            matching_results = [
                res for res in rag_results 
                if res.get("metadata", {}).get("page_number") == page_num
            ]
            
            if not matching_results:
                continue
            
            # 첫 번째 매칭 결과 사용
            result = matching_results[0]
            metadata = result.get("metadata", {})
            
            source = {
                "page_number": page_num,
                "document_id": metadata.get("document_id", ""),
                "relevance": 1.0 - (result.get("distance", 0) if result.get("distance") is not None else 0)
            }
            
            sources.append(source)
        
        return sources
    
    def process_voice_input(self, 
                        transcription: str, 
                        collection_name: str,
                        document_id: Optional[str] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """음성 입력 처리
        
        Args:
            transcription (str): 음성 텍스트 변환 결과
            collection_name (str): 벡터 DB 컬렉션 이름
            document_id (Optional[str], optional): 문서 ID
            conversation_history (Optional[List[Dict[str, str]]], optional): 대화 이력
        
        Returns:
            Dict[str, Any]: 응답 정보
        """
        try:
            # 언어 감지
            input_language = self.language_processor.detect_language(transcription)
            logger.info(f"음성 입력 언어 감지: {input_language}")
            
            # 질문 여부 확인
            is_question = self._is_question(transcription, input_language)
            
            if not is_question:
                # 질문이 아닌 발화 처리
                system_message = (
                    "당신은 학습을 도와주는 챗봇입니다. "
                    "사용자의 발화가 질문이 아닌 경우에도 친절하게 대응하세요. "
                    "사용자가 도움이 필요한 것처럼 보이면 도움을 제안하세요."
                )
                
                prompt = f"사용자: {transcription}\n\n어시스턴트:"
                
                response = self.openai_service.generate_text(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=0.7
                )
                
                result = {
                    "input": transcription,
                    "answer": response,
                    "language": input_language,
                    "is_question": False,
                    "sources": []
                }
                
                logger.info(f"비질문 발화 '{transcription[:30]}...'에 대한 응답 생성 완료")
                return result
            
            # 질문으로 처리
            return self.answer_question(
                question=transcription,
                collection_name=collection_name,
                document_id=document_id,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.error(f"음성 입력 처리 중 오류 발생: {e}")
            return {
                "input": transcription,
                "answer": f"음성 입력 처리 중 오류가 발생했습니다: {str(e)}",
                "language": self.language_processor.detect_language(transcription),
                "is_question": False,
                "error": str(e)
            }
    
    def _is_question(self, text: str, language: str) -> bool:
        """텍스트가 질문인지 확인
        
        Args:
            text (str): 확인할 텍스트
            language (str): 텍스트 언어
        
        Returns:
            bool: 질문이면 True, 아니면 False
        """
        # 언어별 질문 패턴
        question_patterns = {
            "ko": r'[\?？]|\b(뭐|무엇|언제|어디|누구|어떻게|왜|어떤|얼마나|몇|까|나요|ㅂ니까)\b',
            "en": r'[\?？]|\b(what|when|where|who|how|why|which|whose|whom|can|could|would|will|should|do|does|did|is|are|was|were)\b',
            "ja": r'[\?？]|\b(何|誰|どこ|いつ|どのように|なぜ|どの|いくら|か)\b',
            "zh": r'[\?？]|\b(什么|谁|哪里|何时|如何|为什么|哪个|多少|吗|呢)\b'
        }
        
        # 해당 언어의 패턴이 없으면 기본 패턴 사용
        pattern = question_patterns.get(language, r'[\?？]')
        
        # 패턴 매칭
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def improve_query(self, query: str) -> str:
        """쿼리 개선
        
        Args:
            query (str): 원본 쿼리
        
        Returns:
            str: 개선된 쿼리
        """
        try:
            # 쿼리가 너무 짧거나 간단하면 개선하지 않음
            if len(query) < 10 or len(query.split()) < 3:
                return query
            
            # 시스템 메시지 생성
            system_message = (
                "당신은 검색 쿼리 최적화 전문가입니다. "
                "주어진 원본 쿼리를 검색에 더 효과적인 형태로 개선하세요. "
                "키워드를 추출하고, 불필요한 단어를 제거하고, 보다 구체적인 표현을 사용하세요. "
                "개선된 쿼리는 원본 의도를 유지하면서 검색 성능을 높여야 합니다."
            )
            
            # 프롬프트 생성
            prompt = (
                f"원본 쿼리: {query}\n\n"
                f"이 쿼리를 RAG 시스템에 더 효과적인 형태로 개선해주세요. "
                f"개선된 쿼리만 반환하세요."
            )
            
            # 개선된 쿼리 생성
            improved_query = self.openai_service.generate_text(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3
            )
            
            # 결과가 너무 길면 원본 사용
            if len(improved_query) > len(query) * 2:
                logger.warning(f"개선된 쿼리가 너무 깁니다. 원본 쿼리를 사용합니다.")
                return query
                
            logger.info(f"쿼리 개선: '{query}' -> '{improved_query}'")
            return improved_query.strip()
        except Exception as e:
            logger.error(f"쿼리 개선 중 오류 발생: {e}")
            return query
    
    # 새로 추가된 메소드 (오디오 처리)
    def process_audio_file(self, 
                        audio_file_path: str, 
                        collection_name: str,
                        document_id: Optional[str] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        generate_audio_response: bool = False,
                        voice: str = "nova") -> Dict[str, Any]:
        """오디오 파일을 처리하여 응답 생성
        
        Args:
            audio_file_path (str): 오디오 파일 경로
            collection_name (str): 벡터 DB 컬렉션 이름
            document_id (Optional[str], optional): 문서 ID
            conversation_history (Optional[List[Dict[str, str]]], optional): 대화 이력
            generate_audio_response (bool, optional): 오디오 응답 생성 여부
            voice (str, optional): TTS 음성 종류
        
        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            logger.info(f"오디오 파일 처리 중: {audio_file_path}")
            
            # 오디오를 텍스트로 변환
            transcription = self.stt_service.transcribe_audio(audio_file_path)
            
            if not transcription:
                logger.error("오디오 변환 실패")
                return {
                    "error": "오디오를 텍스트로 변환하지 못했습니다."
                }
            
            logger.info(f"오디오 변환 결과: {transcription}")
            
            # 텍스트로 변환된 입력 처리
            result = self.process_voice_input(
                transcription=transcription,
                collection_name=collection_name,
                document_id=document_id,
                conversation_history=conversation_history
            )
            
            # 오디오 응답 생성 (선택적)
            if generate_audio_response and "answer" in result:
                logger.info("응답 오디오 생성 중...")
                audio_path = self.tts_service.generate_speech(
                    text=result["answer"],
                    filename=f"response_{uuid.uuid4().hex[:8]}"
                )
                
                if audio_path:
                    result["audio_response_path"] = audio_path
                    logger.info(f"응답 오디오 생성 완료: {audio_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"오디오 파일 처리 중 오류 발생: {e}")
            return {
                "error": str(e)
            }
    
    def record_and_process(self, 
                        collection_name: str,
                        document_id: Optional[str] = None,
                        conversation_history: Optional[List[Dict[str, str]]] = None,
                        duration: int = 5,
                        detect_speech: bool = True,
                        generate_audio_response: bool = False,
                        voice: str = "nova") -> Dict[str, Any]:
        """음성 녹음 후 처리
        
        Args:
            collection_name (str): 벡터 DB 컬렉션 이름
            document_id (Optional[str], optional): 문서 ID
            conversation_history (Optional[List[Dict[str, str]]], optional): 대화 이력
            duration (int, optional): 녹음 시간(초)
            detect_speech (bool, optional): 음성 감지 모드 사용 여부
            generate_audio_response (bool, optional): 오디오 응답 생성 여부
            voice (str, optional): TTS 음성 종류
        
        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            logger.info("음성 녹음 시작...")
            
            # 음성 녹음
            recording = self.stt_service.record_audio(
                duration=duration,
                detect_speech=detect_speech
            )
            
            if not recording:
                logger.error("녹음 실패")
                return {
                    "error": "녹음에 실패했습니다."
                }
            
            # 녹음 결과 처리
            audio_file_path = recording["file_path"]
            transcription = recording["transcription"]
            
            if not transcription:
                logger.error("음성 인식 실패")
                return {
                    "recording": recording,
                    "error": "음성을 인식하지 못했습니다."
                }
            
            logger.info(f"음성 인식 결과: {transcription}")
            
            # 텍스트로 변환된 입력 처리
            result = self.process_voice_input(
                transcription=transcription,
                collection_name=collection_name,
                document_id=document_id,
                conversation_history=conversation_history
            )
            
            # 녹음 정보 추가
            result["recording"] = recording
            
            # 오디오 응답 생성 (선택적)
            if generate_audio_response and "answer" in result:
                logger.info("응답 오디오 생성 중...")
                audio_path = self.tts_service.generate_speech(
                    text=result["answer"],
                    filename=f"response_{uuid.uuid4().hex[:8]}"
                )
                
                if audio_path:
                    result["audio_response_path"] = audio_path
                    logger.info(f"응답 오디오 생성 완료: {audio_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"음성 녹음 및 처리 중 오류 발생: {e}")
            return {
                "error": str(e)
            }
    
    # 대화 이력 저장 기능 추가
    def save_conversation(self, 
                        conversation_history: List[Dict[str, str]], 
                        output_path: Optional[str] = None) -> str:
        """대화 이력을 JSON으로 저장
        
        Args:
            conversation_history (List[Dict[str, str]]): 대화 이력
            output_path (Optional[str], optional): 저장 경로
        
        Returns:
            str: 저장된 파일 경로
        """
        try:
            import json
            
            # 출력 경로 설정
            if not output_path:
                output_dir = Path(config.OUTPUT_DIR) / "conversations"
                os.makedirs(output_dir, exist_ok=True)
                
                file_id = str(uuid.uuid4())[:8]
                output_path = str(output_dir / f"conversation_{file_id}.json")
            
            # JSON으로 저장
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(conversation_history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"대화 이력이 저장되었습니다: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"대화 이력 저장 중 오류 발생: {e}")
            return ""
