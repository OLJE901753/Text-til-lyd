"""Audio preprocessing using FFmpeg for optimal Whisper performance."""
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import asyncio

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Optimal audio settings for Whisper
WHISPER_SAMPLE_RATE = 16000  # Whisper expects 16kHz
WHISPER_CHANNELS = 1  # Mono audio
WHISPER_FORMAT = "wav"  # WAV format for best compatibility


def _get_system_path() -> str:
    """Get the system PATH environment variable (refreshed from registry on Windows)."""
    import os
    
    if sys.platform == "win32":
        # On Windows, read PATH from system environment variables
        import winreg
        
        # Read from user and system PATH
        user_path = ""
        system_path = ""
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                user_path = winreg.QueryValueEx(key, "PATH")[0]
        except (FileNotFoundError, OSError):
            pass
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                system_path = winreg.QueryValueEx(key, "PATH")[0]
        except (FileNotFoundError, OSError):
            pass
        
        # Combine paths
        paths = []
        if system_path:
            paths.append(system_path)
        if user_path:
            paths.append(user_path)
        
        return os.pathsep.join(paths)
    else:
        # On Unix-like systems, use os.environ
        return os.environ.get("PATH", "")


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed."""
    import os
    import shutil
    
    # Refresh PATH from system environment
    system_path = _get_system_path()
    
    # Temporarily update PATH for this check
    old_path = os.environ.get("PATH", "")
    try:
        os.environ["PATH"] = system_path
        
        # Try to find ffmpeg in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            try:
                subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    check=True,
                    timeout=5,
                    env=os.environ.copy()
                )
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
    finally:
        os.environ["PATH"] = old_path
    
    # If not found, try common Windows installation paths
    if sys.platform == "win32":
        import pathlib
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            pathlib.Path.home() / r"ffmpeg\bin\ffmpeg.exe",
            pathlib.Path(r"C:\Users") / os.getenv("USERNAME", "user") / r"AppData\Local\Microsoft\WinGet\Packages" / r"Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*\bin\ffmpeg.exe",
        ]
        
        for path in common_paths:
            # Handle glob pattern
            if "*" in str(path):
                import glob
                matches = glob.glob(str(path))
                if matches:
                    path = matches[0]
            
            path_obj = pathlib.Path(path)
            if path_obj.exists():
                try:
                    subprocess.run(
                        [str(path_obj), "-version"],
                        capture_output=True,
                        check=True,
                        timeout=5
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    continue
    
    return False


def get_ffmpeg_path() -> str:
    """Get the path to FFmpeg executable."""
    import os
    import shutil
    
    # Refresh PATH from system environment
    system_path = _get_system_path()
    
    # Temporarily update PATH
    old_path = os.environ.get("PATH", "")
    try:
        os.environ["PATH"] = system_path
        
        # Try to find in PATH first
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
    finally:
        os.environ["PATH"] = old_path
    
    # Try common Windows installation paths
    if sys.platform == "win32":
        import pathlib
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            pathlib.Path.home() / r"ffmpeg\bin\ffmpeg.exe",
            pathlib.Path(r"C:\Users") / os.getenv("USERNAME", "user") / r"AppData\Local\Microsoft\WinGet\Packages" / r"Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*\bin\ffmpeg.exe",
        ]
        
        for path in common_paths:
            # Handle glob pattern
            if "*" in str(path):
                import glob
                matches = glob.glob(str(path))
                if matches:
                    path = matches[0]
            
            path_obj = pathlib.Path(path)
            if path_obj.exists():
                return str(path_obj)
    
    # Default to "ffmpeg" and let subprocess handle the error
    return "ffmpeg"


async def preprocess_audio(
    input_path: Path,
    output_path: Optional[Path] = None
) -> Path:
    """
    Preprocess audio file for optimal Whisper performance.
    
    Converts audio to:
    - 16kHz sample rate
    - Mono channel
    - WAV format
    
    Args:
        input_path: Path to input audio file
        output_path: Optional output path (creates temp file if not provided)
    
    Returns:
        Path to processed audio file
    """
    if not check_ffmpeg():
        logger.warning("FFmpeg not found, using original file without preprocessing")
        return input_path
    
    # Check if preprocessing is actually needed
    # This is a simplification; a full check would involve parsing ffprobe output
    # For now, assume if it's not 16kHz mono WAV, it needs processing.
    # This can be enhanced with ffprobe for more precise checks.
    if input_path.suffix.lower() == f".{WHISPER_FORMAT}" and \
       await get_audio_duration(input_path) > 0: # Basic check, can be improved
        logger.debug("Audio already in optimal format, skipping preprocessing", path=str(input_path))
        return input_path
    
    if output_path is None:
        # Create temporary output file
        temp_dir = Path(settings.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_path = temp_dir / f"processed_{input_path.stem}.wav"
    
    try:
        # Get FFmpeg path
        ffmpeg_executable = get_ffmpeg_path()
        
        # FFmpeg command to convert audio
        # -i: input file
        # -ar: sample rate (16kHz for Whisper)
        # -ac: audio channels (1 = mono)
        # -f: output format (wav)
        # -y: overwrite output file
        cmd = [
            ffmpeg_executable,
            "-i", str(input_path),
            "-ar", str(WHISPER_SAMPLE_RATE),
            "-ac", str(WHISPER_CHANNELS),
            "-f", WHISPER_FORMAT,
            "-y",  # Overwrite if exists
            str(output_path)
        ]
        
        logger.info("Preprocessing audio", input=str(input_path), output=str(output_path))
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minute timeout
        )
        
        if not output_path.exists():
            raise Exception("FFmpeg did not create output file")
        
        logger.info("Audio preprocessing completed", output=str(output_path), size=output_path.stat().st_size)
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg preprocessing failed", error=e.stderr, cmd=cmd)
        raise Exception(f"Audio preprocessing failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg preprocessing timeout")
        raise Exception("Audio preprocessing timed out")
    except Exception as e:
        logger.error("Audio preprocessing error", error=str(e))
        raise


async def get_audio_duration(file_path: Path) -> float:
    """Get audio file duration in seconds using FFmpeg."""
    if not check_ffmpeg():
        logger.warning("FFmpeg not found, cannot get audio duration")
        return 0.0
    
    try:
        ffmpeg_executable = get_ffmpeg_path()
        cmd = [
            ffmpeg_executable,
            "-i", str(file_path),
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            stderr=subprocess.STDOUT
        )
        
        # Parse duration from FFmpeg output
        # Format: Duration: HH:MM:SS.mmm
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                parts = duration_str.split(':')
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return total_seconds
        
        return 0.0
        
    except Exception as e:
        logger.warning("Could not get audio duration", error=str(e))
        return 0.0


async def save_uploaded_file(file_content: bytes, file_path: Path) -> None:
    """Save uploaded file content to disk."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    logger.debug("File saved", path=str(file_path), size=len(file_content))
