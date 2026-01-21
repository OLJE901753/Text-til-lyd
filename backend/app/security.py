"""File validation and security utilities."""
import os
import re
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Try to import magic, but make it optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available, will use extension-based validation only")

# Audio MIME types mapping
AUDIO_MIME_TYPES = {
    "audio/mpeg": ["mp3"],
    "audio/mp4": ["m4a", "mp4"],
    "audio/wav": ["wav"],
    "audio/wave": ["wav"],
    "audio/x-wav": ["wav"],
    "audio/webm": ["webm"],
    "audio/ogg": ["ogg"],
    "audio/vorbis": ["ogg"],
    "audio/x-m4a": ["m4a"],
}

# Allowed file extensions
ALLOWED_EXTENSIONS = set(settings.allowed_audio_types_list)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other security issues."""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove any null bytes
    filename = filename.replace("\x00", "")
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_file_size(file_size: int) -> Tuple[bool, Optional[str]]:
    """Validate file size against configured limits."""
    max_size = settings.max_file_size_bytes
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = settings.max_file_size_mb
        return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return Path(filename).suffix.lower().lstrip('.')


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """Validate file extension."""
    ext = get_file_extension(filename)
    
    if not ext:
        return False, "File has no extension"
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, None


def validate_mime_type(file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """Validate file MIME type using magic bytes."""
    if not MAGIC_AVAILABLE:
        # Fallback to extension validation if magic is not available
        logger.debug("Magic not available, using extension validation", filename=filename)
        return validate_file_extension(filename)
    
    try:
        # Use python-magic to detect MIME type
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_content)
        
        logger.debug("File MIME type detected", mime=detected_mime, filename=filename)
        
        # Check if MIME type is in our allowed list
        if detected_mime in AUDIO_MIME_TYPES:
            # Verify extension matches MIME type
            ext = get_file_extension(filename)
            allowed_exts = AUDIO_MIME_TYPES[detected_mime]
            
            if ext in allowed_exts:
                return True, None
            else:
                return False, f"MIME type '{detected_mime}' does not match file extension '{ext}'"
        
        # Check for audio/* prefix as fallback
        if detected_mime.startswith("audio/"):
            ext = get_file_extension(filename)
            if ext in ALLOWED_EXTENSIONS:
                logger.warning("Audio MIME type detected but not in mapping", mime=detected_mime, ext=ext)
                return True, None
        
        return False, f"File type '{detected_mime}' is not an allowed audio format"
    
    except Exception as e:
        logger.error("Error validating MIME type", error=str(e), filename=filename)
        # Fallback to extension validation if magic fails
        return validate_file_extension(filename)


async def validate_upload_file(file: UploadFile) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Comprehensive file validation.
    
    Returns:
        Tuple of (is_valid, error_message, sanitized_filename)
    """
    # Read file content for validation (limit to first 1MB for MIME type detection)
    # This prevents loading entire large files into memory just for validation
    chunk = await file.read(1024 * 1024)  # Read first 1MB
    await file.seek(0)  # Reset file pointer
    
    # Get file size from content-length header if available, otherwise estimate
    file_size = getattr(file, 'size', None) or len(chunk)
    
    # For large files, we'll validate size during streaming upload
    # But check if what we read exceeds max size
    if file_size > settings.max_file_size_bytes:
        return False, f"File size exceeds maximum allowed size ({settings.max_file_size_mb}MB)", None
    
    # Sanitize filename
    sanitized_name = sanitize_filename(file.filename)
    
    # Validate file extension
    is_valid, error = validate_file_extension(sanitized_name)
    if not is_valid:
        return False, error, None
    
    # Validate MIME type using magic bytes (or extension if magic unavailable)
    # Use the chunk we read (first 1MB is enough for MIME detection)
    is_valid, error = validate_mime_type(chunk, sanitized_name)
    if not is_valid:
        return False, error, None
    
    # Log validation success
    if MAGIC_AVAILABLE:
        try:
            mime = magic.Magic(mime=True).from_buffer(chunk)
            logger.info("File validation passed", filename=sanitized_name, size=file_size, mime=mime)
        except Exception:
            logger.info("File validation passed", filename=sanitized_name, size=file_size)
    else:
        logger.info("File validation passed", filename=sanitized_name, size=file_size)
    
    return True, None, sanitized_name


def ensure_temp_directory() -> Path:
    """Ensure temp directory exists and return its path."""
    temp_path = Path(settings.temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def get_temp_file_path(filename: str) -> Path:
    """Get a secure temporary file path."""
    temp_dir = ensure_temp_directory()
    sanitized = sanitize_filename(filename)
    return temp_dir / sanitized
