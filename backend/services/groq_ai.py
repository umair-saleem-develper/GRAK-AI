import os
import requests
from dotenv import load_dotenv
from services.ai.identity import GRAK_IDENTITY_PROMPT

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_text(messages: list) -> str:
    """Generates text using Groq API (Llama 3.1) with conversation memory."""
    if not GROQ_API_KEY:
        return "Please provide a GROQ_API_KEY in the .env file."
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    api_messages = [
        {"role": "system", "content": f"{GRAK_IDENTITY_PROMPT}\n\nAlways provide highly detailed, step-by-step, and comprehensive answers. You must use Markdown formatting like headings (##), bullet points, code blocks, and bold text to make your answers professional and easy to read. You are a highly smart AI. Users will use Roman Urdu/Hindi and make typos or use broken language. Never say you do not understand. Always guess the intent from the context and reply intelligently."}
    ] + messages

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": api_messages,
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            return "Sorry, Grak AI encountered an API error. Please try again."
    except Exception as e:
        print(f"Groq Request Error: {e}")
        return "Sorry, I encountered a network error while connecting to the AI engine."
