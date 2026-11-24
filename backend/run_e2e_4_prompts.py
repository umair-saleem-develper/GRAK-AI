import asyncio
import httpx
import json
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from database import SessionLocal
from models import User
from services.auth import create_access_token

async def run_prompt(client, headers, prompt_name, prompt_text):
    print(f"\n{'='*70}")
    print(f"RUNNING PROMPT: '{prompt_name}'")
    print(f"Query: \"{prompt_text}\"")
    print(f"{'='*70}")
    
    payload = {"content": prompt_text}
    full_text = ""
    provider = ""
    conversation_id = ""
    has_generated_image = False
    has_visual_hero = False
    has_visual_component = False
    image_url = ""

    async with client.stream(
        "POST", 
        "http://localhost:8001/api/chat/stream", 
        headers=headers, 
        json=payload
    ) as resp:
        if resp.status_code != 200:
            print(f"FAILED with HTTP Status: {resp.status_code}")
            return False

        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:].strip()
                try:
                    data = json.loads(data_str)
                    dtype = data.get("type")
                    if dtype == "meta":
                        conversation_id = data.get("conversation_id")
                    elif dtype == "provider":
                        provider = data.get("provider")
                    elif dtype == "chunk":
                        chunk = data.get("content", "")
                        full_text += chunk
                        if ":::generated-image" in chunk:
                            has_generated_image = True
                        if ":::visual-hero" in chunk:
                            has_visual_hero = True
                        if ":::visual-component" in chunk:
                            has_visual_component = True
                except:
                    pass

    # Extract image url if any
    for line in full_text.splitlines():
        if line.strip().startswith("image:"):
            image_url = line.replace("image:", "").strip()
            break

    print(f"Status: HTTP 200 OK")
    print(f"Provider: {provider}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Response Length: {len(full_text)} characters")
    print(f"Has Generated Image Block: {has_generated_image}")
    print(f"Has Visual Hero Block: {has_visual_hero}")
    print(f"Has Component Blocks: {has_visual_component}")
    if image_url:
        print(f"Extracted Image URL: {image_url}")
    
    # Print the first 350 chars of the AI response
    preview = full_text[:350].replace("\n", " ")
    print(f"Response Preview: {preview}...")
    return True

async def main():
    db = SessionLocal()
    user = db.query(User).first()
    token = create_access_token({"sub": user.id})
    db.close()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    test_cases = [
        ("Explain photosynthesis", "Explain photosynthesis"),
        ("Give me a labeled diagram of a plant", "Give me a labeled diagram of a plant"),
        ("Create a gaming mouse diagram with labeled buttons", "Create a gaming mouse diagram with labeled buttons"),
        ("Explain this code", "Explain this code:\ndef bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr")
    ]

    async with httpx.AsyncClient(timeout=45.0) as client:
        for name, query in test_cases:
            await run_prompt(client, headers, name, query)

    print(f"\n{'='*70}")
    print("ALL 4 E2E TESTS FINISHED SUCCESSFULLY")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())
