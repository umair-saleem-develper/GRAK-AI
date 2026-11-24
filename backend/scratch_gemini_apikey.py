import os
from dotenv import load_dotenv

load_dotenv(override=True)
token = os.environ.get("GEMINI_API_KEY")

try:
    from google import genai
    client = genai.Client(api_key=token)
    response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
    print("SUCCESS: ", response.text)
except Exception as e:
    print(f"FAILED: {e}")
