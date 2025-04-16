# app/audio/tts.py
# Text-to-Speech - 텍스트를 음성으로 변환하는 기능

import os
from typing import Dict, List, Any, Optional, Union
import logging
import json
from pathlib import Path
import time

from app.llm.ai.openai_client import get_openai_client, get_language_voice
from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSProcessor:
    """텍스트를 음성으로 변환하는 프로세서"""
    
    def __init__(self, output_dir: str = settings.AUDIO_DIR):
        """
        초기화
        
        Args:
            output_dir: 오디오 파일 출력 디렉토리
        """
        self.openai_client = get_openai_client()
        self.output_dir = output_dir
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
    
    def text_to_speech(
        self, 
        text: str, 
        output_filename: Optional[str] = None, 
        voice: str = "alloy",
        language: str = "en",
        speed: float = 1.0
    ) -> str:
        """
        텍스트를 음성으로 변환하고 파일로 저장
        
        Args:
            text: 변환할 텍스트
            output_filename: 출력 파일 이름 (None이면 자동 생성)
            voice: 음성 (alloy, echo, fable, onyx, nova, shimmer)
            language: 언어 코드
            speed: 음성 속도 (0.25~4.0)
        
        Returns:
            생성된 오디오 파일 경로
        """
        try:
            # 언어에 맞는 음성 선택 (파라미터로 받은 voice가 우선)
            if voice == "auto":
                voice = get_language_voice(language)
            
            # 출력 파일 이름이 없으면 자동 생성
            if output_filename is None:
                timestamp = int(time.time())
                output_filename = f"tts_{language}_{voice}_{timestamp}.mp3"
            
            # 확장자가 없으면 mp3 추가
            if not output_filename.lower().endswith(('.mp3', '.opus', '.aac', '.flac')):
                output_filename += ".mp3"
            
            # 절대 경로 구성
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 텍스트가 너무 길면 분할
            max_chars = 4000  # OpenAI TTS API 제한
            
            if len(text) <= max_chars:
                # 단일 요청으로 처리 가능한 경우
                audio_data = self.openai_client.text_to_speech(
                    text=text,
                    voice=voice,
                    output_format="mp3",
                    speed=speed
                )
                
                # 오디오 파일 저장
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                logger.info(f"TTS 변환 완료: {output_path} ({len(audio_data)} 바이트)")
                return output_path
            else:
                # 텍스트가 너무 길면 분할 처리
                return self._process_long_text(text, output_path, voice, speed)
        except Exception as e:
            logger.error(f"TTS 변환 실패: {str(e)}")
            raise
    
    def _process_long_text(self, text: str, output_path: str, voice: str, speed: float) -> str:
        """
        긴 텍스트를 분할 처리
        
        Args:
            text: 변환할 텍스트
            output_path: 최종 출력 파일 경로
            voice: 음성
            speed: 음성 속도
        
        Returns:
            생성된 오디오 파일 경로
        """
        try:
            import tempfile
            from pydub import AudioSegment
            
            # 텍스트를 문장 단위로 분할
            sentences = self._split_into_sentences(text)
            
            # 청크 생성 (각 청크는 4000자 이하)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                # 현재 청크에 문장 추가했을 때 4000자를 넘지 않으면 추가
                if len(current_chunk) + len(sentence) <= 4000:
                    current_chunk += sentence
                else:
                    # 청크 추가하고 새 청크 시작
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            
            # 마지막 청크 추가
            if current_chunk:
                chunks.append(current_chunk)
            
            # 임시 파일들을 저장할 리스트
            temp_files = []
            
            # 각 청크 처리
            for i, chunk in enumerate(chunks):
                # 청크 변환
                audio_data = self.openai_client.text_to_speech(
                    text=chunk,
                    voice=voice,
                    output_format="mp3",
                    speed=speed
                )
                
                # 임시 파일에 저장
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(audio_data)
                    temp_files.append(tmp.name)
                
                logger.info(f"청크 {i+1}/{len(chunks)} 변환 완료 ({len(audio_data)} 바이트)")
            
            # 모든 임시 파일을 병합
            combined = AudioSegment.empty()
            for temp_file in temp_files:
                segment = AudioSegment.from_mp3(temp_file)
                combined += segment
            
            # 최종 파일 저장
            combined.export(output_path, format="mp3")
            
            # 임시 파일 삭제
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            logger.info(f"긴 텍스트 TTS 변환 완료: {output_path} ({len(chunks)} 청크)")
            return output_path
        except Exception as e:
            logger.error(f"긴 텍스트 TTS 변환 실패: {str(e)}")
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 분할
        
        Args:
            text: 분할할 텍스트
        
        Returns:
            문장 리스트
        """
        import re
        
        # 기본 문장 구분자로 분할
        sentence_delimiters = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_delimiters, text)
        
        # 문장 끝에 구분자 추가 (마지막 문장 제외)
        result = []
        for i, sentence in enumerate(sentences):
            if i < len(sentences) - 1:
                # 다음 문장의 시작 부분을 검사하여 구분자 결정
                next_start = sentences[i+1][:1] if i+1 < len(sentences) and sentences[i+1] else ""
                
                # 마침표 추가
                if not sentence.endswith(('.', '!', '?')):
                    sentence += '.'
                
                # 띄어쓰기 추가
                if next_start and not next_start.isspace():
                    sentence += ' '
            
            result.append(sentence)
        
        return result
    
    def generate_script_audio(
        self, 
        scripts: List[Dict[str, Any]], 
        language: str = "en",
        voice: str = "auto",
        speed: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        스크립트 리스트를 오디오로 변환
        
        Args:
            scripts: 스크립트 리스트 (페이지 번호와 스크립트 텍스트 포함)
            language: 언어 코드
            voice: 음성 (auto이면 언어에 맞게 자동 선택)
            speed: 음성 속도
        
        Returns:
            오디오 파일 정보 리스트
        """
        try:
            # 음성 선택 확인
            if voice == "auto":
                voice = get_language_voice(language)

            # 전체 텍스트를 하나로 합치기
            combined_text = ""
            page_numbers = []
            
            for script_data in scripts:
                page_number = script_data.get("page_number", 0)
                script_text = script_data.get("script", "")
                
                if not script_text:
                    logger.warning(f"페이지 {page_number}의 스크립트가 비어 있습니다")
                    continue
                
                # 페이지 번호 추가
                page_numbers.append(page_number)
                
                # 텍스트 사이에 간격 추가
                if combined_text:
                    combined_text += " "
                
                combined_text += script_text
            
            if not combined_text:
                logger.warning("변환할 스크립트가 없습니다")
                return []
            
            # 출력 파일명 생성 - 모든 페이지를 포함
            timestamp = int(time.time())
            # 사용한 페이지 번호 표시 (최대 3개까지만 표시, 그 이상은 ...으로 표시)
            pages_str = "_".join(str(p) for p in page_numbers[:3])
            if len(page_numbers) > 3:
                pages_str += "_etc"
                
            output_filename = f"lecture_pages_{pages_str}_{language}_{timestamp}.mp3"
            
            # TTS 변환 - 하나의 파일로 생성
            audio_path = self.text_to_speech(
                text=combined_text,
                output_filename=output_filename,
                voice=voice,
                language=language,
                speed=speed
            )
            
            # 결과 목록에 하나의 항목만 추가
            result = [{
                "pages": page_numbers,
                "audio_path": audio_path,
                "language": language,
                "voice": voice
            }]
            
            logger.info(f"스크립트 {len(page_numbers)}개 페이지를 하나의 오디오로 변환 완료: {audio_path}")
            return result
            
        except Exception as e:
            logger.error(f"스크립트 오디오 생성 실패: {str(e)}")
            return []


def get_tts_processor() -> TTSProcessor:
    """
    TTSProcessor 인스턴스 가져오기 헬퍼 함수
    
    Returns:
        TTSProcessor 인스턴스
    """
    return TTSProcessor()


def text_to_speech_file(
    text: str, 
    output_filename: Optional[str] = None, 
    voice: str = "alloy",
    language: str = "en",
    speed: float = 1.0
) -> str:
    """
    텍스트를 음성으로 변환하고 파일로 저장하는 헬퍼 함수
    
    Args:
        text: 변환할 텍스트
        output_filename: 출력 파일 이름
        voice: 음성
        language: 언어 코드
        speed: 음성 속도
    
    Returns:
        생성된 오디오 파일 경로
    """
    processor = get_tts_processor()
    return processor.text_to_speech(text, output_filename, voice, language, speed)