import os
import requests
from dotenv import load_dotenv

load_dotenv('C:/Users/us761/.gemini/antigravity/scratch/OmniAI/backend/.env')
query = 'top AI news'

print('--- TAVILY TEST ---')
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
        print('Tavily Success:', response.json().get('results', [])[0]['url'])
    else:
        print('Tavily API key missing')
except Exception as e:
    print('Tavily Error:', repr(e))

print('\n--- DDGS TEST ---')
try:
    from duckduckgo_search import DDGS
    results = DDGS().text(query, max_results=3)
    if results:
        print('DDGS Success:', list(results)[0]['href'])
except Exception as ddg_e:
    print('DDGS Error:', repr(ddg_e))
