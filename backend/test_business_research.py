import os
import sys
sys.path.append('C:/Users/us761/.gemini/antigravity/scratch/OmniAI/backend')
from services.ai_engine import hybrid_web_research, optimize_search_query

query = 'in pakistan what number of business starting last week in online'
print('Optimizing query...')
opt = optimize_search_query(query)
print('Optimized:', opt)

print('Running research...')
res = hybrid_web_research(query)
print('Result:')
print(res)
