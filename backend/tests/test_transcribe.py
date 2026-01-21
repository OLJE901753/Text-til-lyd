"""Tests for transcription service."""
import pytest
from pathlib import Path
from app.transcribe import WhisperTranscriptionService, get_transcription_service


def test_singleton_pattern():
    """Test that WhisperTranscriptionService is a singleton."""
    service1 = get_transcription_service()
    service2 = get_transcription_service()
    
    assert service1 is service2
    assert id(service1) == id(service2)


def test_model_info_before_load():
    """Test model info before model is loaded."""
    service = get_transcription_service()
    info = service.get_model_info()
    
    assert "loaded" in info
    assert "model_name" in info
    assert "device" in info


def test_is_model_loaded_before_load():
    """Test is_model_loaded before model is loaded."""
    service = get_transcription_service()
    # Note: This test assumes model is not preloaded
    # In actual usage, model would be loaded on first transcription
    assert isinstance(service.is_model_loaded(), bool)
