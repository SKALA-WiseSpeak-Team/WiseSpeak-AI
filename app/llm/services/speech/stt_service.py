"""
STT(Speech-to-Text) 서비스
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, BinaryIO
from openai import OpenAI
import speech_recognition as sr
from pydub import AudioSegment

from ...config import config
from ...utils.logger import get_logger

logger = get_logger(__name__)

class STTService:
    """STT(Speech-to-Text) 서비스 클래스"""
    
    def __init__(self, api_key: Optional[str] = None, 
                model: str = "gpt-4o-transcribe", 
                language: Optional[str] = None,
                use_openai: bool = True):
        """STT 서비스 초기화
        
        Args:
            api_key (Optional[str], optional): OpenAI API 키
            model (str, optional): STT 모델
            language (Optional[str], optional): 오디오 언어 (ko, en, ja, zh 등)
            use_openai (bool, optional): OpenAI API 사용 여부 (False면 로컬 모델)
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if use_openai else None
        self.model = model
        self.language = language
        self.use_openai = use_openai
        self.recognizer = sr.Recognizer()
        
        # 언어 코드 매핑 (OpenAI -> speech_recognition)
        self.language_mapping = {
            "ko": "ko-KR",
            "en": "en-US",
            "ja": "ja-JP",
            "zh": "zh-CN"
        }
        
        logger.info(f"STT 서비스 초기화 완료 (모델: {model}, 언어: {language or '자동 감지'}, OpenAI: {use_openai})")
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """오디오 파일을 텍스트로 변환
        
        Args:
            audio_file_path (str): 오디오 파일 경로
        
        Returns:
            Optional[str]: 변환된 텍스트
        """
        if not Path(audio_file_path).exists():
            logger.error(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")
            return None
        
        # 파일 형식 확인 및 변환
        audio_format = Path(audio_file_path).suffix.lower()[1:]  # .mp3 -> mp3
        
        # 지원되는 형식인지 확인
        if self.use_openai:
            return self._transcribe_with_openai(audio_file_path)
        else:
            return self._transcribe_locally(audio_file_path)
    
    def _transcribe_with_openai(self, audio_file_path: str) -> Optional[str]:
        """OpenAI API를 사용하여 오디오 변환
        
        Args:
            audio_file_path (str): 오디오 파일 경로
        
        Returns:
            Optional[str]: 변환된 텍스트
        """
        try:
            # OpenAI Whisper API 호출
            with open(audio_file_path, "rb") as audio_file:
                options = {"model": self.model}
                
                if self.language:
                    options["language"] = self.language
                
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **options
                )
            
            logger.info(f"OpenAI로 오디오 변환 완료: {audio_file_path}")
            return response.text
        
        except Exception as e:
            logger.error(f"OpenAI 오디오 변환 중 오류 발생: {e}")
            return None
    
    def _transcribe_locally(self, audio_file_path: str) -> Optional[str]:
        """로컬 모델을 사용하여 오디오 변환
        
        Args:
            audio_file_path (str): 오디오 파일 경로
        
        Returns:
            Optional[str]: 변환된 텍스트
        """
        try:
            # 오디오 파일 로드
            with sr.AudioFile(self._ensure_wav_format(audio_file_path)) as source:
                audio_data = self.recognizer.record(source)
            
            # 언어 설정
            sr_language = self.language_mapping.get(self.language, None) if self.language else None
            
            # 음성 인식
            if sr_language:
                text = self.recognizer.recognize_google(audio_data, language=sr_language)
            else:
                text = self.recognizer.recognize_google(audio_data)
            
            logger.info(f"로컬 모델로 오디오 변환 완료: {audio_file_path}")
            return text
        
        except sr.UnknownValueError:
            logger.error("음성을 인식할 수 없습니다")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition 서비스에 접근할 수 없습니다: {e}")
            return None
        except Exception as e:
            logger.error(f"로컬 오디오 변환 중 오류 발생: {e}")
            return None
    
    def _ensure_wav_format(self, audio_file_path: str) -> str:
        """필요시 오디오 파일을 WAV 형식으로 변환
        
        Args:
            audio_file_path (str): 오디오 파일 경로
        
        Returns:
            str: WAV 파일 경로
        """
        file_ext = Path(audio_file_path).suffix.lower()
        
        # 이미 WAV 형식이면 그대로 반환
        if file_ext == ".wav":
            return audio_file_path
        
        # WAV로 변환
        try:
            # 임시 파일 경로
            temp_wav_path = tempfile.mktemp(suffix=".wav")
            
            # 변환
            audio = AudioSegment.from_file(audio_file_path)
            audio.export(temp_wav_path, format="wav")
            
            logger.info(f"오디오 파일을 WAV 형식으로 변환: {audio_file_path} -> {temp_wav_path}")
            return temp_wav_path
        
        except Exception as e:
            logger.error(f"WAV 변환 중 오류 발생: {e}")
            return audio_file_path  # 오류 시 원본 반환
    
    def transcribe_audio_from_bytes(self, 
                                audio_bytes: bytes, 
                                file_format: str = "mp3") -> Optional[str]:
        """오디오 바이트 데이터를 텍스트로 변환
        
        Args:
            audio_bytes (bytes): 오디오 바이트 데이터
            file_format (str): 오디오 파일 형식
        
        Returns:
            Optional[str]: 변환된 텍스트
        """
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(audio_bytes)
            
            # 변환 수행
            result = self.transcribe_audio(temp_file_path)
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
            return result
        
        except Exception as e:
            logger.error(f"오디오 바이트 변환 중 오류 발생: {e}")
            return None
    
    def record_audio(self, 
                    duration: int = 5, 
                    output_path: Optional[str] = None,
                    format: str = "wav",
                    detect_speech: bool = True) -> Optional[Dict[str, Any]]:
        """마이크로 오디오 녹음
        
        Args:
            duration (int, optional): 녹음 시간(초). 기본값은 5
            output_path (Optional[str], optional): 출력 파일 경로
            format (str, optional): 출력 파일 형식. 기본값은 "wav"
            detect_speech (bool, optional): 음성 감지 모드 사용 여부
        
        Returns:
            Optional[Dict[str, Any]]: 녹음 정보 (파일 경로 및 텍스트)
        """
        # 출력 경로 설정
        if not output_path:
            output_dir = Path(config.OUTPUT_DIR) / "recordings"
            os.makedirs(output_dir, exist_ok=True)
            
            file_id = str(uuid.uuid4())[:8]
            output_path = str(output_dir / f"recording_{file_id}.{format}")
        
        try:
            with sr.Microphone() as source:
                logger.info("마이크 조정 중...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # 녹음 시작
                if detect_speech:
                    logger.info("음성을 감지하면 녹음을 시작합니다...")
                    audio_data = self.recognizer.listen(source)
                else:
                    logger.info(f"{duration}초 동안 녹음합니다...")
                    audio_data = self.recognizer.record(source, duration=duration)
                
                # 오디오 저장
                with open(output_path, "wb") as f:
                    f.write(audio_data.get_wav_data())
                
                logger.info(f"녹음 완료: {output_path}")
                
                # 텍스트 변환
                text = None
                if self.use_openai:
                    text = self._transcribe_with_openai(output_path)
                else:
                    try:
                        if self.language:
                            sr_language = self.language_mapping.get(self.language, None)
                            text = self.recognizer.recognize_google(audio_data, language=sr_language)
                        else:
                            text = self.recognizer.recognize_google(audio_data)
                    except Exception as e:
                        logger.error(f"음성 인식 중 오류 발생: {e}")
                
                return {
                    "file_path": output_path,
                    "transcription": text,
                    "duration": duration if not detect_speech else None
                }
                
        except Exception as e:
            logger.error(f"녹음 중 오류 발생: {e}")
            return None
