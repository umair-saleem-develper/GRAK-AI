import asyncio
import httpx
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from database import SessionLocal
from models import User
from services.auth import create_access_token

async def test_prompt(client, headers, prompt):
    print(f"\n{'='*70}")
    print(f"TESTING PROMPT: '{prompt}'")
    print(f"{'='*70}")
    
    full_text = ""
    provider = ""
    has_hero = False
    has_component = False
    has_gen = False
    
    async with client.stream(
        "POST", 
        "http://localhost:8001/api/chat/stream", 
        headers=headers, 
        json={"content": prompt}
    ) as resp:
        if resp.status_code != 200:
            print(f"HTTP Status: {resp.status_code}")
            return
            
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "provider":
                        provider = data.get("provider")
                    elif data.get("type") == "chunk":
                        content = data.get("content", "")
                        full_text += content
                        if ":::visual-hero" in content:
                            has_hero = True
                        if ":::visual-component" in content:
                            has_component = True
                        if ":::generated-image" in content:
                            has_gen = True
                except:
                    pass

    print(f"Provider: {provider}")
    print(f"Has :::visual-hero: {has_hero}")
    print(f"Has :::visual-component: {has_component}")
    print(f"Has :::generated-image: {has_gen}")
    print(f"Total Response Length: {len(full_text)} chars")
    
    # Extract images
    urls = []
    for line in full_text.splitlines():
        if line.strip().startswith("image:"):
            urls.append(line.replace("image:", "").strip())
    print(f"Found Image URLs ({len(urls)}):")
    for u in urls[:5]:
        print(f"  - {u}")
        
    print("\nResponse Preview (First 400 chars):")
    print(full_text[:400].replace("\n", " ") + "...")

async def main():
    db = SessionLocal()
    user = db.query(User).first()
    token = create_access_token({"sub": user.id})
    db.close()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        await test_prompt(client, headers, "explain plant with diagram")
        await test_prompt(client, headers, "give elon pic and explain all part of elon")

if __name__ == "__main__":
    asyncio.run(main())
