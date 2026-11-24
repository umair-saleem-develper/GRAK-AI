import requests

BASE_URL = "http://localhost:3000"
USER_EMAIL = "test_frontend@grak.ai"
USER_PASSWORD = "StrongPassword123!"

print("Logging in to Next.js...")
res = requests.post(f"{BASE_URL}/auth/firebase", headers={"Authorization": "Bearer fake_token"})
# Wait, this won't work because it requires a valid firebase token.
# But wait, in the previous log, `test_frontend_proxy.py` got a 404 Not Found for /auth/register.
# Let's see if we can use the backend port 8001 directly to test streaming!
print(f"Got token: {token[:10]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "conversation_id": None,
    "content": "Hello",
    "uploaded_text": None
}

print("Hitting /api/chat/stream via Next.js...")
res = requests.post(f"{BASE_URL}/api/chat/stream", json=payload, headers=headers, stream=True)
print(f"Status: {res.status_code}")

if res.status_code == 200:
    for line in res.iter_lines():
        if line:
            print(f"Chunk: {line.decode()}")
else:
    print(f"Error: {res.text}")
