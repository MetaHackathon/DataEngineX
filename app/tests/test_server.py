#!/usr/bin/env python3
import subprocess
import time
import requests
import sys
import json

def test_server():
    """Test DataEngineX API endpoints"""
    print("🚀 Starting DataEngineX server...")
    
    # Start server
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'main:app', 
        '--port', '8080', '--host', '127.0.0.1'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(8)
    
    try:
        base_url = "http://127.0.0.1:8080"
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Health check passed: {response.json()}")
                tests_passed += 1
            else:
                print(f"❌ Health check failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Health check error: {e}")
            tests_failed += 1
        
        # Test 2: Root Endpoint
        print("\n2️⃣ Testing Root Endpoint...")
        try:
            response = requests.get(f"{base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint passed: {data['message']}")
                tests_passed += 1
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            tests_failed += 1
        
        # Test 3: ArXiv Discovery
        print("\n3️⃣ Testing ArXiv Discovery...")
        try:
            response = requests.get(f"{base_url}/api/discover?q=transformer&limit=3", timeout=15)
            if response.status_code == 200:
                papers = response.json()
                print(f"✅ ArXiv discovery passed: Found {len(papers)} papers")
                if papers:
                    print(f"   📄 First paper: {papers[0]['title'][:50]}...")
                tests_passed += 1
            else:
                print(f"❌ ArXiv discovery failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ ArXiv discovery error: {e}")
            tests_failed += 1
        
        # Test 4: Trending Papers
        print("\n4️⃣ Testing Trending Papers...")
        try:
            response = requests.get(f"{base_url}/api/discover/trending?limit=5", timeout=15)
            if response.status_code == 200:
                papers = response.json()
                print(f"✅ Trending papers passed: Found {len(papers)} papers")
                tests_passed += 1
            else:
                print(f"❌ Trending papers failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Trending papers error: {e}")
            tests_failed += 1
            
        # Test 5: Library Access (with demo user)
        print("\n5️⃣ Testing Library Access...")
        try:
            response = requests.get(f"{base_url}/api/library", timeout=10)
            if response.status_code == 200:
                library = response.json()
                print(f"✅ Library access passed: {len(library)} papers in demo library")
                tests_passed += 1
            else:
                print(f"❌ Library access failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Library access error: {e}")
            tests_failed += 1
        
        # Test Results
        print(f"\n📊 TEST RESULTS:")
        print(f"✅ Passed: {tests_passed}")
        print(f"❌ Failed: {tests_failed}")
        print(f"📈 Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
        
        if tests_passed >= 4:
            print("\n🎉 DataEngineX API is functional!")
            return True
        else:
            print("\n⚠️ Some tests failed - check implementation")
            return False
            
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        return False
        
    finally:
        # Cleanup
        print("\n🛑 Stopping server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("✅ Server stopped")

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1) 