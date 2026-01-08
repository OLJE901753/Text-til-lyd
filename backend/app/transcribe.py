"""Whisper transcription service with singleton model loading."""
import whisper
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading

from app.config import settings
from app.logger import get_logger
from app.audio_processor import preprocess_audio, get_audio_duration

logger = get_logger(__name__)


class WhisperTranscriptionService:
    """Singleton Whisper transcription service."""
    
    _instance = None
    _lock = threading.Lock()
    _model = None
    _model_name = None
    _model_loaded = False
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(WhisperTranscriptionService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the service (only called once due to singleton)."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._model = None
            self._model_name = settings.whisper_model
            self._model_loaded = False
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """Load Whisper model (singleton - only loads once)."""
        if self._model_loaded and self._model is not None:
            logger.info("Model already loaded", model=self._model_name)
            return
        
        model_to_load = model_name or settings.whisper_model
        download_root = Path(settings.whisper_download_root)
        download_root.mkdir(parents=True, exist_ok=True)
        
        logger.info("Loading Whisper model", model=model_to_load, device=settings.whisper_device)
        start_time = time.time()
        
        try:
            self._model = whisper.load_model(
                model_to_load,
                device=settings.whisper_device,
                download_root=str(download_root)
            )
            self._model_name = model_to_load
            self._model_loaded = True
            
            load_time = time.time() - start_time
            logger.info("Whisper model loaded successfully", model=model_to_load, load_time=f"{load_time:.2f}s")
            
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e), model=model_to_load)
            raise Exception(f"Failed to load Whisper model: {str(e)}")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded and self._model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "loaded": self._model_loaded,
            "model_name": self._model_name,
            "device": settings.whisper_device
        }
    
    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., "no" for Norwegian, "en" for English)
            task: "transcribe" or "translate"
        
        Returns:
            Dictionary with transcription results
        """
        if not self.is_model_loaded():
            logger.info("Model not loaded, loading now")
            self.load_model()
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info("Starting transcription", file=str(audio_path), language=language, task=task)
        start_time = time.time()
        
        try:
            # Preprocess audio if needed
            processed_path = await preprocess_audio(audio_path)
            use_processed = processed_path != audio_path
            
            # Get audio duration
            duration = await get_audio_duration(processed_path if use_processed else audio_path)
            
            # Transcribe
            result = self._model.transcribe(
                str(processed_path if use_processed else audio_path),
                language=language,
                task=task,
                verbose=False
            )
            
            transcription_time = time.time() - start_time
            
            # Extract transcript and metadata
            transcript = result.get("text", "").strip()
            detected_language = result.get("language", language or "unknown")
            segments = result.get("segments", [])
            
            # Calculate average confidence from segments
            confidence = None
            if segments:
                confidences = [seg.get("no_speech_prob", 0) for seg in segments if "no_speech_prob" in seg]
                if confidences:
                    # Convert no_speech_prob to confidence (lower no_speech = higher confidence)
                    avg_no_speech = sum(confidences) / len(confidences)
                    confidence = 1.0 - avg_no_speech
            
            logger.info(
                "Transcription completed",
                duration=f"{duration:.2f}s",
                transcription_time=f"{transcription_time:.2f}s",
                language=detected_language,
                transcript_length=len(transcript)
            )
            
            # Cleanup processed file if it was created
            if use_processed and processed_path.exists():
                try:
                    processed_path.unlink()
                    logger.debug("Cleaned up processed audio file", path=str(processed_path))
                except Exception as e:
                    logger.warning("Failed to cleanup processed file", error=str(e))
            
            return {
                "transcript": transcript,
                "language": detected_language,
                "confidence": confidence,
                "duration": duration,
                "segments": segments,
                "model": self._model_name,
                "transcription_time": transcription_time
            }
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e), file=str(audio_path))
            raise Exception(f"Transcription failed: {str(e)}")


# Global service instance
_transcription_service: Optional[WhisperTranscriptionService] = None


def get_transcription_service() -> WhisperTranscriptionService:
    """Get the singleton transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = WhisperTranscriptionService()
    return _transcription_service
