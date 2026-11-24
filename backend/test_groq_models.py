import os
import requests, time
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

# List available models
r = requests.get('https://api.groq.com/openai/v1/models', 
    headers={'Authorization': f'Bearer {groq_key}'}, timeout=10)
print('Models status:', r.status_code)
if r.status_code == 200:
    models = r.json()['data']
    # Filter for chat models only
    chat_models = [m['id'] for m in models if 'whisper' not in m['id'].lower()]
    print('Available models:')
    for m in sorted(chat_models):
        print(' ', m)
else:
    print(r.text[:300])
