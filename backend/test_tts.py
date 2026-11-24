import os
import requests, time
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DEEPGRAM_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

# Test TTS
print("=== Testing Deepgram TTS ===")
t0 = time.time()
try:
    r = requests.post(
        'https://api.deepgram.com/v1/speak?model=aura-asteria-en',
        headers={'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'},
        json={'text': 'Hello, I am Grak, your AI assistant.'},
        timeout=20.0
    )
    t1 = time.time()
    print(f'TTS status: {r.status_code}, bytes: {len(r.content)}, time: {t1-t0:.2f}s')
    if r.status_code != 200:
        print('Error:', r.text[:300])
except Exception as e:
    print(f'TTS Exception: {e}')

# Test Groq
print("\n=== Testing Groq ===")
t0 = time.time()
try:
    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'},
        json={
            'model': 'llama-3.1-8b-instant',
            'messages': [
                {'role': 'system', 'content': 'You are Grak. Reply in 1-2 short sentences, no markdown.'},
                {'role': 'user', 'content': 'Hello, what can you do?'}
            ],
            'max_tokens': 80
        },
        timeout=8.0
    )
    t1 = time.time()
    print(f'Groq status: {r.status_code}, time: {t1-t0:.2f}s')
    if r.status_code == 200:
        j = r.json()
        print('Reply:', j['choices'][0]['message']['content'])
    else:
        print('Error:', r.text[:300])
except Exception as e:
    print(f'Groq Exception: {e}')
