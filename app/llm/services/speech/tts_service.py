"""
TTS(Text-to-Speech) 서비스
"""
import os
import tempfile
import uuid
from pathlib import Path
from openai import OpenAI
from typing import Optional, List, Dict, Any

from ...config import config
from ...utils.logger import get_logger

logger = get_logger(__name__)

class TTSService:
    """TTS(Text-to-Speech) 서비스 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, 
                voice: str = "alloy", 
                model: str = "gpt-4o-mini-tts", 
                output_dir: Optional[str] = None):
        """TTS 서비스 초기화
        
        Args:
            api_key (Optional[str], optional): OpenAI API 키
            voice (str, optional): 음성 종류 (alloy, echo, fable, onyx, nova, shimmer)
            model (str, optional): TTS 모델 (tts-1, tts-1-hd)
            output_dir (Optional[str], optional): 오디오 파일 저장 디렉토리
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.voice = voice
        self.model = model
        self.output_dir = output_dir or Path(config.OUTPUT_DIR) / "audio"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 사용 가능한 음성 목록
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        logger.info(f"TTS 서비스 초기화 완료 (음성: {voice}, 모델: {model})")
    
    def generate_speech(self, 
                    text: str, 
                    output_format: str = "mp3", 
                    filename: Optional[str] = None) -> Optional[str]:
        """텍스트를 음성으로 변환
        
        Args:
            text (str): 변환할 텍스트
            output_format (str, optional): 출력 파일 형식 (mp3, opus, aac, flac)
            filename (Optional[str], optional): 출력 파일 이름 (없으면 자동 생성)
        
        Returns:
            Optional[str]: 생성된 오디오 파일 경로
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트는 음성으로 변환할 수 없습니다")
            return None
        
        # 텍스트가 너무 길면 분할 (OpenAI API는 4096자 제한)
        if len(text) > 4000:
            logger.warning(f"텍스트가 너무 깁니다 ({len(text)}자). 분할하여 처리합니다.")
            return self._process_long_text(text, output_format, filename)
        
        try:
            # 출력 파일 경로 설정
            if filename:
                base_filename = filename
            else:
                file_id = str(uuid.uuid4())[:8]
                base_filename = f"speech_{file_id}"
            
            output_path = Path(self.output_dir) / f"{base_filename}.{output_format}"
            
            # OpenAI TTS API 호출
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=output_format
            )
            
            # 파일로 저장
            response.stream_to_file(str(output_path))
            
            logger.info(f"텍스트를 음성으로 변환 완료: {output_path}")
            return str(output_path)
        
        except Exception as e:
            logger.error(f"음성 생성 중 오류 발생: {e}")
            return None
    
    def _process_long_text(self, 
                        text: str, 
                        output_format: str = "mp3", 
                        filename: Optional[str] = None) -> Optional[str]:
        """긴 텍스트 처리 (분할 후 합치기)
        
        Args:
            text (str): 변환할 긴 텍스트
            output_format (str): 출력 파일 형식
            filename (Optional[str]): 출력 파일 이름
        
        Returns:
            Optional[str]: 생성된 오디오 파일 경로
        """
        from pydub import AudioSegment
        
        # 텍스트 분할 (문장 기준)
        segments = self._split_text(text)
        audio_paths = []
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 각 세그먼트 처리
            for i, segment in enumerate(segments):
                if not segment.strip():
                    continue
                
                temp_filename = f"segment_{i:03d}"
                audio_path = self.generate_speech(
                    text=segment,
                    output_format=output_format,
                    filename=str(temp_dir / temp_filename)
                )
                
                if audio_path:
                    audio_paths.append(audio_path)
            
            # 모든 세그먼트가 처리되었으면 합치기
            if not audio_paths:
                logger.error("처리된 오디오 세그먼트가 없습니다")
                return None
            
            # 출력 파일 경로 설정
            if filename:
                base_filename = filename
            else:
                file_id = str(uuid.uuid4())[:8]
                base_filename = f"speech_combined_{file_id}"
            
            output_path = Path(self.output_dir) / f"{base_filename}.{output_format}"
            
            # 오디오 합치기
            combined = AudioSegment.empty()
            for path in audio_paths:
                segment = AudioSegment.from_file(path)
                combined += segment
            
            combined.export(output_path, format=output_format)
            logger.info(f"분할된 {len(audio_paths)}개 오디오를 결합하여 저장: {output_path}")
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"긴 텍스트 처리 중 오류 발생: {e}")
            return None
        finally:
            # 임시 파일 정리
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"임시 파일 정리 중 오류: {e}")
    
    def _split_text(self, text: str, max_length: int = 3000) -> List[str]:
        """텍스트를 적절한 크기로 분할
        
        Args:
            text (str): 분할할 텍스트
            max_length (int, optional): 최대 세그먼트 길이
        
        Returns:
            List[str]: 분할된 텍스트 세그먼트 목록
        """
        # 문장 기준으로 분할 (한국어 포함)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            # 문장이 너무 길면 그 자체가 하나의 세그먼트
            if len(sentence) > max_length:
                if current_segment:
                    segments.append(current_segment)
                    current_segment = ""
                
                # 긴 문장을 더 작은 단위로 분할 (단락 기준)
                sub_segments = self._split_by_chunk(sentence, max_length)
                segments.extend(sub_segments)
                continue
            
            # 현재 세그먼트에 문장 추가 시 최대 길이 초과 확인
            if len(current_segment) + len(sentence) + 1 > max_length:
                segments.append(current_segment)
                current_segment = sentence
            else:
                if current_segment:
                    current_segment += " " + sentence
                else:
                    current_segment = sentence
        
        # 마지막 세그먼트 처리
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _split_by_chunk(self, text: str, max_length: int) -> List[str]:
        """텍스트를 청크 단위로 분할
        
        Args:
            text (str): 분할할 텍스트
            max_length (int): 최대 청크 길이
        
        Returns:
            List[str]: 분할된 청크 목록
        """
        chunks = []
        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            chunks.append(chunk)
        return chunks
    
    def generate_speech_for_lecture(self, 
                                lecture_script: Dict[int, Dict[str, Any]], 
                                output_format: str = "mp3") -> Dict[int, str]:
        """강의 스크립트를 오디오로 변환
        
        Args:
            lecture_script (Dict[int, Dict[str, Any]]): 페이지별 강의 스크립트
            output_format (str, optional): 출력 파일 형식
        
        Returns:
            Dict[int, str]: 페이지 번호를 키로 하는 오디오 파일 경로 딕셔너리
        """
        audio_paths = {}
        
        total_pages = len(lecture_script)
        logger.info(f"총 {total_pages}페이지의 강의 스크립트를 오디오로 변환합니다")
        
        for page_num, script_data in sorted(lecture_script.items()):
            script_text = script_data.get("script", "")
            if not script_text:
                logger.warning(f"페이지 {page_num}의 스크립트가 비어 있습니다")
                continue
            
            logger.info(f"페이지 {page_num}/{total_pages} 처리 중...")
            
            # 파일명 지정 (페이지 번호 포함)
            filename = f"lecture_page_{page_num}"
            
            # 음성 생성
            audio_path = self.generate_speech(
                text=script_text,
                output_format=output_format,
                filename=filename
            )
            
            if audio_path:
                audio_paths[page_num] = audio_path
        
        logger.info(f"{len(audio_paths)}/{total_pages}페이지의 오디오 생성 완료")
        return audio_paths
