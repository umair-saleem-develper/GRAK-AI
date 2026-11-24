import os
import requests
from dotenv import load_dotenv

load_dotenv('C:/Users/us761/.gemini/antigravity/scratch/OmniAI/backend/.env')
query = 'Aaj Lahore mein sone (gold) ka kya rate hai aur pichle hafte se kitna farq aya hai?'

tavily_api_key = os.environ.get('TAVILY_API_KEY')
print(f'Tavily Key starts with: {tavily_api_key[:5] if tavily_api_key else None}')
try:
    if tavily_api_key:
        payload = {
            'api_key': tavily_api_key,
            'query': query,
            'search_depth': 'basic',
            'max_results': 3
        }
        response = requests.post('https://api.tavily.com/search', json=payload)
        response.raise_for_status()
        results = response.json().get('results', [])
        for res in results:
            print('Tavily Result:', res.get('content'))
    else:
        print('Tavily API key missing')
except Exception as e:
    print('Tavily Error:', repr(e))

print('\n--- DDGS TEST ---')
try:
    from duckduckgo_search import DDGS
    results = DDGS().text(query, max_results=3)
    if results:
        for r in results:
             print('DDGS Result:', r['body'])
except Exception as ddg_e:
    print('DDGS Error:', repr(ddg_e))
