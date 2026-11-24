import os
import sys
sys.path.append('C:/Users/us761/.gemini/antigravity/scratch/OmniAI/backend')
from services.ai_engine import hybrid_web_research

try:
    print(hybrid_web_research('What is the capital of Japan and what is its current population?'))
except Exception as e:
    print('Exception:', e)
