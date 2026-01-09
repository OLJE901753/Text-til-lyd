# Backend Dockerfile for Audio Transcription API
FROM python:3.13-slim

# Install system dependencies including FFmpeg and Git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Configure pip to suppress warnings
ENV PIP_NO_WARN_SCRIPT_LOCATION=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=100
# Set TMPDIR to isolated location for easier cleanup
ENV TMPDIR=/tmp/pip-tmp

# Copy pip configuration and requirements
COPY pip.conf /etc/pip.conf
COPY requirements.txt .

# Install Python dependencies with optimized settings
# OPTIMIZATION: Install PyTorch CPU-only FIRST to avoid CUDA dependencies
# This reduces image size from ~4.5GB to ~1.5GB and speeds up build time
# Since we use WHISPER_DEVICE=cpu, we don't need CUDA libraries
RUN mkdir -p /tmp/pip-tmp && \
    # Install PyTorch CPU-only version first (much smaller, no CUDA libraries)
    pip install --no-cache-dir --no-warn-script-location \
    --disable-pip-version-check \
    --progress-bar off \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchaudio && \
    # Install other dependencies (Whisper will use the already-installed PyTorch CPU)
    pip install --no-cache-dir --no-warn-script-location \
    --disable-pip-version-check \
    --progress-bar off \
    -r requirements.txt 2>&1 | grep -vE "WARNING: Failed to remove|You can safely remove" || pip install --no-cache-dir --no-warn-script-location --disable-pip-version-check --progress-bar off -r requirements.txt && \
    # Clean up pip cache and temp files aggressively
    pip cache purge 2>/dev/null || true && \
    rm -rf /tmp/pip-tmp/* /tmp/pip-* /tmp/*.tmp /tmp/pip-build-tracker-* /tmp/pip-unpack-* /tmp/pip-metadata-* 2>/dev/null || true && \
    # Remove pip.conf after installation (not needed in final image)
    rm -f /etc/pip.conf && \
    # Final cleanup of any remaining pip temp directories
    find /tmp -maxdepth 1 -type d -name "pip-*" -exec rm -rf {} + 2>/dev/null || true

# Copy application code
COPY app/ ./app/
COPY pytest.ini .

# Create directories for models and temp files
RUN mkdir -p /app/models /app/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV WHISPER_DOWNLOAD_ROOT=/app/models
ENV TEMP_DIR=/app/temp
# Memory and performance optimizations
ENV PYTHONHASHSEED=0
ENV OMP_NUM_THREADS=2
ENV MKL_NUM_THREADS=2
ENV NUMEXPR_NUM_THREADS=2

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:3001/api/health', timeout=5)" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
