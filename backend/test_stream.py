import requests
import json
import os
import sys

# Get token using Firebase fake login trick or just generating one!
# Actually, since I have access to backend code, I can just import `create_access_token`!
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.auth import create_access_token
from database import SessionLocal
import models

db = SessionLocal()
user = db.query(models.User).first()
if not user:
    print("No user found!")
    sys.exit(1)

token = create_access_token({"sub": user.id})
db.close()

url = "http://localhost:3000/api/chat/stream"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "content": "Hello, this is a test from python."
}

print(f"Testing stream endpoint: {url}")
try:
    with requests.post(url, headers=headers, json=payload, stream=True) as r:
        print(f"Status Code: {r.status_code}")
        for line in r.iter_lines():
            if line:
                print(line.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")

