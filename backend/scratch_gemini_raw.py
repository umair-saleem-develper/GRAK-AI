import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
token = os.environ.get("GEMINI_API_KEY")

print("Testing as x-goog-api-key...")
headers_api = {
    "x-goog-api-key": token,
    "Content-Type": "application/json"
}
url_api = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
payload = {
    "contents": [{"parts":[{"text": "Hi"}]}]
}
r_api = requests.post(url_api, headers=headers_api, json=payload)
print(r_api.status_code, r_api.text)

print("\nTesting Vertex as query param...")
url_query = f"https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1/publishers/google/models/gemini-1.5-flash:generateContent?key={token}"
headers_query = {"Content-Type": "application/json"}
r_query = requests.post(url_query, headers=headers_query, json=payload)
print(r_query.status_code, r_query.text)
