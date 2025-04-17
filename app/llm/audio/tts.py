# app/audio/tts.py
# Text-to-Speech - 텍스트를 음성으로 변환하는 기능

import os
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import json
from pathlib import Path
import time
import random
from enum import Enum

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
    
    def apply_speech_patterns(self, text: str, voice: str) -> Tuple[str, float]:
        """
        음성 패턴을 텍스트에 적용
        
        Args:
            text: 원본 텍스트
            voice: 음성 유형
        
        Returns:
            수정된 텍스트와 기본 속도 튜플
        """
        try:
            # 기본 속도 설정
            base_speed = 1.0
            voice_char = settings.VOICE_CHARACTERISTICS.get(voice, {})
            
            # TTS_SPEECH_PATTERNS에서 데이터 가져오기
            speed_variations = settings.TTS_SPEECH_PATTERNS.get("speed_variations", {})
            pause_patterns = settings.TTS_SPEECH_PATTERNS.get("pause_patterns", {})
            
            # 목소리 특성에 따른 기본 속도 조정
            role = voice_char.get("role", "")
            if "교수" in role or "원로" in role:
                # 교수 타입은 약간 느린 경향
                base_speed *= 0.95
            elif "퍼실리테이터" in role or "활기찬" in role:
                # 활기찬 타입은 약간 빠른 경향
                base_speed *= 1.05
            
            # 나이대에 따른 속도 조정
            age = voice_char.get("age", "")
            if age and age.endswith("대"):
                age_num = int(age[:-1])
                if age_num >= 50:
                    # 나이가 많을수록 느린 경향
                    base_speed *= 0.95
                elif age_num <= 30:
                    # 나이가 적을수록 빠른 경향
                    base_speed *= 1.05
            
            # 텍스트 내용 분석을 통한 속도 조정 패턴 적용
            # 1. 페이지 전환 안내 검색
            if "다음 페이지로 넘어가기 위해 5초간 기다려 주세요" in text or "지금부터 5초 후에 본격적인 강의를 시작하겠습니다" in text:
                page_transition_factor = speed_variations.get("page_transition", 0.8)
                base_speed *= page_transition_factor
                logger.info(f"페이지 전환 안내 발견: 속도 조정 적용 ({page_transition_factor})")
            
            # 2. 새로운 주제 도입 검색
            new_topic_keywords = ["이제 살펴볼 주제는", "다음 주제로", "이번에는", "이어서 살펴볼", "이번 주제는"]
            for keyword in new_topic_keywords:
                if keyword in text:
                    new_topic_factor = speed_variations.get("new_topic", 0.9)
                    base_speed *= new_topic_factor
                    logger.info(f"새로운 주제 도입 발견: 속도 조정 적용 ({new_topic_factor})")
                    break
            
            # 3. 중요 포인트 강조 검색
            important_keywords = ["중요한 것", "핵심 개념", "반드시 기억해야 할", "나중에 다시 설명하겠지만", "반드시 알아두어야 합니다", "뽑때는 점"]
            for keyword in important_keywords:
                if keyword in text:
                    important_factor = speed_variations.get("important_point", 0.85)
                    base_speed *= important_factor
                    logger.info(f"중요 내용 강조 표현 발견: 속도 조정 적용 ({important_factor})")
                    break
            
            # 4. 유머 표현 검색
            humor_keywords = ["재미있게도", "하하", "우스움", "재미있는 예로", "재밌는 부분", "재밌는 사실", "주목할 점", "신기하게도"]
            for keyword in humor_keywords:
                if keyword in text:
                    humor_factor = speed_variations.get("humor", 1.15)
                    base_speed *= humor_factor
                    logger.info(f"유머 표현 발견: 속도 조정 적용 ({humor_factor})")
                    break
            
            # 5. 예시 설명 검색
            example_keywords = ["예를 들어", "예시를 들어보면", "다음과 같은 사례", "실제 상황에서", "인사이트", "예시를 살펴볼까요", "예를 들어볼까요"]
            for keyword in example_keywords:
                if keyword in text:
                    example_factor = speed_variations.get("examples", 1.1)
                    base_speed *= example_factor
                    logger.info(f"예시 설명 발견: 속도 조정 적용 ({example_factor})")
                    break
                    
            # 6. 요약 및 마무리 검색
            summary_keywords = ["요약하자면", "정리하자면", "마무리하면", "정리해보자면", "지금까지 살펴본", "지글까지 배운"]
            for keyword in summary_keywords:
                if keyword in text:
                    summary_factor = speed_variations.get("summary", 1.0)
                    base_speed *= summary_factor
                    logger.info(f"요약 및 마무리 발견: 속도 조정 적용 ({summary_factor})")
                    break
                    
            # SSML이 지원되지 않으로 문장과 단락 사이의 휴지(멈춤)를 적용할 수 없지만,
            # 텍스트 분석 결과를 로그로 기록하여 휴지 패턴을 활용한 것처럼 요소를 추적
            
            # 중요 개념 전후 휴지 패턴 검색
            key_concept_keywords = ["핵심 개념", "주요 원리", "중요한 원칙", "핵심 원리"]
            for keyword in key_concept_keywords:
                if keyword in text:
                    # SSML이 지원되면 이 부분에 pause_patterns.get("key_concept") 값을 사용하여 휴지 삽입 가능
                    pause_range = pause_patterns.get("key_concept", [900, 1100])
                    avg_pause = sum(pause_range) / len(pause_range)
                    logger.info(f"핵심 개념 전후 휴지 패턴 발견: 평균 {avg_pause}ms 휴지 필요 (실제로는 SSML 미지원으로 적용되지 않음)")
                    break
            
            # 개행(단락 구분) 패턴 검색 - 휴지가 필요한 부분 로그로 기록
            paragraph_breaks = text.count('\n\n')
            if paragraph_breaks > 0:
                pause_range = pause_patterns.get("paragraph", [700, 900])
                avg_pause = sum(pause_range) / len(pause_range)
                logger.info(f"단락 구분 {paragraph_breaks}개 발견: 부분별 평균 {avg_pause}ms 휴지 필요 (실제로는 SSML 미지원으로 적용되지 않음)")
            
            # API 한계로 인한 속도 범위 클램핑 (0.25~4.0)
            base_speed = max(0.25, min(4.0, base_speed))
            
            return text, base_speed
        except Exception as e:
            logger.warning(f"음성 패턴 적용 실패: {str(e)}")
            return text, 1.0
    
    
    def text_to_speech(
        self, 
        text: str, 
        output_filename: Optional[str] = None, 
        voice: str = "alloy",
        language: str = "en",
        speed: float = 1.0,
        apply_patterns: bool = True
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
                
            # 음성 패턴 적용 (옵션)
            actual_speed = speed
            if apply_patterns:
                # 패턴 적용하여 텍스트 전처리 및 속도 조정
                processed_text, base_voice_speed = self.apply_speech_patterns(text, voice)
                text = processed_text
                actual_speed = speed * base_voice_speed  # 기본 속도에 사용자 설정 속도 적용
                
                # API 한계로 인해 속도 범위 클램핑 (0.25~4.0)
                actual_speed = max(0.25, min(4.0, actual_speed))
                
                # 로그 추가
                if actual_speed != speed:
                    logger.info(f"음성 특성 반영: {voice} 목소리의 속도가 {speed} 에서 {actual_speed} 으로 조정되었습니다.")
            
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
                    speed=actual_speed
                )
                
                # 오디오 파일 저장
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                
                logger.info(f"TTS 변환 완료: {output_path} ({len(audio_data)} 바이트)")
                return output_path
            else:
                # 텍스트가 너무 길면 분할 처리
                return self._process_long_text(text, output_path, voice, actual_speed)
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
    
    def get_voice_info(self, voice: str) -> Dict[str, Any]:
        """
        목소리 특성 정보 가져오기
        
        Args:
            voice: 목소리 이름
        
        Returns:
            목소리 특성 정보
        """
        return settings.VOICE_CHARACTERISTICS.get(voice, {
            "age": "40대",
            "role": "교육자",
            "style": "일반적인 분명한 발음",
            "speed": "중간 속도",
            "features": "기본 특성",
            "culture": "전체 문화권에 적합"
        })
    
    
    def generate_script_audio(
        self, 
        scripts: List[Dict[str, Any]], 
        language: str = "en",
        voice: str = "auto",
        speed: float = 1.0,
        apply_patterns: bool = True
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
                speed=speed,
                apply_patterns=apply_patterns
            )
            
            # 목소리 특성 정보 가져오기
            voice_info = self.get_voice_info(voice)
            
            # 결과 목록에 하나의 항목만 추가
            result = [{
                "pages": page_numbers,
                "audio_path": audio_path,
                "language": language,
                "voice": voice,
                "voice_characteristics": voice_info
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
    speed: float = 1.0,
    apply_patterns: bool = True
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
    return processor.text_to_speech(text, output_filename, voice, language, speed, apply_patterns)