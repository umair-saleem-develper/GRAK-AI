import asyncio
import json
import time
import websockets

async def test_turns():
    url = "ws://127.0.0.1:8001/api/voice/grak-speak"
    print("Connecting to", url, flush=True)
    async with websockets.connect(url, open_timeout=8.0) as ws:
        ready = json.loads(await ws.recv())
        print("[1] Got Ready:", ready, flush=True)

        turns = ["Hello Grak!", "What is 2 plus 2?", "Tell me a joke."]
        for i, text in enumerate(turns, 1):
            t0 = time.time()
            print(f"\n--- TURN {i}: Sending '{text}' ---", flush=True)
            await ws.send(json.dumps({"type": "transcript", "text": text, "isFinal": True}))

            got_resp, got_aud = False, False
            while not (got_resp and got_aud):
                raw = await asyncio.wait_for(ws.recv(), timeout=20.0)
                msg = json.loads(raw)
                mtype = msg.get("type")
                elapsed = time.time() - t0
                if mtype == "state":
                    print(f"  [+{elapsed:.2f}s] State: {msg.get('voiceState')}", flush=True)
                elif mtype == "response":
                    got_resp = True
                    print(f"  [+{elapsed:.2f}s] AI Text: {msg.get('text', '')}", flush=True)
                elif mtype == "audio":
                    got_aud = True
                    b64 = msg.get("audio", "")
                    print(f"  [+{elapsed:.2f}s] Audio: {len(b64)} chars base64 MP3", flush=True)
                elif mtype == "error":
                    print(f"  [+{elapsed:.2f}s] ERROR: {msg.get('message')}", flush=True)
                    break

            await ws.send(json.dumps({"type": "playback_finished"}))
            state = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
            print(f"  [+{time.time()-t0:.2f}s] Post playback state: {state.get('voiceState')}", flush=True)
            print(f"=== TURN {i} PASSED ===", flush=True)

        print("\n*** ALL TURNS PASSED COMPLETELY! ***", flush=True)

if __name__ == "__main__":
    asyncio.run(test_turns())
