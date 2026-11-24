
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

async def test_gemini():
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = await client.aio.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents="Hello"
        )
        print("SUCCESS:", response.text.strip())
    except Exception as e:
        print("ERROR:", str(e))

asyncio.run(test_gemini())

