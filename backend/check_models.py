
import asyncio
from dotenv import load_dotenv
import os
from groq import AsyncGroq

load_dotenv()

async def main():
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        models = await client.models.list()
        print("AVAILABLE GROQ MODELS:")
        for m in models.data:
            print("-", m.id)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())

