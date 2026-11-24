import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
token = os.environ.get("GEMINI_API_KEY")

url = "https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1/publishers/google/models/gemini-1.5-flash:generateContent"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "contents": [{"role": "user", "parts": [{"text": "Hi"}]}]
}
r = requests.post(url, headers=headers, json=payload)
print("Vertex:", r.status_code, r.text)
