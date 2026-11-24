import os
import json
import asyncio
import base64
import logging
import time
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("grak_voice")
logger.setLevel(logging.INFO)
router = APIRouter()

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

VOICE_SYSTEM = (
    "You are Grak, a friendly and concise AI voice assistant. "
    "Always respond in 1 to 2 short conversational sentences. "
    "No markdown, no bullet points, no asterisks, no code blocks. "
    "Speak naturally as if talking to a person."
)

# ──────────────────────────────────────────────
# FAST VOICE LLM — Groq primary, OpenRouter fallback
# ──────────────────────────────────────────────
async def generate_voice_response(messages: list, turn_id: str) -> tuple[str, str]:
    """
    Fast voice LLM path. Async HTTP, Groq primary (qwen/qwen3.8-27b ~1-2s),
    OpenRouter fallback. Returns (reply_text, provider_name).
    """
    payload = [{"role": "system", "content": VOICE_SYSTEM}] + messages[-6:]  # last 3 turns

    # ── 1. Groq (fastest) ──────────────────────────────────
    groq_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": "qwen/qwen3.8-27b",
                        "messages": payload,
                        "max_tokens": 120,
                        "temperature": 0.6,
                    },
                )
                t1 = time.time()
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"] or ""
                    text = text.replace("**", "").replace("*", "").replace("`", "").strip()
                    if text:
                        logger.info(f"[{turn_id}] LLM=Groq/qwen latency={t1-t0:.2f}s reply={text[:60]}")
                        return text, "Groq/qwen"
                else:
                    logger.warning(f"[{turn_id}] Groq error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.warning(f"[{turn_id}] Groq exception: {e}")

    # ── 2. OpenRouter fallback ─────────────────────────────
    or_key = OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {or_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://grak.ai",
                    },
                    json={
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
                        "messages": payload,
                        "max_tokens": 120,
                        "temperature": 0.6,
                    },
                )
                t1 = time.time()
                if res.status_code == 200:
                    msg = res.json()["choices"][0]["message"]
                    text = (msg.get("content") or msg.get("reasoning") or "").strip()
                    text = text.replace("**", "").replace("*", "").replace("`", "").strip()
                    if text:
                        logger.info(f"[{turn_id}] LLM=OR/llama latency={t1-t0:.2f}s reply={text[:60]}")
                        return text, "OpenRouter/llama"
                else:
                    logger.warning(f"[{turn_id}] OpenRouter error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.warning(f"[{turn_id}] OpenRouter exception: {e}")

    # ── 3. Hard fallback ──────────────────────────────────
    logger.error(f"[{turn_id}] All LLM providers failed — using fallback reply")
    return "I'm here to help! Could you please repeat that?", "fallback"


# ──────────────────────────────────────────────
# DEEPGRAM TTS (REST) — MP3 audio
# ──────────────────────────────────────────────
async def text_to_speech_deepgram(text: str, turn_id: str) -> bytes:
    """Converts text to MP3 audio using Deepgram TTS (Aura Asteria model)."""
    api_key = DEEPGRAM_API_KEY or os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        logger.error(f"[{turn_id}] [TTS] Missing DEEPGRAM_API_KEY")
        return b""
    clean_text = text.replace("**", "").replace("*", "").replace("`", "").strip()
    if not clean_text:
        return b""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(
                "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=mp3",
                headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
                json={"text": clean_text},
            )
            t1 = time.time()
            if res.status_code == 200:
                logger.info(f"[{turn_id}] [TTS] Generated {len(res.content)} bytes MP3 in {t1-t0:.2f}s")
                return res.content
            else:
                logger.error(f"[{turn_id}] [TTS] Error status={res.status_code} body={res.text[:100]}")
                return b""
    except Exception as e:
        logger.warning(f"[{turn_id}] [TTS] Exception/Timeout: {e}")
        return b""


# ──────────────────────────────────────────────
# VOICE WEBSOCKET ENDPOINT
# Architecture:
#   Browser (Web Speech API) → transcript text → WS → backend
#   backend → Groq LLM → Deepgram TTS → base64 audio → WS → browser
# ──────────────────────────────────────────────
@router.websocket("/api/voice/grak-speak")
async def voice_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    api_key = DEEPGRAM_API_KEY or os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Deepgram API key missing on server"
        }))
        await websocket.close()
        return

    is_active = True
    active_tts_task = None
    conversation_history = []
    turn_counter = [0]  # mutable for closure

    session_start = time.time()
    logger.info("[Voice Session] New session started.")

    # ── Send ready signal ──────────────────────────────────
    await websocket.send_text(json.dumps({
        "type": "ready",
        "voiceState": "listening"
    }))

    # ── Cancel any ongoing AI+TTS task (barge-in) ─────────
    async def cancel_active_response():
        nonlocal active_tts_task
        if active_tts_task and not active_tts_task.done():
            logger.info("[Voice Session] Barge-in: cancelling active response.")
            active_tts_task.cancel()
            try:
                await active_tts_task
            except asyncio.CancelledError:
                pass
            active_tts_task = None
        try:
            await websocket.send_text(json.dumps({
                "type": "interrupted",
                "voiceState": "listening"
            }))
        except Exception:
            pass

    # ── Handle one AI turn: LLM + TTS ─────────────────────
    async def handle_ai_turn(user_utterance: str):
        turn_counter[0] += 1
        turn_id = f"T{turn_counter[0]}"
        t_transcript = time.time()
        logger.info(f"[{turn_id}] ── START TURN ─────────────────────────")
        logger.info(f"[{turn_id}] t_transcript={t_transcript - session_start:.2f}s  utterance={user_utterance!r}")

        try:
            if not user_utterance.strip():
                return

            # Notify browser: thinking state
            await websocket.send_text(json.dumps({
                "type": "state",
                "voiceState": "thinking"
            }))

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_utterance})

            # ── LLM ─────────────────────────────────────────
            t_llm_start = time.time()
            logger.info(f"[{turn_id}] t_llm_start={t_llm_start - session_start:.2f}s")

            try:
                ai_reply, provider = await asyncio.wait_for(
                    generate_voice_response(conversation_history, turn_id),
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.error(f"[{turn_id}] LLM timed out after 8s")
                ai_reply = "I'm thinking, give me just a moment."
                provider = "timeout"

            t_llm_done = time.time()
            logger.info(f"[{turn_id}] t_llm_done={t_llm_done - session_start:.2f}s  LLM_latency={t_llm_done - t_llm_start:.2f}s  provider={provider}")

            if not ai_reply:
                ai_reply = "I'm here — please go ahead."

            conversation_history.append({"role": "assistant", "content": ai_reply})

            # Send text to frontend (shows in chat area)
            await websocket.send_text(json.dumps({
                "type": "response",
                "text": ai_reply,
                "userText": user_utterance,
                "voiceState": "speaking"
            }))

            # ── TTS ─────────────────────────────────────────
            t_tts_start = time.time()
            logger.info(f"[{turn_id}] t_tts_start={t_tts_start - session_start:.2f}s")

            try:
                audio_bytes = await asyncio.wait_for(
                    text_to_speech_deepgram(ai_reply, turn_id),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                logger.error(f"[{turn_id}] TTS timed out after 15s")
                audio_bytes = b""

            t_tts_done = time.time()
            logger.info(f"[{turn_id}] t_tts_done={t_tts_done - session_start:.2f}s  TTS_latency={t_tts_done - t_tts_start:.2f}s  audio_bytes={len(audio_bytes)}")

            if audio_bytes:
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                await websocket.send_text(json.dumps({
                    "type": "audio",
                    "audio": b64_audio,
                    "format": "mp3",
                    "turnId": turn_id
                }))
                t_audio_sent = time.time()
                logger.info(f"[{turn_id}] t_audio_sent={t_audio_sent - session_start:.2f}s")
            else:
                # No audio — still need to return to listening
                await websocket.send_text(json.dumps({
                    "type": "playback_done",
                    "voiceState": "listening"
                }))

            total = time.time() - t_transcript
            logger.info(f"[{turn_id}] ── TURN COMPLETE  total={total:.2f}s ─────────────────")

        except asyncio.CancelledError:
            logger.info(f"[{turn_id}] Turn cancelled (barge-in).")
            raise
        except Exception as e:
            logger.error(f"[{turn_id}] Error in handle_ai_turn: {e}", exc_info=True)
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"AI error: {str(e)}",
                    "voiceState": "listening"
                }))
            except Exception:
                pass

    # ── Idle keepalive ping to browser ────────────────────
    async def ping_browser():
        nonlocal is_active
        try:
            while is_active:
                await asyncio.sleep(20)
                if is_active:
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                    except Exception:
                        is_active = False
                        break
        except asyncio.CancelledError:
            pass

    # ── Main receive loop ─────────────────────────────────
    async def receive_loop():
        nonlocal is_active, active_tts_task
        try:
            while is_active:
                message = await websocket.receive()
                if "text" in message and message["text"]:
                    try:
                        data = json.loads(message["text"])
                        msg_type = data.get("type")

                        if msg_type == "transcript":
                            # Browser Web Speech API sent us a final transcript
                            transcript = data.get("text", "").strip()
                            is_final = data.get("isFinal", False)
                            logger.info(f"[Voice Session] Transcript received: isFinal={is_final} text={transcript!r}")

                            if transcript:
                                # Barge-in check: if AI is active, cancel it
                                if active_tts_task and not active_tts_task.done():
                                    await cancel_active_response()

                                # Forward interim transcript for UI display
                                await websocket.send_text(json.dumps({
                                    "type": "transcript",
                                    "text": transcript,
                                    "isFinal": is_final
                                }))

                                # Only trigger AI on final transcript
                                if is_final:
                                    if active_tts_task and not active_tts_task.done():
                                        active_tts_task.cancel()
                                    active_tts_task = asyncio.create_task(
                                        handle_ai_turn(transcript)
                                    )

                        elif msg_type == "barge_in":
                            await cancel_active_response()

                        elif msg_type == "playback_finished":
                            # Browser finished playing audio — go back to listening
                            logger.info("[Voice Session] Browser: playback finished → listening")
                            await websocket.send_text(json.dumps({
                                "type": "state",
                                "voiceState": "listening"
                            }))

                        elif msg_type == "pong":
                            pass  # keepalive response

                        elif msg_type == "close":
                            logger.info("[Voice Session] Client requested close.")
                            is_active = False
                            break

                    except json.JSONDecodeError:
                        pass

                elif "bytes" in message and message["bytes"]:
                    # Binary audio (old PCM path) — ignore, we use text transcripts now
                    pass

        except WebSocketDisconnect:
            logger.info("[Voice Session] WebSocket disconnected by client.")
            is_active = False
        except Exception as e:
            logger.debug(f"[Voice Session] receive_loop ended: {e}")
            is_active = False

    # ── Run both coroutines ───────────────────────────────
    try:
        await asyncio.gather(
            receive_loop(),
            ping_browser(),
            return_exceptions=True
        )
    finally:
        is_active = False
        if active_tts_task and not active_tts_task.done():
            active_tts_task.cancel()
        elapsed = time.time() - session_start
        logger.info(f"[Voice Session] Session ended after {elapsed:.1f}s.")
