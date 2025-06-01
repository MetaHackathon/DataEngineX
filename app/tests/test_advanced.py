#!/usr/bin/env python3
import subprocess
import time
import requests
import sys
import json

def test_advanced_endpoints():
    """Test advanced DataEngineX functionality"""
    print("🚀 Starting DataEngineX server for advanced tests...")
    
    # Start server
    proc = subprocess.Popen([
        'python3', '-m', 'uvicorn', 'main:app', 
        '--port', '8080', '--host', '127.0.0.1'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(6)
    
    try:
        base_url = "http://127.0.0.1:8080"
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Search Functionality
        print("\n1️⃣ Testing Library Search...")
        try:
            search_data = {
                "query": "transformer",
                "search_types": ["papers", "annotations"],
                "limit": 10
            }
            response = requests.post(f"{base_url}/api/search", json=search_data, timeout=10)
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Search passed: Found {len(results.get('results', []))} results")
                tests_passed += 1
            else:
                print(f"❌ Search failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Search error: {e}")
            tests_failed += 1
        
        # Test 2: Quick Search
        print("\n2️⃣ Testing Quick Search...")
        try:
            response = requests.get(f"{base_url}/api/search/quick?q=attention", timeout=10)
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Quick search passed: Found {len(results.get('results', []))} results")
                tests_passed += 1
            else:
                print(f"❌ Quick search failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Quick search error: {e}")
            tests_failed += 1
        
        # Test 3: Chat Session Creation
        print("\n3️⃣ Testing Chat Session Creation...")
        try:
            chat_data = {
                "session_type": "library",
                "title": "Test Chat Session"
            }
            response = requests.post(f"{base_url}/api/chat/sessions", json=chat_data, timeout=10)
            if response.status_code == 200:
                session = response.json()
                print(f"✅ Chat session created: {session.get('session_id')}")
                tests_passed += 1
                
                # Test 4: Send Chat Message
                print("\n4️⃣ Testing Chat Message...")
                message_data = {
                    "session_id": session.get('session_id'),
                    "message": "What are the main topics in my library?"
                }
                response = requests.post(f"{base_url}/api/chat/message", json=message_data, timeout=15)
                if response.status_code == 200:
                    chat_response = response.json()
                    print(f"✅ Chat message sent: Got response with {len(chat_response.get('content', ''))} chars")
                    tests_passed += 1
                else:
                    print(f"❌ Chat message failed: {response.status_code}")
                    tests_failed += 1
            else:
                print(f"❌ Chat session failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Chat error: {e}")
            tests_failed += 1
        
        # Test 5: Library Stats
        print("\n5️⃣ Testing Library Stats...")
        try:
            response = requests.get(f"{base_url}/api/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Stats passed: {stats.get('total_papers', 0)} papers in library")
                tests_passed += 1
            else:
                print(f"❌ Stats failed: {response.status_code}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ Stats error: {e}")
            tests_failed += 1
        
        # Test Results
        print(f"\n📊 ADVANCED TEST RESULTS:")
        print(f"✅ Passed: {tests_passed}")
        print(f"❌ Failed: {tests_failed}")
        print(f"📈 Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")
        
        if tests_passed >= 4:
            print("\n🎉 Advanced DataEngineX features are functional!")
            return True
        else:
            print("\n⚠️ Some advanced tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Advanced test suite error: {e}")
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
    success = test_advanced_endpoints()
    sys.exit(0 if success else 1) 