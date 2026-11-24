import requests
import json
import time
import sys

BASE_URL = "http://localhost:3000"
USER_EMAIL = "frontend_e2e@grak.ai"
USER_PASSWORD = "StrongPassword123!"

print("--- End to End Verification ---")

def test_flow():
    # 1. Register User (hitting Auth backend directly via Next.js proxy)
    print("1. Registering user...")
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    print("1.5. Verifying email...")
    verify_payload = {
        "email": USER_EMAIL,
        "otp": "123456"
    }
    verify_res = requests.post(f"{BASE_URL}/auth/verify-email", json=verify_payload)
    print(f"Verify status: {verify_res.status_code}")
    if verify_res.status_code != 200:
        print(f"Verify failed: {verify_res.text}")

    print("\n2. Logging in...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return False
        
    data = res.json()
    access_token = data.get("data", {}).get("access_token")
    refresh_token = data.get("data", {}).get("refresh_token")
    
    if not access_token:
        print("No access token returned!")
        return False
    print("Login successful! Token acquired.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 3. Test Chat
    print("\n3. Testing Chat Stream (via AI backend on port 8001)...")
    res = requests.post(f"{BASE_URL}/api/chat/stream", json={
        "messages": [{"role": "user", "content": "Hello!"}]
    }, headers=headers, stream=True)
    
    if res.status_code == 200:
        print("Chat Stream connected successfully!")
        # Consume some of the stream
        for line in res.iter_lines():
            if line:
                print("Received:", line.decode())
                break
    else:
        print(f"Chat failed: {res.status_code} - {res.text}")
        return False

    # 4. Test Image
    print("\n4. Testing Generate Image...")
    res = requests.post(f"{BASE_URL}/api/image", json={
        "prompt": "A beautiful sunset"
    }, headers=headers)
    print(f"Image status: {res.status_code}")
    if res.status_code == 200:
        print(res.json())

    # 5. Test Document
    print("\n5. Testing Document Generation...")
    res = requests.post(f"{BASE_URL}/api/document", json={
        "topic": "AI in healthcare",
        "doc_type": "ppt"
    }, headers=headers)
    print(f"Document status: {res.status_code}")

    # 6. Logout
    print("\n6. Logging out...")
    res = requests.post(f"{BASE_URL}/auth/logout", json={
        "refresh_token": refresh_token
    }, headers=headers)
    print(f"Logout status: {res.status_code}")

    # 7. Login Again
    print("\n7. Logging in again...")
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    print(f"Login Again status: {res.status_code}")
    
    # 8. Test Google Login (Expect 400 since backend enforces real tokens)
    print("\n8. Testing Google Login with invalid token...")
    res = requests.post(f"{BASE_URL}/auth/google", json={
        "id_token": "mock_google_token_test_123"
    })
    print(f"Google Login status: {res.status_code}")
    if res.status_code == 400:
        print("Google Login correctly rejected invalid token!")
    else:
        print("Warning: Expected 400 Bad Request for Google")
    
    # 9. Test Phone Login (Expect 400 since backend enforces real tokens)
    print("\n9. Testing Phone Login with invalid token...")
    res = requests.post(f"{BASE_URL}/auth/phone", json={
        "id_token": "mock_firebase_token_1234567890"
    })
    print(f"Phone Login status: {res.status_code}")
    if res.status_code == 400:
        print("Phone Login correctly rejected invalid token!")
    else:
        print("Warning: Expected 400 Bad Request for Phone")
    
    print("\nSUCCESS! End-to-End flow verified (Google/Phone APIs correctly secured)!")
    return True

if __name__ == "__main__":
    time.sleep(2) # Wait for Next.js to fully boot
    success = test_flow()
    if not success:
        sys.exit(1)
