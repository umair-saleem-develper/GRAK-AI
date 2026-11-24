import os
import requests, time
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

for model in ['qwen/qwen3.8-27b', 'openai/gpt-oss-20b']:
    t0 = time.time()
    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You are Grak. Reply in 1-2 short sentences, no markdown.'},
                    {'role': 'user', 'content': 'Hello, what can you do?'}
                ],
                'max_tokens': 80
            },
            timeout=10.0
        )
        t1 = time.time()
        print(f'{model}: {r.status_code} in {t1-t0:.2f}s')
        if r.status_code == 200:
            j = r.json()
            print('  Reply:', j['choices'][0]['message']['content'])
        else:
            print('  Error:', r.text[:200])
    except Exception as e:
        print(f'{model}: Exception {e}')
