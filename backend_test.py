import requests
import sys
import json
import time
from datetime import datetime

class SmartCodeGeneratorAPITester:
    def __init__(self, base_url="https://codecraft-38.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.generated_files = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_optimize_prompt(self, prompt):
        """Test prompt optimization with Gemini API"""
        success, response = self.run_test(
            "Optimize Prompt (Gemini API)",
            "POST",
            "api/optimize-prompt",
            200,
            data={"prompt": prompt},
            timeout=60  # Longer timeout for LLM API
        )
        
        if success and response:
            # Validate response structure
            required_keys = ['original_prompt', 'optimized_prompt', 'session_id']
            if all(key in response for key in required_keys):
                self.session_id = response['session_id']
                print(f"   Session ID: {self.session_id}")
                print(f"   Original prompt length: {len(response['original_prompt'])}")
                print(f"   Optimized prompt length: {len(response['optimized_prompt'])}")
                
                # Check if optimization actually happened
                if len(response['optimized_prompt']) > len(response['original_prompt']):
                    print("   ✅ Prompt was successfully optimized (expanded)")
                else:
                    print("   ⚠️  Optimized prompt is not longer than original")
                
                return True, response
            else:
                print(f"   ❌ Missing required keys in response: {required_keys}")
                return False, {}
        
        return success, response

    def test_generate_code(self, optimized_prompt):
        """Test code generation with Claude API"""
        if not self.session_id:
            print("❌ No session ID available for code generation")
            return False, {}

        success, response = self.run_test(
            "Generate Code (Claude API)",
            "POST",
            "api/generate-code",
            200,
            data={
                "optimized_prompt": optimized_prompt,
                "session_id": self.session_id
            },
            timeout=120  # Longer timeout for code generation
        )
        
        if success and response:
            # Validate response structure
            if 'files' in response and isinstance(response['files'], list):
                self.generated_files = response['files']
                print(f"   Generated {len(self.generated_files)} files")
                
                for i, file in enumerate(self.generated_files):
                    if 'path' in file and 'content' in file:
                        print(f"   File {i+1}: {file['path']} ({len(file['content'])} chars)")
                    else:
                        print(f"   ❌ File {i+1} missing path or content")
                        return False, {}
                
                return True, response
            else:
                print("   ❌ Response missing 'files' array")
                return False, {}
        
        return success, response

    def test_download_zip(self):
        """Test zip file download"""
        if not self.session_id:
            print("❌ No session ID available for zip download")
            return False

        print(f"\n🔍 Testing Download ZIP...")
        url = f"{self.base_url}/api/download-zip/{self.session_id}"
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/zip':
                    print(f"✅ Passed - ZIP file downloaded ({len(response.content)} bytes)")
                    self.tests_passed += 1
                    return True
                else:
                    print(f"❌ Failed - Wrong content type: {response.headers.get('content-type')}")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
        
        self.tests_run += 1
        return False

    def test_download_individual_file(self, file_index=0):
        """Test individual file download"""
        if not self.session_id or not self.generated_files:
            print("❌ No session ID or files available for individual download")
            return False

        print(f"\n🔍 Testing Download Individual File (index {file_index})...")
        url = f"{self.base_url}/api/download-file/{self.session_id}/{file_index}"
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Passed - File downloaded ({len(response.content)} bytes)")
                self.tests_passed += 1
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
        
        self.tests_run += 1
        return False

    def test_invalid_session(self):
        """Test error handling with invalid session"""
        success, response = self.run_test(
            "Invalid Session Error Handling",
            "POST",
            "api/generate-code",
            404,
            data={
                "optimized_prompt": "test prompt",
                "session_id": "invalid-session-id"
            }
        )
        return success

def main():
    print("🚀 Starting Smart Code Generator API Tests")
    print("=" * 60)
    
    # Setup
    tester = SmartCodeGeneratorAPITester()
    test_prompt = "build a simple calculator app with React frontend"
    
    # Test 1: Health Check
    if not tester.test_health_check():
        print("❌ Health check failed, stopping tests")
        return 1

    # Test 2: Optimize Prompt (Gemini API)
    success, optimize_response = tester.test_optimize_prompt(test_prompt)
    if not success:
        print("❌ Prompt optimization failed, stopping tests")
        return 1

    optimized_prompt = optimize_response.get('optimized_prompt', '')
    if not optimized_prompt:
        print("❌ No optimized prompt received, stopping tests")
        return 1

    # Test 3: Generate Code (Claude API)
    success, generate_response = tester.test_generate_code(optimized_prompt)
    if not success:
        print("❌ Code generation failed, stopping tests")
        return 1

    # Test 4: Download ZIP
    if not tester.test_download_zip():
        print("⚠️  ZIP download failed")

    # Test 5: Download Individual File
    if tester.generated_files:
        if not tester.test_download_individual_file(0):
            print("⚠️  Individual file download failed")

    # Test 6: Error Handling
    if not tester.test_invalid_session():
        print("⚠️  Error handling test failed")

    # Print results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend APIs are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())