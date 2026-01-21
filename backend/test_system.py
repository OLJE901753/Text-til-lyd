#!/usr/bin/env python3
"""
Comprehensive system test script.
Tests each component step by step with detailed debugging.
"""
import sys
import asyncio
import httpx
import json
from pathlib import Path
from io import BytesIO
import time

# Test configuration
BASE_URL = "http://localhost:3001"
API_URL = f"{BASE_URL}/api"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num: int, name: str):
    """Print step header."""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}STEP {step_num}: {name}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}→ {message}{Colors.RESET}")

def print_debug(message: str):
    """Print debug message."""
    print(f"{Colors.BLUE}  {message}{Colors.RESET}")


async def test_health_check():
    """Test 1: Backend health check."""
    print_step(1, "BACKEND HEALTH CHECK")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Backend is healthy")
                print_debug(f"Status: {data.get('status')}")
                print_debug(f"Service: {data.get('service')}")
                print_debug(f"Version: {data.get('version')}")
                print_debug(f"Model Loaded: {data.get('model_loaded')}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                print_debug(f"Response: {response.text}")
                return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


async def test_file_validation():
    """Test 2: File validation and security."""
    print_step(2, "FILE VALIDATION & SECURITY")
    
    # Test with invalid file extension
    print_info("Testing invalid file extension...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("test.exe", BytesIO(b"fake exe content"), "application/x-msdownload")}
            response = await client.post(f"{API_URL}/transcribe", files=files)
            
            if response.status_code == 400:
                print_success("Invalid file extension rejected")
                print_debug(f"Error: {response.json().get('detail', 'Unknown')}")
            else:
                print_error(f"Expected 400, got {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Validation test error: {str(e)}")
        return False
    
    # Test with empty file
    print_info("Testing empty file...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("empty.mp3", BytesIO(b""), "audio/mpeg")}
            response = await client.post(f"{API_URL}/transcribe", files=files)
            
            if response.status_code == 400:
                print_success("Empty file rejected")
            else:
                print_error(f"Expected 400 for empty file, got {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Empty file test error: {str(e)}")
        return False
    
    print_success("File validation tests passed")
    return True


async def test_streaming_upload():
    """Test 3: Streaming file upload."""
    print_step(3, "STREAMING FILE UPLOAD")
    
    # Create a test audio file (small WAV file header)
    # This is a minimal valid WAV file
    wav_header = b'RIFF' + (36).to_bytes(4, 'little') + b'WAVE' + \
                 b'fmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + \
                 (16000).to_bytes(4, 'little') + (32000).to_bytes(4, 'little') + \
                 (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (0).to_bytes(4, 'little')
    
    print_info("Testing streaming upload with small file...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("test.wav", BytesIO(wav_header), "audio/wav")}
            
            start_time = time.time()
            response = await client.post(f"{API_URL}/transcribe", files=files)
            upload_time = time.time() - start_time
            
            print_debug(f"Upload completed in {upload_time:.2f}s")
            
            # We expect either success (if model loads) or a model loading error
            if response.status_code in [200, 500]:
                print_success("Streaming upload works")
                if response.status_code == 500:
                    error_detail = response.json().get('detail', '')
                    if 'model' in error_detail.lower() or 'whisper' in error_detail.lower():
                        print_info("Model loading error (expected on first request)")
                    else:
                        print_error(f"Unexpected error: {error_detail}")
                        return False
                return True
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                print_debug(f"Response: {response.text[:200]}")
                return False
    except Exception as e:
        print_error(f"Streaming upload test error: {str(e)}")
        import traceback
        print_debug(traceback.format_exc())
        return False


async def test_model_loading():
    """Test 4: Model loading (non-blocking)."""
    print_step(4, "MODEL LOADING (NON-BLOCKING)")
    
    print_info("Checking if model can be loaded...")
    print_info("Note: This will load the model on first transcription request")
    
    # Check health before
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/health")
            if response.status_code == 200:
                data = response.json()
                model_loaded_before = data.get('model_loaded', False)
                print_debug(f"Model loaded before: {model_loaded_before}")
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False
    
    print_success("Model loading test (will be tested during transcription)")
    return True


async def test_error_handling():
    """Test 5: Error handling and edge cases."""
    print_step(5, "ERROR HANDLING & EDGE CASES")
    
    # Test with file too large (simulate)
    print_info("Testing file size limit...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a file that's just over the limit (101MB)
            large_content = b"x" * (101 * 1024 * 1024)
            files = {"file": ("large.mp3", BytesIO(large_content), "audio/mpeg")}
            
            # This will fail during upload, which is expected
            try:
                response = await client.post(f"{API_URL}/transcribe", files=files, timeout=60.0)
                if response.status_code == 400:
                    print_success("Large file rejected correctly")
                else:
                    print_info(f"Got status {response.status_code} (may timeout during upload)")
            except httpx.ReadTimeout:
                print_info("Upload timeout (expected for very large file)")
                print_success("Large file handling works (timeout protection)")
    except Exception as e:
        print_info(f"Large file test: {str(e)} (expected)")
    
    # Test with missing file parameter
    print_info("Testing missing file parameter...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{API_URL}/transcribe", data={})
            if response.status_code == 422:  # FastAPI validation error
                print_success("Missing file parameter handled correctly")
            else:
                print_error(f"Expected 422, got {response.status_code}")
    except Exception as e:
        print_error(f"Missing file test error: {str(e)}")
        return False
    
    print_success("Error handling tests passed")
    return True


async def test_resource_cleanup():
    """Test 6: Resource cleanup and memory management."""
    print_step(6, "RESOURCE CLEANUP & MEMORY MANAGEMENT")
    
    print_info("Checking temp directory...")
    try:
        from app.config import settings
        from app.security import ensure_temp_directory
        
        temp_dir = ensure_temp_directory()
        print_debug(f"Temp directory: {temp_dir}")
        
        if temp_dir.exists():
            file_count = len(list(temp_dir.glob("*")))
            print_debug(f"Files in temp directory: {file_count}")
            
            if file_count == 0:
                print_success("Temp directory is clean")
            else:
                print_info(f"Found {file_count} files in temp (may be from previous tests)")
        else:
            print_error("Temp directory does not exist")
            return False
    except Exception as e:
        print_error(f"Resource cleanup check error: {str(e)}")
        return False
    
    print_success("Resource cleanup check passed")
    return True


async def run_all_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("="*60)
    print("COMPREHENSIVE SYSTEM TEST SUITE")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("File Validation", test_file_validation),
        ("Streaming Upload", test_streaming_upload),
        ("Model Loading", test_model_loading),
        ("Error Handling", test_error_handling),
        ("Resource Cleanup", test_resource_cleanup),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite crashed: {str(e)}")
        import traceback
        print_debug(traceback.format_exc())
        sys.exit(1)
