"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    transcript: str = Field(..., description="The transcribed text")
    language: Optional[str] = Field(None, description="Detected language code")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    confidence_warning: Optional[bool] = Field(False, description="Whether confidence is below threshold (<0.5)")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[dict]] = Field(None, description="Transcription segments with timestamps")
    model: str = Field(..., description="Whisper model used")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="API version")
    model_loaded: Optional[bool] = Field(None, description="Whether Whisper model is loaded")
    model_name: Optional[str] = Field(None, description="Loaded model name")
    device: Optional[str] = Field(None, description="Device being used (cuda/cpu)")
    gpu_info: Optional[Dict[str, Any]] = Field(None, description="GPU information if available")
    cuda_available: Optional[bool] = Field(None, description="Whether CUDA is available")
    cuda_device_count: Optional[int] = Field(None, description="Number of CUDA devices available")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")
