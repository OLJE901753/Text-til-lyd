"""FastAPI application entry point."""
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from pathlib import Path
import shutil

from app.config import settings
from app.logger import configure_logging, get_logger
from app.security import validate_upload_file, get_temp_file_path
from app.audio_processor import save_uploaded_file
from app.transcribe import get_transcription_service
from app.models import TranscriptionResponse, HealthResponse, ErrorResponse

# Configure logging
configure_logging(settings.log_level, settings.log_format)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Audio Transcription API",
    description="World-class audio transcription service with Whisper",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    import time
    import shutil
    startup_start = time.time()
    
    logger.info("Starting Audio Transcription API", version="1.0.0")
    logger.info("Configuration loaded", model=settings.whisper_model)
    
    # Cleanup old temp files on startup
    try:
        temp_dir = Path(settings.temp_dir)
        if temp_dir.exists():
            # Remove files older than 1 hour
            import time as time_module
            current_time = time_module.time()
            cleaned_count = 0
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > 3600:  # 1 hour
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning("Failed to cleanup old temp file", file=str(file_path), error=str(e))
            if cleaned_count > 0:
                logger.info("Cleaned up old temp files", count=cleaned_count)
    except Exception as e:
        logger.warning("Failed to cleanup temp files on startup", error=str(e))
    
    # Optionally preload model on startup (can be disabled for faster startup)
    # Uncomment the following lines to preload model:
    # try:
    #     service = get_transcription_service()
    #     load_start = time.time()
    #     service.load_model()
    #     load_time = time.time() - load_start
    #     logger.info("Model preloaded on startup", load_time=f"{load_time:.2f}s")
    # except Exception as e:
    #     logger.warning("Failed to preload model", error=str(e))
    
    startup_time = time.time() - startup_start
    logger.info("Startup completed", startup_time=f"{startup_time:.2f}s")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Audio Transcription API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Audio Transcription API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health", response_model=HealthResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health_check(request: Request):
    """Health check endpoint with model status."""
    service = get_transcription_service()
    model_info = service.get_model_info()
    
    return HealthResponse(
        status="healthy",
        service="audio-transcription-api",
        version="1.0.0",
        model_loaded=model_info["loaded"],
        model_name=model_info["model_name"] if model_info["loaded"] else None
    )


@app.post("/api/transcribe", response_model=TranscriptionResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: str = None
):
    """
    Transcribe audio file.
    
    Args:
        file: Audio file to transcribe
        language: Optional language code (e.g., "no" for Norwegian, "en" for English)
    
    Returns:
        TranscriptionResponse with transcript and metadata
    """
    temp_file_path = None
    
    try:
        # Ensure temp directory exists
        from app.security import ensure_temp_directory
        ensure_temp_directory()
        
        # Validate file
        is_valid, error_msg, sanitized_name = await validate_upload_file(file)
        if not is_valid:
            logger.warning("File validation failed", error=error_msg, filename=file.filename)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Save uploaded file to temp location using streaming to prevent memory issues
        temp_file_path = get_temp_file_path(sanitized_name)
        
        # Stream file to disk in chunks to avoid loading entire file into memory
        try:
            import aiofiles
            file_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            async with aiofiles.open(temp_file_path, 'wb') as f:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    await f.write(chunk)
                    file_size += len(chunk)
                    
                    # Check file size during upload to prevent DoS
                    if file_size > settings.max_file_size_bytes:
                        temp_file_path.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=400,
                            detail=f"File size exceeds maximum allowed size ({settings.max_file_size_mb}MB)"
                        )
            
            if file_size == 0:
                temp_file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="File is empty or could not be read")
            
            logger.info("File uploaded and validated", filename=sanitized_name, size=file_size)
        except HTTPException:
            raise
        except Exception as e:
            # Cleanup on error
            if temp_file_path.exists():
                temp_file_path.unlink(missing_ok=True)
            logger.error("Failed to read/save file", error=str(e), filename=sanitized_name, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process file: {str(e)}"
            )
        
        # Get transcription service
        service = get_transcription_service()
        
        # Load model if not already loaded (in thread pool to avoid blocking event loop)
        if not service.is_model_loaded():
            logger.info("Loading Whisper model on first request")
            import asyncio
            import concurrent.futures
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                await loop.run_in_executor(executor, service.load_model)
        
        # Transcribe with timing
        import time
        start_time = time.time()
        result = await service.transcribe(
            temp_file_path,
            language=language if language else None
        )
        transcription_time = time.time() - start_time
        logger.info(
            "Transcription completed",
            filename=sanitized_name,
            duration=result.get("duration", 0),
            transcription_time=transcription_time,
            language=result.get("language"),
            model=result.get("model")
        )
        
        # Return response
        return TranscriptionResponse(
            transcript=result["transcript"],
            language=result["language"],
            confidence=result["confidence"],
            duration=result["duration"],
            segments=result.get("segments", []),
            model=result["model"]
        )
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error("File not found", error=str(e), exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except MemoryError as e:
        logger.error("Out of memory", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="File is too large or system is out of memory. Try a smaller file."
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(
            "Transcription error",
            error=str(e),
            type=type(e).__name__,
            traceback=error_trace,
            exc_info=True
        )
        # Provide more detailed error message for debugging
        error_detail = str(e)
        if "model" in error_detail.lower() or "whisper" in error_detail.lower():
            error_detail = f"Model error: {error_detail}. Please check if the Whisper model is properly installed."
        elif "memory" in error_detail.lower() or "out of" in error_detail.lower():
            error_detail = f"Memory error: {error_detail}. The file may be too large."
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {error_detail}"
        )
    finally:
        # Cleanup temp file
        if temp_file_path and temp_file_path.exists() and settings.cleanup_temp_files:
            try:
                temp_file_path.unlink()
                logger.debug("Cleaned up temp file", path=str(temp_file_path))
            except Exception as e:
                logger.warning("Failed to cleanup temp file", error=str(e), path=str(temp_file_path))


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error="Rate limit exceeded",
            detail=f"Too many requests. Limit: {settings.rate_limit_per_minute} per minute",
            code="RATE_LIMIT_EXCEEDED"
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error("Unhandled exception", error=str(exc), type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred",
            code="INTERNAL_ERROR"
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        limit_concurrency=100,
        limit_max_requests=1000,
        timeout_keep_alive=300,
        # Increase max request size to handle large audio files (100MB + buffer)
        client_max_body_size=120 * 1024 * 1024,  # 120MB
    )
