# How to Run Comprehensive System Tests

## Prerequisites

1. **Server must be running** on `http://localhost:3001`
2. **Docker** (recommended) or **local Python environment** with dependencies

## Running Tests

### Option 1: Inside Docker (Recommended)

```bash
# Start the services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
sleep 60

# Run tests inside backend container
docker-compose exec backend python test_system_comprehensive.py
```

### Option 2: With Local Python

```bash
# Install dependencies first
pip install -r requirements.txt

# Ensure server is running
# In one terminal: python -m uvicorn app.main:app --host 0.0.0.0 --port 3001

# In another terminal, run tests
cd backend
python test_system_comprehensive.py
```

### Option 3: Unit Tests Only (No Server Required)

```bash
# Run pytest unit tests (requires dependencies installed)
cd backend
pytest tests/ -v
```

## Test Results Interpretation

### ✅ All Tests Pass
- All features are working correctly
- Server is running latest code
- No issues found

### ⚠️ Some Tests Fail (Server Running Old Code)
- **CUDA fields missing**: Restart server to load new code
- **Rate limiting still enabled**: Restart server to load new code
- **Model not loaded**: Normal if server just started (preloading happens in background)

### ❌ Tests Cannot Connect
- Server is not running on `http://localhost:3001`
- Start server with: `docker-compose up` or `python -m uvicorn app.main:app`

### ⚠️ Import Errors
- Dependencies not installed locally
- Expected when running outside Docker
- Install with: `pip install -r requirements.txt`

## Expected Test Results (After Server Restart)

After restarting the server with new code:

```
TEST 1: HEALTH CHECK WITH GPU/CUDA DETECTION
  [PASS] Backend is healthy
  [PASS] CUDA Available: True/False
  [PASS] CUDA Device Count: 0/1/2...
  [PASS] All GPU/CUDA fields present in health response

TEST 2: RATE LIMITING DISABLED
  [PASS] Rate limiting is disabled (all requests succeeded)

TEST 3: CODE IMPLEMENTATION CHECKS
  [PASS] Found: best_of=5
  [PASS] Found: beam_size=10
  [PASS] Found: condition_on_previous_text
  [PASS] Found: initial_prompt
  [PASS] Found: no_speech_threshold
  [PASS] Found: post_processing
  [PASS] Preprocessing optimization check found
  [PASS] Rate limiting is commented out in config
  [PASS] Rate limiting configuration check passed

TEST 4: ERROR HANDLING
  [PASS] Invalid file extension rejected
  [PASS] Empty file rejected
  [PASS] Missing file parameter handled correctly

TEST 5: CONFIGURATION CHECKS
  [PASS] Transcription timeout correctly set (10 minutes)
  [PASS] Device set to 'auto' (will auto-detect GPU/CPU)
  [PASS] Model configured: large-v3

Total: 5/5 tests passed
ALL TESTS PASSED! System is fully functional.
```

## Troubleshooting

### Issue: "Cannot connect to backend"
**Solution**: Start the server:
```bash
docker-compose up
# OR
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001
```

### Issue: "CUDA fields missing" or "Rate limiting still enabled"
**Solution**: Server is running old code. Restart:
```bash
docker-compose down
docker-compose up --build -d
```

### Issue: "ModuleNotFoundError: No module named 'whisper'"
**Solution**: Install dependencies or run tests in Docker:
```bash
pip install -r requirements.txt
# OR
docker-compose exec backend python test_system_comprehensive.py
```

### Issue: "UnicodeEncodeError" on Windows
**Solution**: The test script handles this automatically, but if issues persist:
```powershell
$env:PYTHONIOENCODING='utf-8'
python test_system_comprehensive.py
```

## What the Tests Verify

1. ✅ GPU/CUDA detection and reporting
2. ✅ Rate limiting disabled for performance
3. ✅ Transcription parameters optimized (best_of=5, beam_size=10)
4. ✅ Post-processing implemented
5. ✅ Audio preprocessing optimization
6. ✅ Model preloading on startup
7. ✅ Memory monitoring and model selection
8. ✅ Error handling and validation
9. ✅ Configuration settings correct
10. ✅ Health check includes all required fields

## Success Criteria

- ✅ 5/5 tests pass
- ✅ CUDA fields present in health response
- ✅ Rate limiting disabled (no 429 errors)
- ✅ All code optimizations verified
- ✅ Server running latest code
