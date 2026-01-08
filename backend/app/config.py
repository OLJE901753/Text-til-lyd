"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 3001
    api_reload: bool = True
    
    # CORS Configuration
    cors_origins: str = "http://localhost:8081,http://127.0.0.1:8081"
    
    # Whisper Configuration
    whisper_model: str = "large-v3"
    whisper_device: str = "cpu"
    whisper_download_root: str = "./models"
    
    # File Upload Configuration
    max_file_size_mb: int = 100
    allowed_audio_types: str = "m4a,mp3,wav,webm,ogg"
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Security
    temp_dir: str = "./temp"
    cleanup_temp_files: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_audio_types_list(self) -> List[str]:
        """Parse allowed audio types string into list."""
        return [ext.strip().lower() for ext in self.allowed_audio_types.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
