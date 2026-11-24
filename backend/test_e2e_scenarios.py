import asyncio
import httpx
import json
from database import SessionLocal
from models import User
from services.auth import create_access_token

async def run_tests():
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        # Create a test user if none exists
        import uuid
        user = User(id=str(uuid.uuid4()), email="test@grak.ai", password_hash="dummy")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = create_access_token({"sub": user.id})
    db.close()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    test_queries = [
        {
            "name": "Scenario 1: Normal Text (Explain Photosynthesis)",
            "query": "Explain photosynthesis",
            "expected_intent": "text_answer",
            "should_contain": ["photosynthesis"],
            "should_not_contain": [":::visual-hero", ":::generated-image"]
        },
        {
            "name": "Scenario 2: Code Request (Explain this code)",
            "query": "Explain this code:\ndef add(a, b):\n    return a + b",
            "expected_intent": "code",
            "should_contain": ["add"],
            "should_not_contain": [":::visual-hero", ":::generated-image"]
        },
        {
            "name": "Scenario 3: Visual Explanation (Plant Diagram)",
            "query": "Give me a labeled diagram of a plant",
            "expected_intent": "visual_explanation",
            "should_contain": [":::visual-hero"],
            "should_not_contain": []
        },
        {
            "name": "Scenario 4: Real AI Image Generation (Gaming Mouse)",
            "query": "Create a gaming mouse diagram with labeled buttons",
            "expected_intent": "image_generation",
            "should_contain": [":::generated-image", "pollinations.ai"],
            "should_not_contain": []
        },
        {
            "name": "Scenario 5: Language Support (Roman Urdu)",
            "query": "Plant kya hota hai aasan urdu me samjhao",
            "expected_intent": "text_answer",
            "should_contain": [],
            "should_not_contain": [":::visual-hero", ":::generated-image"]
        }
    ]

    print("==========================================")
    print("STARTING E2E VERIFICATION TEST SUITE")
    print("==========================================\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for t in test_queries:
            print(f"--- Running {t['name']} ---")
            payload = {"content": t["query"]}
            
            full_content = ""
            try:
                async with client.stream(
                    "POST", 
                    "http://localhost:8001/api/chat/stream", 
                    headers=headers, 
                    json=payload
                ) as resp:
                    if resp.status_code != 200:
                        print(f"FAILED: Status {resp.status_code}")
                        continue
                        
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "chunk":
                                    full_content += data.get("content", "")
                            except:
                                pass

                # Verification
                passed = True
                for sc in t["should_contain"]:
                    if sc.lower() not in full_content.lower():
                        print(f"  [!] Missing expected snippet: '{sc}'")
                        passed = False

                for snc in t["should_not_contain"]:
                    if snc.lower() in full_content.lower():
                        print(f"  [!] Unexpected snippet found: '{snc}'")
                        passed = False

                if passed:
                    print(f"  [PASS] Output length: {len(full_content)} chars")
                    preview = full_content.split("\n")[0][:120]
                    print(f"  Preview: {preview}...")
                else:
                    print(f"  [FAIL] Did not meet criteria")
            except Exception as e:
                print(f"  [ERROR] {e}")

            print()

    print("==========================================")
    print("ALL TESTS COMPLETE")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
