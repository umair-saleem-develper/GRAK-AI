import asyncio
import json
import time
import websockets

async def run_voice_e2e_test():
    url = "ws://127.0.0.1:8001/api/voice/grak-speak"
    print(f"Connecting to {url}...")

    results = []

    async with websockets.connect(url, open_timeout=15.0) as ws:
        print("[OK] Connected to voice WebSocket!")

        # 1. Wait for ready event
        ready_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        ready = json.loads(ready_raw)
        print(f"[OK] Ready event: {ready}")
        assert ready.get("type") == "ready", f"Unexpected ready: {ready}"

        test_turns = [
            "Hello Grak, what is your name?",
            "What is the highest mountain on Earth?",
            "Can you tell me a quick one-line joke?",
            "What color is the sky on a clear day?",
            "Thank you Grak, goodbye!"
        ]

        for i, user_utterance in enumerate(test_turns, 1):
            turn_label = f"Turn {i}"
            print(f"\n--------------------------------------------")
            print(f"> Starting {turn_label}: '{user_utterance}'")
            t_start = time.time()

            # Send final transcript as if user spoke it
            await ws.send(json.dumps({
                "type": "transcript",
                "text": user_utterance,
                "isFinal": True
            }))

            got_thinking = False
            got_response = False
            got_audio = False
            ai_text = ""
            audio_len = 0
            t_first_state = None
            t_response = None
            t_audio = None

            # Read messages until we get response + audio or timeout
            while not (got_response and got_audio):
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    msg = json.loads(raw)
                    mtype = msg.get("type")

                    if mtype == "state" and msg.get("voiceState") == "thinking":
                        got_thinking = True
                        if not t_first_state:
                            t_first_state = time.time()
                        print(f"  [{turn_label}] State -> thinking (+{t_first_state - t_start:.2f}s)")

                    elif mtype == "response":
                        got_response = True
                        t_response = time.time()
                        ai_text = msg.get("text", "")
                        print(f"  [{turn_label}] Response (+{t_response - t_start:.2f}s): {ai_text[:80]}")

                    elif mtype == "audio":
                        got_audio = True
                        t_audio = time.time()
                        b64 = msg.get("audio", "")
                        audio_len = len(b64)
                        print(f"  [{turn_label}] Audio received (+{t_audio - t_start:.2f}s): {audio_len} base64 chars")

                    elif mtype == "playback_done":
                        print(f"  [{turn_label}] playback_done received")
                        break

                    elif mtype == "error":
                        print(f"  [{turn_label}] ERROR: {msg.get('message')}")
                        break

                except asyncio.TimeoutError:
                    print(f"  [{turn_label}] TIMEOUT waiting for message!")
                    break

            t_turn_total = time.time() - t_start

            # Send playback finished to signal client is ready for next turn
            await ws.send(json.dumps({"type": "playback_finished"}))
            # Wait for state -> listening
            try:
                state_raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                state_msg = json.loads(state_raw)
                print(f"  [{turn_label}] Post-playback state: {state_msg.get('voiceState')}")
            except Exception as e:
                print(f"  [{turn_label}] Warning waiting for listening state: {e}")

            passed = got_response and got_audio and len(ai_text) > 0 and audio_len > 0
            results.append({
                "turn": turn_label,
                "input": user_utterance,
                "output": ai_text,
                "llm_time": round(t_response - t_start, 2) if t_response else None,
                "tts_time": round(t_audio - (t_response or t_start), 2) if t_audio else None,
                "total_time": round(t_turn_total, 2),
                "audio_bytes": audio_len,
                "status": "PASS" if passed else "FAIL"
            })

            # Small pause between turns
            await asyncio.sleep(0.5)

    print("\n" + "="*70)
    print("                  FINAL E2E MULTI-TURN RESULTS")
    print("="*70)
    print(f"{'Turn':<8} | {'Status':<6} | {'LLM (s)':<8} | {'TTS (s)':<8} | {'Total (s)':<9} | Response Preview")
    print("-" * 70)
    for r in results:
        preview = (r['output'][:35] + '...') if len(r['output']) > 35 else r['output']
        print(f"{r['turn']:<8} | {r['status']:<6} | {str(r['llm_time']):<8} | {str(r['tts_time']):<8} | {str(r['total_time']):<9} | {preview}")

    all_passed = all(r['status'] == 'PASS' for r in results)
    print("="*70)
    if all_passed:
        print(f"SUCCESS: All {len(results)} consecutive voice turns PASSED!")
    else:
        print("FAILURE: Some turns failed.")
    return all_passed

if __name__ == "__main__":
    asyncio.run(run_voice_e2e_test())
