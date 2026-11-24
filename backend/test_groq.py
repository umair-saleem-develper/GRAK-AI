import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.ai.gateway import AIGateway
import logging
import os

logging.basicConfig(level=logging.DEBUG)

async def test():
    print(f"GROQ API KEY LOADED: {'yes' if os.getenv('GROQ_API_KEY') else 'no'}")
    
    from services.ai.providers.groq import GroqProvider
    try:
        provider = GroqProvider()
        print("GroqProvider initialized successfully.")
    except Exception as e:
        print(f"GroqProvider init failed: {e}")
        return
        
    gw = AIGateway()
    print(f"Providers loaded in gateway: {[p.provider_name for p in gw.providers]}")
    try:
        stream = gw.stream([{'role': 'user', 'content': 'Hello'}])
        async for chunk in stream:
            print(f'Chunk: {chunk.content}')
    except Exception as e:
        print(f'Error: {e}')
    
    print('Done.')

asyncio.run(test())
