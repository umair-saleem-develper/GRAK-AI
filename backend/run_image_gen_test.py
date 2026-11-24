import asyncio
import httpx
from services.image_generation import generate_ai_image

async def main():
    print("==================================================")
    print("TEST 1: LIVE IMAGE GENERATION CALL (FLUX.1 ENGINE)")
    print("==================================================")
    prompt = "gaming mouse diagram with labeled buttons"
    res = await generate_ai_image(prompt, is_diagram=True)
    
    print(f"Success: {res.get('success')}")
    print(f"Original Prompt: {res.get('prompt')}")
    print(f"Enhanced Prompt: {res.get('enhanced_prompt')}")
    print(f"Model: {res.get('model')}")
    print(f"Dimensions: {res.get('width')}x{res.get('height')}")
    print(f"Size Bytes: {res.get('size_bytes')}")
    print(f"Returned URL: {res.get('url')}")
    print(f"Error (if any): {res.get('error')}")

    if res.get("url"):
        # Explicitly verify HTTP status of the returned URL
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(res["url"])
            print(f"HTTP GET Status of Returned URL: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type')}")
            print(f"Verified Payload Length: {len(resp.content)} bytes")

    print("\n==================================================")
    print("TEST 2: ERROR HANDLING / INVALID INPUT TEST")
    print("==================================================")
    err_res = await generate_ai_image("")
    print(f"Empty prompt success: {err_res.get('success')}")
    print(f"Reported error detail: {err_res.get('error')}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
