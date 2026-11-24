import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("Warning: GEMINI_API_KEY not found.")

def generate_text(prompt: str) -> str:
    """Generates text using Google Gemini API."""
    if not model:
        return f"[Mock Gemini Response] I would have responded to: '{prompt}', but the API key is missing."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Sorry, I encountered an error while generating a response."
