import asyncio
import httpx
import json
from database import SessionLocal
from models import User
from services.auth import create_access_token

async def test_followup():
    db = SessionLocal()
    user = db.query(User).first()
    token = create_access_token({"sub": user.id})
    db.close()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Send initial query
        conv_id = None
        print("Sending initial question: 'Tell me about plants'...")
        async with client.stream(
            "POST", 
            "http://localhost:8001/api/chat/stream", 
            headers=headers, 
            json={"content": "Tell me about plants"}
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "meta":
                            conv_id = data.get("conversation_id")
                    except:
                        pass

        print(f"Conversation ID: {conv_id}")

        # Step 2: Send follow-up: "give me its diagram"
        print("Sending follow-up: 'give me its diagram'...")
        diagram_found = False
        async with client.stream(
            "POST", 
            "http://localhost:8001/api/chat/stream", 
            headers=headers, 
            json={"content": "give me its diagram", "conversation_id": conv_id}
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "chunk":
                            content = data.get("content", "")
                            if ":::visual-hero" in content or ":::generated-image" in content:
                                diagram_found = True
                    except:
                        pass

        print(f"Follow-up Diagram Resolved Successfully: {diagram_found}")

if __name__ == "__main__":
    asyncio.run(test_followup())
