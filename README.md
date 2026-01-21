# Text til lyd - Audio Transcription Application

World-class audio transcription application for Norwegian and English audio files with 90-95% accuracy using OpenAI Whisper.

## Features

- 🎯 **High Accuracy**: 90-95% transcription accuracy for Norwegian/English
- 🔒 **Secure**: File validation, rate limiting, and secure temp handling
- ⚡ **Fast**: Model caching, audio preprocessing, and optimized responses
- 🎨 **Beautiful UI**: Modern dark theme with lime green accents
- 📱 **Responsive**: Works on desktop and mobile devices
- ♿ **Accessible**: Full keyboard navigation and screen reader support
- 📤 **Export**: Download transcripts as TXT, SRT, or VTT formats

## Architecture

- **Frontend**: React + Vite with TypeScript, Tailwind CSS, and shadcn/ui
- **Backend**: Python FastAPI with OpenAI Whisper (local)
- **Transcription**: Whisper large-v3 model with singleton caching

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Node.js**: 20 or higher
- **FFmpeg**: Required for audio preprocessing
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg` (Ubuntu/Debian)
- **RAM**: Minimum 4GB (8GB+ recommended for large Whisper models)
- **Disk Space**: ~10GB for Whisper large-v3 model

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file from example:
```bash
cp .env.example .env
```

6. Edit `.env` file with your configuration (optional):
```env
WHISPER_MODEL=large-v3
MAX_FILE_SIZE_MB=100
RATE_LIMIT_PER_MINUTE=10
```

### Frontend Setup

1. Install dependencies:
```bash
npm install
# or
pnpm install
```

2. Create `.env` file (optional, uses defaults):
```env
VITE_API_URL=http://localhost:3001
```

## Running the Application

### Development Mode

1. **Start the backend** (in `backend/` directory):
```bash
python -m uvicorn app.main:app --reload
```
Backend will run on `http://localhost:3001`

2. **Start the frontend** (in project root):
```bash
npm run dev
```
Frontend will run on `http://localhost:8081`

3. Open your browser and navigate to `http://localhost:8081`

### Production Build

1. **Build the frontend**:
```bash
npm run build
```

2. **Start the backend**:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001
```

3. Serve the frontend `dist/` folder with a web server (nginx, Apache, etc.)

### Docker Deployment

#### Prerequisites
- Docker Desktop installed (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (included with Docker Desktop)

#### Development with Docker

1. **Start both services** (backend + frontend):
```bash
docker-compose -f docker-compose.dev.yml up --build
```

2. **Access the application**:
   - Frontend: `http://localhost:8081`
   - Backend API: `http://localhost:3001`
   - API Health: `http://localhost:3001/api/health`

3. **Stop services**:
```bash
docker-compose -f docker-compose.dev.yml down
```

#### Production with Docker

1. **Build and start production services**:
```bash
docker-compose up --build -d
```

2. **Access the application**:
   - Frontend: `http://localhost:8080`
   - Backend API: `http://localhost:3001`
   - API Health: `http://localhost:3001/api/health`

3. **View logs**:
```bash
docker-compose logs -f
```

4. **Stop services**:
```bash
docker-compose down
```

#### Docker Commands

- **View running containers**: `docker-compose ps`
- **Rebuild containers**: `docker-compose build --no-cache`
- **Remove volumes** (including Whisper models): `docker-compose down -v`
- **View backend logs**: `docker-compose logs -f backend`
- **View frontend logs**: `docker-compose logs -f frontend`

#### Docker Volumes

- **whisper-models**: Persists downloaded Whisper models between container restarts
- **temp-files**: Temporary audio files (cleared on container restart)

#### Environment Variables

You can override environment variables by creating a `.env` file or using Docker Compose environment variables. See `docker-compose.yml` for available options.

## Usage

1. **Upload Audio File**:
   - Drag and drop an audio file onto the upload area
   - Or click to browse and select a file
   - Supported formats: M4A, MP3, WAV, WEBM, OGG
   - Maximum file size: 100MB

2. **Wait for Transcription**:
   - File uploads with progress indicator
   - Audio is preprocessed for optimal accuracy
   - Transcription happens automatically
   - Progress is shown in real-time

3. **View and Export**:
   - View the transcript with language detection
   - Copy to clipboard with one click
   - Download as TXT, SRT, or VTT format
   - Play audio preview

## API Documentation

### Endpoints

#### `POST /api/transcribe`

Transcribe an audio file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Audio file (required)
  - `language`: Language code (optional, e.g., "no", "en")

**Response:**
```json
{
  "transcript": "Transcribed text...",
  "language": "no",
  "confidence": 0.95,
  "duration": 120.5,
  "segments": [...],
  "model": "large-v3"
}
```

#### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "audio-transcription-api",
  "version": "1.0.0",
  "model_loaded": true,
  "model_name": "large-v3"
}
```

## Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Whisper Model (base, small, medium, large, large-v3)
WHISPER_MODEL=large-v3

# File Upload
MAX_FILE_SIZE_MB=100
ALLOWED_AUDIO_TYPES=m4a,mp3,wav,webm,ogg

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend Configuration

Edit `.env`:

```env
VITE_API_URL=http://localhost:3001
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
npm run test
```

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpeg not found`

**Solution**: Install FFmpeg and ensure it's in your system PATH.

### Model Download Issues

**Error**: Model download fails or is slow

**Solution**: 
- First download can take time (models are large)
- Check internet connection
- Models are cached after first download

### Memory Issues

**Error**: Out of memory during transcription

**Solution**:
- Use a smaller Whisper model (e.g., "base" instead of "large-v3")
- Close other applications
- Increase system RAM

### CORS Errors

**Error**: CORS policy errors in browser

**Solution**: 
- Ensure backend CORS_ORIGINS includes your frontend URL
- Check that backend is running on correct port

## Performance Tips

1. **Model Selection**: 
   - `base`: Fastest, lower accuracy
   - `large-v3`: Best accuracy, slower, more memory

2. **First Request**: Model loads on first transcription (takes ~5-10 seconds)

3. **Subsequent Requests**: Model is cached, much faster

4. **Large Files**: Consider splitting very long audio files

## Security

- File type validation using magic bytes (not just extension)
- File size limits to prevent DoS
- Rate limiting to prevent abuse
- Secure temporary file handling
- Input sanitization
- CORS configuration

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
