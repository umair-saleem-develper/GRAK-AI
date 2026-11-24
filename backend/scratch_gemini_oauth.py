import os
from dotenv import load_dotenv

load_dotenv(override=True)
token = os.environ.get("GEMINI_API_KEY")

try:
    from google import genai
    from google.oauth2.credentials import Credentials

    # Create OAuth credentials object
    creds = Credentials(token=token)
    
    client = genai.Client(credentials=creds)
    response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
    print("SUCCESS: ", response.text)
except Exception as e:
    print(f"FAILED: {e}")
