import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv('C:/Users/us761/.gemini/antigravity/scratch/OmniAI/backend/.env')

query = 'academy teacher salary for freshers in Pakistan'
tavily_api_key = os.environ.get('TAVILY_API_KEY')
payload = {
    'api_key': tavily_api_key,
    'query': query,
    'search_depth': 'basic',
    'max_results': 3
}
response = requests.post('https://api.tavily.com/search', json=payload)
results = response.json().get('results', [])
with open('tavily_out_salary.txt', 'w', encoding='utf-8') as f:
    for i, res in enumerate(results):
        f.write(f"Result {i}: {res.get('url')}\n")
        f.write(res.get('content') + "\n")
        f.write("---\n")
