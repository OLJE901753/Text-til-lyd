"""Whisper transcription service with singleton model loading and GPU support."""
import whisper
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
import sys

from app.config import settings
from app.logger import get_logger
from app.audio_processor import preprocess_audio, get_audio_duration

logger = get_logger(__name__)

# Try to import torch for GPU detection (will fail gracefully if not available)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GPU detection disabled")


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
            self._device = None
            self._gpu_info = None
    
    def _detect_device(self) -> str:
        """Detect optimal device (GPU/CPU) based on availability and memory."""
        device_setting = settings.whisper_device.lower()
        
        # If explicitly set to cpu, use CPU
        if device_setting == "cpu":
            logger.info("Device set to CPU (explicit)")
            return "cpu"
        
        # If explicitly set to cuda, try CUDA
        if device_setting == "cuda":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                logger.info("Device set to CUDA (explicit)")
                return "cuda"
            else:
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
        
        # Auto-detect (device_setting == "auto" or default)
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                # Get GPU info
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    gpu_name = torch.cuda.get_device_name(0)
                    vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                    vram_free = (torch.cuda.get_device_properties(0).total_memory - 
                                torch.cuda.memory_allocated(0)) / (1024**3)  # GB
                    cuda_version = torch.version.cuda
                    
                    self._gpu_info = {
                        "name": gpu_name,
                        "vram_total_gb": round(vram_total, 2),
                        "vram_free_gb": round(vram_free, 2),
                        "cuda_version": cuda_version,
                        "device_count": gpu_count
                    }
                    
                    logger.info(
                        "GPU detected and available",
                        gpu=gpu_name,
                        vram_total_gb=round(vram_total, 2),
                        vram_free_gb=round(vram_free, 2),
                        cuda_version=cuda_version
                    )
                    return "cuda"
                else:
                    logger.info("No GPU devices found, using CPU")
                    return "cpu"
            except Exception as e:
                logger.warning("Error detecting GPU, falling back to CPU", error=str(e))
                return "cpu"
        else:
            logger.info("CUDA not available (PyTorch not installed or no GPU), using CPU")
            return "cpu"
    
    def _check_memory_and_select_model(self, device: str, requested_model: str) -> str:
        """Check available memory (VRAM for GPU, RAM for CPU) and select appropriate model."""
        if device == "cuda" and TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                # Check GPU VRAM
                vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                
                if vram_total < 4:
                    logger.warning(
                        "GPU VRAM insufficient for large-v3",
                        vram_gb=round(vram_total, 2),
                        fallback="medium"
                    )
                    return "medium"
                elif vram_total < 6:
                    logger.info(
                        "GPU VRAM may be tight for large-v3, but proceeding",
                        vram_gb=round(vram_total, 2),
                        model=requested_model
                    )
                    return requested_model
                else:
                    logger.info(
                        "GPU VRAM sufficient for large-v3",
                        vram_gb=round(vram_total, 2),
                        model=requested_model
                    )
                    return requested_model
            except Exception as e:
                logger.warning("Error checking GPU VRAM, using requested model", error=str(e))
                return requested_model
        else:
            # CPU mode - check system RAM
            try:
                import psutil
                ram_total = psutil.virtual_memory().total / (1024**3)  # GB
                ram_available = psutil.virtual_memory().available / (1024**3)  # GB
                
                logger.info(
                    "CPU mode - checking system RAM",
                    ram_total_gb=round(ram_total, 2),
                    ram_available_gb=round(ram_available, 2)
                )
                
                if ram_available < 4:
                    logger.warning(
                        "System RAM insufficient for large-v3",
                        ram_available_gb=round(ram_available, 2),
                        fallback="base"
                    )
                    return "base"
                elif ram_available < 6:
                    logger.warning(
                        "System RAM may be tight for large-v3",
                        ram_available_gb=round(ram_available, 2),
                        fallback="medium"
                    )
                    return "medium"
                else:
                    logger.info(
                        "System RAM sufficient for large-v3",
                        ram_available_gb=round(ram_available, 2),
                        model=requested_model
                    )
                    return requested_model
            except ImportError:
                logger.warning("psutil not available, cannot check RAM, using requested model")
                return requested_model
            except Exception as e:
                logger.warning("Error checking system RAM, using requested model", error=str(e))
                return requested_model
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """Load Whisper model (singleton - only loads once) with GPU/CPU detection."""
        if self._model_loaded and self._model is not None:
            logger.info("Model already loaded", model=self._model_name, device=self._device)
            return
        
        # Detect device (GPU/CPU)
        device = self._detect_device()
        self._device = device
        
        # Determine model to load based on memory availability
        requested_model = model_name or settings.whisper_model
        model_to_load = self._check_memory_and_select_model(device, requested_model)
        
        download_root = Path(settings.whisper_download_root)
        download_root.mkdir(parents=True, exist_ok=True)
        
        logger.info("Loading Whisper model", model=model_to_load, device=device)
        if self._gpu_info:
            logger.info("GPU info", **self._gpu_info)
        start_time = time.time()
        
        try:
            # Load model with detected device
            self._model = whisper.load_model(
                model_to_load,
                device=device,
                download_root=str(download_root)
            )
            self._model_name = model_to_load
            self._model_loaded = True
            
            load_time = time.time() - start_time
            logger.info(
                "Whisper model loaded successfully",
                model=model_to_load,
                device=device,
                load_time=f"{load_time:.2f}s"
            )
            
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e), model=model_to_load, device=device, exc_info=True)
            # Try fallback to CPU if GPU failed
            if device == "cuda":
                logger.info("GPU load failed, attempting CPU fallback")
                try:
                    self._device = "cpu"
                    self._model = whisper.load_model(
                        model_to_load,
                        device="cpu",
                        download_root=str(download_root)
                    )
                    self._model_name = model_to_load
                    self._model_loaded = True
                    logger.info("Model loaded successfully on CPU fallback", model=model_to_load)
                except Exception as fallback_error:
                    logger.error("CPU fallback also failed", error=str(fallback_error), exc_info=True)
                    raise Exception(f"Failed to load Whisper model on both GPU and CPU: {str(e)}")
            else:
                raise Exception(f"Failed to load Whisper model: {str(e)}")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded and self._model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model and device."""
        info = {
            "loaded": self._model_loaded,
            "model_name": self._model_name if self._model_loaded else None,
            "device": self._device or settings.whisper_device
        }
        
        # Always check CUDA availability (even if model not loaded) for health check
        if TORCH_AVAILABLE:
            info["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                info["cuda_device_count"] = torch.cuda.device_count()
                # If device not detected yet but CUDA is available, detect it now
                if not self._device or self._device == "unknown":
                    # Try to get GPU info if not already available
                    if not self._gpu_info:
                        try:
                            gpu_count = torch.cuda.device_count()
                            if gpu_count > 0:
                                gpu_name = torch.cuda.get_device_name(0)
                                vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                                cuda_version = torch.version.cuda
                                
                                self._gpu_info = {
                                    "name": gpu_name,
                                    "vram_total_gb": round(vram_total, 2),
                                    "vram_free_gb": round(vram_total, 2),  # Approximate if not allocated yet
                                    "cuda_version": cuda_version,
                                    "device_count": gpu_count
                                }
                                # Update device if auto-detect
                                if settings.whisper_device.lower() == "auto":
                                    self._device = "cuda"
                                    info["device"] = "cuda"
                        except Exception as e:
                            logger.debug("Error getting GPU info for health check", error=str(e))
            else:
                info["cuda_device_count"] = 0
        else:
            info["cuda_available"] = False
            info["cuda_device_count"] = 0
            info["torch_available"] = False
        
        # Add GPU info if available
        if self._gpu_info:
            info["gpu_info"] = self._gpu_info
        
        return info
    
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
            
            # Transcribe in thread pool to avoid blocking event loop
            import asyncio
            import concurrent.futures
            
            # Use thread pool executor for CPU-bound transcription (or GPU-bound)
            loop = asyncio.get_event_loop()
            
            # Optimized transcription parameters for maximum accuracy (99% goal)
            def transcribe_fn():
                return self._model.transcribe(
                    str(processed_path if use_processed else audio_path),
                    language=language,
                    task=task,
                    verbose=False,
                    temperature=0,  # Deterministic results
                    best_of=5,  # Try multiple decodings for better accuracy (increased from 1)
                    beam_size=10,  # Increased beam size for 99% accuracy goal (was 5)
                    compression_ratio_threshold=2.4,  # Filter low-quality results
                    logprob_threshold=-1.0,  # Filter low-probability segments
                    condition_on_previous_text=True,  # Use context from previous segments for better accuracy
                    initial_prompt=None if not language else f"This is a {language} audio recording.",  # Language hint for better accuracy
                    no_speech_threshold=0.6  # Lower threshold to catch more speech
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                result = await loop.run_in_executor(executor, transcribe_fn)
            
            transcription_time = time.time() - start_time
            
            # Extract transcript and metadata
            transcript = result.get("text", "").strip()
            detected_language = result.get("language", language or "unknown")
            segments = result.get("segments", [])
            
            # Post-process transcript for better quality (punctuation, capitalization, spacing)
            transcript = self._post_process_transcript(transcript, detected_language)
            
            # Calculate average confidence from segments
            confidence = None
            confidence_warning = False
            if segments:
                confidences = [seg.get("no_speech_prob", 0) for seg in segments if "no_speech_prob" in seg]
                if confidences:
                    # Convert no_speech_prob to confidence (lower no_speech = higher confidence)
                    avg_no_speech = sum(confidences) / len(confidences)
                    confidence = 1.0 - avg_no_speech
                    
                    # Validate confidence threshold (warn if confidence < 0.5)
                    if confidence < 0.5:
                        confidence_warning = True
                        logger.warning(
                            "Low confidence transcription",
                            confidence=round(confidence, 3),
                            threshold=0.5,
                            duration=f"{duration:.2f}s",
                            language=detected_language
                        )
            
            logger.info(
                "Transcription completed",
                duration=f"{duration:.2f}s",
                transcription_time=f"{transcription_time:.2f}s",
                language=detected_language,
                transcript_length=len(transcript),
                confidence=round(confidence, 3) if confidence is not None else None,
                confidence_warning=confidence_warning
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
                "confidence_warning": confidence_warning,
                "duration": duration,
                "segments": segments,
                "model": self._model_name,
                "transcription_time": transcription_time
            }
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e), file=str(audio_path))
            raise Exception(f"Transcription failed: {str(e)}")
    
    def _post_process_transcript(self, transcript: str, language: str) -> str:
        """
        Post-process transcript to improve quality (punctuation, capitalization, spacing).
        
        Args:
            transcript: Raw transcript text
            language: Detected language code
        
        Returns:
            Post-processed transcript
        """
        if not transcript:
            return transcript
        
        # Basic cleanup - fix common spacing issues
        import re
        
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript)
        
        # Fix spacing around punctuation (common Whisper issues)
        # Add space after periods, commas, etc. if missing
        transcript = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', transcript)
        transcript = re.sub(r'([,;:])([A-Za-z])', r'\1 \2', transcript)
        
        # Remove spaces before punctuation
        transcript = re.sub(r'\s+([,.!?;:])', r'\1', transcript)
        
        # Fix capitalization at sentence starts (basic heuristic)
        # Split by sentence endings and capitalize first letter
        sentences = re.split(r'([.!?]+\s*)', transcript)
        processed_sentences = []
        capitalize_next = True  # Always capitalize first sentence
        
        for sentence in sentences:
            if not sentence.strip():
                processed_sentences.append(sentence)
                continue
            
            # If it's a sentence ending punctuation, keep as is and flag next for capitalization
            if re.match(r'^[.!?]+\s*$', sentence):
                processed_sentences.append(sentence)
                capitalize_next = True
            else:
                # Capitalize first letter of sentence if needed
                if capitalize_next:
                    # Find first letter character
                    for i, char in enumerate(sentence):
                        if char.isalpha():
                            sentence = sentence[:i] + char.upper() + sentence[i+1:]
                            break
                    capitalize_next = False
                processed_sentences.append(sentence)
        
        transcript = ''.join(processed_sentences)
        
        # Strip and return
        return transcript.strip()


# Global service instance
_transcription_service: Optional[WhisperTranscriptionService] = None


def get_transcription_service() -> WhisperTranscriptionService:
    """Get the singleton transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = WhisperTranscriptionService()
    return _transcription_service
