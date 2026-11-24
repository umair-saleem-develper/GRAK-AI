
import asyncio
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

from services.ai.gateway import AIGateway

async def test_fallback():
    gateway = AIGateway()
    messages = [{"role": "user", "content": "Hello, this is a test."}]
    
    print("Starting stream test...")
    stream = gateway.stream(messages)
    
    full_response = ""
    final_provider = None
    
    try:
        async for chunk in stream:
            if chunk.content:
                full_response += chunk.content
            if chunk.is_done:
                final_provider = chunk.provider
    except Exception as e:
        print("ERROR:", e)
        return
        
    print("\n====================")
    print("FINAL PROVIDER:", final_provider)
    print("FINAL RESPONSE:", full_response.strip())
    print("====================")

if __name__ == "__main__":
    asyncio.run(test_fallback())

