"""Tests for security module."""
import pytest
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

from app.security import (
    validate_file_size,
    validate_file_extension,
    sanitize_filename,
    get_file_extension,
)


def test_validate_file_size_valid():
    """Test file size validation with valid size."""
    is_valid, error = validate_file_size(1024 * 1024)  # 1MB
    assert is_valid is True
    assert error is None


def test_validate_file_size_too_large():
    """Test file size validation with file too large."""
    max_size = 100 * 1024 * 1024  # 100MB
    is_valid, error = validate_file_size(max_size + 1)
    assert is_valid is False
    assert error is not None
    assert "exceeds maximum" in error.lower()


def test_validate_file_size_empty():
    """Test file size validation with empty file."""
    is_valid, error = validate_file_size(0)
    assert is_valid is False
    assert error == "File is empty"


def test_get_file_extension():
    """Test file extension extraction."""
    assert get_file_extension("test.mp3") == "mp3"
    assert get_file_extension("test.MP3") == "mp3"
    assert get_file_extension("test.file.m4a") == "m4a"
    assert get_file_extension("test") == ""


def test_validate_file_extension_valid():
    """Test file extension validation with valid extension."""
    is_valid, error = validate_file_extension("test.mp3")
    assert is_valid is True
    assert error is None


def test_validate_file_extension_invalid():
    """Test file extension validation with invalid extension."""
    is_valid, error = validate_file_extension("test.exe")
    assert is_valid is False
    assert error is not None
    assert "not allowed" in error.lower()


def test_sanitize_filename():
    """Test filename sanitization."""
    # Test path traversal
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    
    # Test dangerous characters
    assert "/" not in sanitize_filename("test/file.mp3")
    assert "\\" not in sanitize_filename("test\\file.mp3")
    assert ":" not in sanitize_filename("test:file.mp3")
    
    # Test null bytes
    assert "\x00" not in sanitize_filename("test\x00file.mp3")
    
    # Test length limit
    long_name = "a" * 300 + ".mp3"
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) <= 255
