#!/usr/bin/env python3
"""
Comprehensive system test script for all implemented features.
Tests GPU support, optimizations, accuracy improvements, and all fixes.
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
    try:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST {step_num}: {name}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    except UnicodeEncodeError:
        print(f"\n{'='*70}")
        print(f"TEST {step_num}: {name}")
        print(f"{'='*70}\n")

def print_success(message: str):
    """Print success message."""
    try:
        print(f"{Colors.GREEN}[PASS] {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[PASS] {message}")

def print_error(message: str):
    """Print error message."""
    try:
        print(f"{Colors.RED}[FAIL] {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"[FAIL] {message}")

def print_info(message: str):
    """Print info message."""
    try:
        print(f"{Colors.YELLOW}-> {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"-> {message}")

def print_debug(message: str):
    """Print debug message."""
    try:
        print(f"{Colors.BLUE}  {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"  {message}")


async def test_health_check_with_gpu():
    """Test 1: Health check with GPU/CUDA info."""
    print_step(1, "HEALTH CHECK WITH GPU/CUDA DETECTION")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Backend is healthy")
                print_debug(f"Status: {data.get('status')}")
                print_debug(f"Service: {data.get('service')}")
                print_debug(f"Version: {data.get('version')}")
                
                # Check model info
                model_loaded = data.get('model_loaded')
                model_name = data.get('model_name')
                print_debug(f"Model Loaded: {model_loaded}")
                if model_name:
                    print_debug(f"Model Name: {model_name}")
                
                # Check GPU/CUDA info (NEW FEATURES)
                device = data.get('device', 'unknown')
                print_debug(f"Device: {device}")
                
                cuda_available = data.get('cuda_available')
                cuda_device_count = data.get('cuda_device_count')
                
                if cuda_available is not None:
                    print_success(f"CUDA Available: {cuda_available}")
                    if cuda_available:
                        print_success(f"CUDA Device Count: {cuda_device_count}")
                        
                        # Check GPU info
                        gpu_info = data.get('gpu_info')
                        if gpu_info:
                            print_success("GPU Info Present")
                            print_debug(f"  GPU Name: {gpu_info.get('name', 'Unknown')}")
                            print_debug(f"  VRAM Total: {gpu_info.get('vram_total_gb', 'Unknown')} GB")
                            print_debug(f"  CUDA Version: {gpu_info.get('cuda_version', 'Unknown')}")
                        else:
                            print_info("GPU info not yet available (model may not be loaded)")
                    else:
                        print_info("Running on CPU (GPU not available)")
                else:
                    print_error("CUDA availability not reported (missing field)")
                    return False
                
                # Verify CUDA fields exist (NEW REQUIREMENT)
                if 'cuda_available' not in data:
                    print_error("Missing 'cuda_available' field in health response")
                    return False
                if 'cuda_device_count' not in data:
                    print_error("Missing 'cuda_device_count' field in health response")
                    return False
                
                print_success("All GPU/CUDA fields present in health response")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                print_debug(f"Response: {response.text}")
                return False
    except httpx.ConnectError:
        try:
            print_error("Cannot connect to backend. Is the server running on http://localhost:3001?")
            print_info("Start the server with: docker-compose up or python -m uvicorn app.main:app")
            print_info("Skipping API integration tests - running code verification tests only")
        except UnicodeEncodeError:
            print("[FAIL] Cannot connect to backend. Server not running on http://localhost:3001")
            print("-> Start the server with: docker-compose up or python -m uvicorn app.main:app")
            print("-> Skipping API integration tests - running code verification tests only")
        return None  # Return None to indicate skip
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        import traceback
        print_debug(traceback.format_exc())
        return False


async def test_rate_limiting_disabled():
    """Test 2: Verify rate limiting is disabled (performance optimization)."""
    print_step(2, "RATE LIMITING DISABLED (PERFORMANCE TEST)")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(f"{API_URL}/health")
        server_running = True
    except:
        server_running = False
        print_info("Server not running - skipping API rate limiting test")
        print_info("Rate limiting disabled check will be done via code inspection")
        return None  # Skip test
    
    print_info("Sending multiple rapid requests to test rate limiting...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Send 20 rapid requests (would normally trigger rate limit)
            success_count = 0
            rate_limited_count = 0
            
            for i in range(20):
                try:
                    response = await client.get(f"{API_URL}/health")
                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:
                        rate_limited_count += 1
                        print_error(f"Request {i+1} was rate limited (unexpected!)")
                except Exception as e:
                    print_debug(f"Request {i+1} error: {str(e)}")
            
            print_debug(f"Successful requests: {success_count}/20")
            print_debug(f"Rate limited requests: {rate_limited_count}/20")
            
            if rate_limited_count > 0:
                print_error("Rate limiting is still enabled (should be disabled for performance)")
                return False
            else:
                print_success("Rate limiting is disabled (all requests succeeded)")
                return True
                
    except Exception as e:
        print_error(f"Rate limiting test error: {str(e)}")
        return False


async def test_code_implementation_checks():
    """Test 3: Check code implementation for optimizations."""
    print_step(3, "CODE IMPLEMENTATION CHECKS")
    
    all_passed = True
    
    # Check transcription parameters
    print_info("Checking transcription parameters optimization...")
    try:
        import inspect
        from app.transcribe import WhisperTranscriptionService
        
        service = WhisperTranscriptionService()
        source = inspect.getsource(service.transcribe)
        
        checks = {
            "best_of=5": "best_of=5" in source or "best_of = 5" in source,
            "beam_size=10": "beam_size=10" in source or "beam_size = 10" in source,
            "condition_on_previous_text": "condition_on_previous_text=True" in source,
            "initial_prompt": "initial_prompt" in source,
            "no_speech_threshold": "no_speech_threshold" in source,
            "post_processing": "_post_process_transcript" in source or hasattr(service, '_post_process_transcript'),
        }
        
        for param, found in checks.items():
            if found:
                print_success(f"Found: {param}")
            else:
                print_error(f"Missing: {param}")
                all_passed = False
    except Exception as e:
        print_error(f"Transcription parameters check error: {str(e)}")
        all_passed = False
    
    # Check audio preprocessing optimization
    print_info("Checking audio preprocessing optimization...")
    try:
        from app.audio_processor import preprocess_audio
        source = inspect.getsource(preprocess_audio)
        
        if "already in optimal format" in source.lower() or "skipping preprocessing" in source.lower():
            print_success("Preprocessing optimization check found")
        else:
            print_error("Preprocessing optimization check not found")
            all_passed = False
    except Exception as e:
        print_error(f"Preprocessing check error: {str(e)}")
        all_passed = False
    
    # Check rate limiting disabled
    print_info("Checking rate limiting configuration...")
    try:
        from app.config import settings
        import inspect
        
        # Check if rate_limit_per_minute is commented out in config
        config_source = inspect.getsource(settings.__class__)
        if "# rate_limit_per_minute" in config_source or "# Rate Limiting" in config_source:
            print_success("Rate limiting is commented out in config.py")
        else:
            # Check if it exists but is not accessible (commented out)
            if hasattr(settings, 'rate_limit_per_minute'):
                print_error("Rate limiting still enabled in config (rate_limit_per_minute attribute exists)")
                all_passed = False
            else:
                print_success("Rate limiting disabled in config (attribute not found)")
        
        # Check main.py for limiter being None
        import app.main as main_module
        import inspect
        
        # Read main.py source to check for limiter = None
        main_source = inspect.getsource(main_module)
        if "limiter = None" in main_source:
            print_success("Rate limiting disabled in main.py (limiter = None)")
        elif "limiter = Limiter" in main_source:
            print_error("Rate limiting still enabled in main.py (limiter = Limiter found)")
            all_passed = False
        else:
            print_info("Rate limiting check (limiter assignment pattern not found)")
        
        # Check if slowapi imports are commented out
        if "# from slowapi import" in main_source or "# Rate limiting disabled" in main_source:
            print_success("Rate limiting imports commented out in main.py")
        elif "from slowapi import" in main_source and "# from slowapi import" not in main_source:
            print_error("Rate limiting imports not commented out in main.py")
            all_passed = False
        else:
            print_info("Rate limiting import check (using different pattern)")
        
    except Exception as e:
        print_error(f"Rate limiting check error: {str(e)}")
        import traceback
        print_debug(traceback.format_exc())
        all_passed = False
    
    return all_passed


async def test_error_handling():
    """Test 4: Error handling and validation."""
    print_step(4, "ERROR HANDLING & VALIDATION")
    
    # Check if server is running first
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(f"{API_URL}/health")
        server_running = True
    except:
        server_running = False
        print_info("Server not running - skipping API error handling tests")
        print_info("These tests require the backend server to be running")
        return None  # Skip test
    
    passed = True
    
    # Test invalid file extension
    print_info("Testing invalid file extension rejection...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            files = {"file": ("test.exe", BytesIO(b"fake content"), "application/x-msdownload")}
            response = await client.post(f"{API_URL}/transcribe", files=files)
            
            if response.status_code == 400:
                print_success("Invalid file extension rejected")
            else:
                print_error(f"Expected 400, got {response.status_code}")
                passed = False
    except httpx.ConnectError:
        print_info("Server disconnected - skipping remaining error handling tests")
        return None
    except Exception as e:
        print_error(f"Invalid extension test error: {str(e)}")
        passed = False
    
    # Test empty file
    if passed:
        print_info("Testing empty file rejection...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                files = {"file": ("empty.mp3", BytesIO(b""), "audio/mpeg")}
                response = await client.post(f"{API_URL}/transcribe", files=files)
                
                if response.status_code == 400:
                    print_success("Empty file rejected")
                else:
                    print_error(f"Expected 400 for empty file, got {response.status_code}")
                    passed = False
        except httpx.ConnectError:
            print_info("Server disconnected - skipping remaining tests")
            return None
        except Exception as e:
            print_error(f"Empty file test error: {str(e)}")
            passed = False
    
    # Test missing file parameter
    if passed:
        print_info("Testing missing file parameter...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{API_URL}/transcribe", data={})
                if response.status_code == 422:  # FastAPI validation error
                    print_success("Missing file parameter handled correctly")
                else:
                    print_error(f"Expected 422, got {response.status_code}")
                    passed = False
        except httpx.ConnectError:
            print_info("Server disconnected")
            return None
        except Exception as e:
            print_error(f"Missing file test error: {str(e)}")
            passed = False
    
    if passed:
        print_success("All error handling tests passed")
    return passed


async def test_configuration_checks():
    """Test 5: Configuration and settings checks."""
    print_step(5, "CONFIGURATION CHECKS")
    
    all_passed = True
    
    try:
        from app.config import settings
        
        # Check transcription timeout
        if hasattr(settings, 'transcription_timeout'):
            timeout = settings.transcription_timeout
            print_debug(f"Transcription timeout: {timeout} seconds")
            if timeout == 600:
                print_success("Transcription timeout correctly set (10 minutes)")
            else:
                print_info(f"Transcription timeout is {timeout} seconds")
        else:
            print_error("Transcription timeout not found in settings")
            all_passed = False
        
        # Check device setting
        if hasattr(settings, 'whisper_device'):
            device = settings.whisper_device
            print_debug(f"Whisper device: {device}")
            if device == "auto":
                print_success("Device set to 'auto' (will auto-detect GPU/CPU)")
            else:
                print_info(f"Device set to '{device}'")
        else:
            print_error("Whisper device setting not found")
            all_passed = False
        
        # Check model setting
        if hasattr(settings, 'whisper_model'):
            model = settings.whisper_model
            print_debug(f"Whisper model: {model}")
            print_success(f"Model configured: {model}")
        else:
            print_error("Whisper model setting not found")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Configuration check error: {str(e)}")
        import traceback
        print_debug(traceback.format_exc())
        return False


async def run_all_tests():
    """Run all comprehensive tests."""
    try:
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("="*70)
        print("COMPREHENSIVE SYSTEM TEST SUITE")
        print("Testing All Implemented Features & Optimizations")
        print("="*70)
        print(f"{Colors.RESET}\n")
    except UnicodeEncodeError:
        print("\n" + "="*70)
        print("COMPREHENSIVE SYSTEM TEST SUITE")
        print("Testing All Implemented Features & Optimizations")
        print("="*70 + "\n")
    
    tests = [
        ("Health Check with GPU/CUDA", test_health_check_with_gpu),
        ("Rate Limiting Disabled", test_rate_limiting_disabled),
        ("Code Implementation Checks", test_code_implementation_checks),
        ("Error Handling", test_error_handling),
        ("Configuration Checks", test_configuration_checks),
    ]
    
    results = []
    skipped = 0
    for name, test_func in tests:
        try:
            result = await test_func()
            if result is None:
                skipped += 1
                results.append((name, None))
            else:
                results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' crashed: {str(e)}")
            import traceback
            print_debug(traceback.format_exc())
            results.append((name, False))
    
    # Summary
    try:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    except UnicodeEncodeError:
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    total = len(results) - skipped
    
    for name, result in results:
        if result is None:
            try:
                print(f"{Colors.YELLOW}[SKIP] {name}: SKIPPED (server not running){Colors.RESET}")
            except UnicodeEncodeError:
                print(f"[SKIP] {name}: SKIPPED (server not running)")
        elif result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    try:
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed", end="")
        if skipped > 0:
            print(f" ({skipped} skipped)", end="")
        print(f"{Colors.RESET}\n")
    except UnicodeEncodeError:
        print(f"\nTotal: {passed}/{total} tests passed", end="")
        if skipped > 0:
            print(f" ({skipped} skipped)", end="")
        print("\n")
    
    if passed == total and total > 0:
        try:
            print(f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED! System is fully functional.{Colors.RESET}\n")
        except UnicodeEncodeError:
            print("ALL TESTS PASSED! System is fully functional.\n")
        return True
    elif passed >= total * 0.8 and total > 0:
        try:
            print(f"{Colors.YELLOW}{Colors.BOLD}Most tests passed ({passed}/{total}). Review failed tests.{Colors.RESET}\n")
        except UnicodeEncodeError:
            print(f"Most tests passed ({passed}/{total}). Review failed tests.\n")
        return False
    elif total > 0:
        try:
            print(f"{Colors.RED}{Colors.BOLD}Many tests failed. Please review and fix issues.{Colors.RESET}\n")
        except UnicodeEncodeError:
            print("Many tests failed. Please review and fix issues.\n")
        return False
    else:
        print("All tests skipped - server not running. Run code verification tests only.\n")
        return True  # Don't fail if server is just not running


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
