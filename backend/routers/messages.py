import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
from models import User, Conversation, Message, AIUsage
from services.auth import get_current_user
from services.ai.gateway import AIGateway
from services.ai.identity import GRAK_IDENTITY_PROMPT
from services.visual_enrichment import get_visual_enrichment, build_visual_system_prompt
from services.intent_router import (
    detect_intent, 
    INTENT_IMAGE_GENERATION, 
    INTENT_VISUAL_EXPLANATION, 
    INTENT_CODE, 
    INTENT_TEXT
)
from services.image_generation import generate_ai_image
from services.image_studio import (
    generate_or_edit_image,
    is_followup_edit_request,
    is_long_detailed_prompt,
    sanitize_block_prompt,
    extract_latest_generated_image,
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])
gateway = AIGateway()

class MessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    content: str
    uploaded_text: Optional[str] = None # Text extracted from uploaded files to prepend
    image_base64: Optional[str] = None # Inline image data for Gemini multimodal vision
    edit_image_url: Optional[str] = None # Target generated image URL for iterative editing
    mode: Optional[str] = None # "create_image" or None

def generate_title_task(conversation_id: str, first_message: str):
    """Background task to generate a title for a new conversation."""
    # We must create a new DB session for the background task
    from database import SessionLocal
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return
            
        prompt = f"Generate a short (max 5 words) title for a conversation that starts with this message:\n\n{first_message}"
        messages = [{"role": "user", "content": prompt}]
        
        # Use gateway directly, blocking event loop slightly is OK for background task 
        # or use asyncio.run if this was a sync function, but fastapi background tasks can be async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(gateway.chat(messages, apply_identity=False))
            conv.title = response.content.strip().strip('"').strip("'")
            db.commit()
        except Exception as e:
            pass # Ignore failure in title generation
        finally:
            loop.close()
    finally:
        db.close()

async def async_generate_title_task(conversation_id: str, first_message: str):
    from database import SessionLocal
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return
            
        prompt = f"Generate a very short, plain text title (max 5 words) for a chat starting with: {first_message[:200]}"
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await gateway.chat(messages, apply_identity=False)
            # Cleanup common quotes or markdown
            title = response.content.strip().replace('"', '').replace('`', '').replace('*', '')
            if len(title) > 50:
                title = title[:47] + "..."
            conv.title = title
            db.commit()
        except Exception as e:
            pass 
    finally:
        db.close()

@router.post("/stream")
async def send_message(
    request: Request,
    msg_req: MessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handles streaming AI response.
    Lazy initializes conversation if not provided.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("[DEBUG] Chat: sending message")
    
    # 1. Lazy Initialization of Conversation
    conversation_id = msg_req.conversation_id
    is_new_conversation = False
    
    if not conversation_id:
        conv = Conversation(user_id=current_user.id, title="New Chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
        is_new_conversation = True
    else:
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
            Conversation.deleted_at == None
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Save User Message
    full_content = msg_req.content
    if msg_req.uploaded_text:
        user_query = msg_req.content.strip() if msg_req.content and msg_req.content.strip() else "Please review, analyze, and explain this attached image/file."
        full_content = f"Attached Document Context:\n{msg_req.uploaded_text}\n\nUser Message: {user_query}"
        
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=full_content,
        image_base64=msg_req.image_base64
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    # Trigger async title generation for new chats
    if is_new_conversation:
        background_tasks.add_task(async_generate_title_task, conversation_id, msg_req.content)

    # 3. Retrieve Conversation History (Last 10 messages for context window)
    history_msgs = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(10).all()
    history_msgs.reverse()

    # Format recent history for context (exclude current user message when inspecting prior turns)
    prior_history = [m for m in history_msgs if m.id != user_msg.id]
    recent_history_context = [{"role": m.role, "content": m.content} for m in history_msgs]

    # Mode: Direct Image Creation OR Explicit "Edit" Button Target
    if msg_req.mode == "create_image" or msg_req.edit_image_url:
        source_image_ref = msg_req.edit_image_url.strip() if msg_req.edit_image_url else None
        source_image_b64 = msg_req.image_base64
        prior_prompt = None

        if not source_image_ref and not source_image_b64:
            followup = is_followup_edit_request(msg_req.content, prior_history, mode="create_image")
            if followup:
                source_image_ref, prior_prompt = followup
        elif source_image_ref:
            latest = extract_latest_generated_image(prior_history)
            if latest:
                prior_prompt = latest[1]

        logger.info(
            f"[CreateImageMode] mode={msg_req.mode} edit_target={bool(source_image_ref or source_image_b64)} "
            f"lines={len(msg_req.content.splitlines())} raw_prompt='{msg_req.content[:80]}'"
        )

        async def direct_image_generator():
            # 1. Send meta event immediately so client knows conversation is registered
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"

            # 2. Run image generation/editing as a background task, sending SSE keep-alives every 1s
            # This ensures Next.js proxy rewrite and browser fetch NEVER hit an idle timeout or drop!
            gen_task = asyncio.create_task(
                generate_or_edit_image(
                    prompt=msg_req.content,
                    source_image_ref=source_image_ref,
                    source_image_b64=source_image_b64,
                    prior_prompt=prior_prompt,
                )
            )
            while not gen_task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(gen_task), timeout=1.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"

            nv_result = await gen_task

            # Log provider decision (never logs any API key)
            provider = nv_result.get("provider", "none")
            model_used = nv_result.get("model", "unknown")
            fallback = nv_result.get("fallback", False)
            edited = nv_result.get("edited", False)
            enhanced = nv_result.get("enhanced_prompt", msg_req.content)
            logger.info(
                f"[CreateImageMode] RESULT provider={provider} model={model_used} "
                f"edited={edited} fallback={fallback} success={nv_result.get('success')} "
                f"enhanced_prompt='{enhanced[:80]}'"
            )

            # Provider event — frontend logs this via console.debug, never shown in UI
            yield f"data: {json.dumps({'type': 'provider', 'provider': provider, 'model': model_used, 'fallback': fallback, 'edited': edited})}\n\n"

            if nv_result.get("success") and nv_result.get("url"):
                safe_card_prompt = sanitize_block_prompt(nv_result.get("prompt", msg_req.content))
                img_block = (
                    f":::generated-image\n"
                    f"image: {nv_result['url']}\n"
                    f"prompt: {safe_card_prompt}\n"
                    f":::\n"
                )
                yield f"data: {json.dumps({'type': 'chunk', 'content': img_block})}\n\n"
                ai_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=img_block,
                    provider=provider,
                    model=model_used,
                )
                db.add(ai_msg)
                db.commit()
            else:
                err_text = nv_result.get("error") or "Image generation could not be completed right now. Please try again."
                yield f"data: {json.dumps({'type': 'chunk', 'content': err_text})}\n\n"
                ai_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=err_text,
                    provider=provider,
                    model=model_used,
                )
                db.add(ai_msg)
                db.commit()

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            direct_image_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # 3.5 Intent Detection & Context Resolution
    classification = detect_intent(msg_req.content, recent_history_context)
    intent_type = classification.get("intent", INTENT_TEXT)
    logger.info(f"[ChatIntent] Query: '{msg_req.content[:60]}' => Intent: {intent_type}")

    deterministic_hero_block = ""
    visual_enrichment = None

    # Conversational follow-up image edit detection in regular chat right after a generated image
    chat_edit_target = None
    if intent_type != INTENT_CODE and prior_history:
        last_msg = prior_history[-1]
        if getattr(last_msg, "role", None) == "assistant" and ":::generated-image" in (getattr(last_msg, "content", "") or ""):
            chat_edit_target = is_followup_edit_request(msg_req.content, prior_history, mode=None)
            if chat_edit_target:
                intent_type = INTENT_IMAGE_GENERATION

    if intent_type == INTENT_IMAGE_GENERATION:
        # Preserve full untruncated prompt for long descriptions or iterative edits
        is_long = is_long_detailed_prompt(msg_req.content)
        target_prompt = msg_req.content if (is_long or chat_edit_target) else classification.get("prompt", msg_req.content)
        is_diag = classification.get("is_diagram", False) and not chat_edit_target
        source_ref = chat_edit_target[0] if chat_edit_target else None
        prior_p = chat_edit_target[1] if chat_edit_target else None

        ai_img_result = await generate_or_edit_image(
            prompt=target_prompt,
            source_image_ref=source_ref,
            source_image_b64=msg_req.image_base64,
            prior_prompt=prior_p,
            is_diagram=is_diag,
        )
        if ai_img_result.get("success"):
            safe_card_prompt = sanitize_block_prompt(ai_img_result.get("prompt", target_prompt))
            deterministic_hero_block = f""":::generated-image
image: {ai_img_result['url']}
prompt: {safe_card_prompt}
:::

"""
        else:
            logger.warning(f"[ImageGeneration] Generation failed: {ai_img_result.get('error')}")

    elif intent_type == INTENT_VISUAL_EXPLANATION:
        # User asked for educational explanation accompanied by diagrams/photos
        try:
            visual_enrichment = await get_visual_enrichment(msg_req.content, gateway, recent_history_context)
            # We do NOT set deterministic_hero_block at the very top, so the Title + 2-sentence intro render first as required by ChatGPT layout
        except Exception as e:
            logger.warning(f"Visual enrichment lookup error: {e}")

    # Build system instructions combining central Grak AI identity with A-to-Z response formatting
    system_instruction = f"""{GRAK_IDENTITY_PROMPT}

You are a smart, warm, and capable AI collaborator. Follow these formatting and communication rules on every response:

1. LANGUAGE & TONE ADAPTATION:
   - Automatically match the user's language and style.
   - If the user writes in Roman Urdu (e.g., "muja samjhao", "ye kasa kaam karta ha"), respond in clear, natural, easy-to-understand Roman Urdu mixed with standard English technical terms.
   - If the user writes in English, respond in clear, natural, everyday English.
   - Never use stiff, robotic, or overly academic jargon (avoid phrases like "Scientific Note on Evaluation" or "corporate architectures"). Talk like a helpful, knowledgeable friend and senior engineer.

2. CONVERSATION MEMORY & CONTEXT:
   - Always read the previous messages in the conversation before answering.
   - When the user asks a short follow-up (e.g., "iska code do", "aur detail batao", "give example", "muja tasver du"), connect it directly to the topic from the previous turn.
   - If the user's request is ambiguous or missing a topic, ask 1–2 short, polite clarifying questions with concrete options instead of guessing a random topic.

3. A-TO-Z RESPONSE STRUCTURE (STRUCTURED MARKDOWN):
   - Direct Opening (1–2 Sentences): Start directly with the clear answer or outcome. Skip filler openings like "Sure, I can help with that!" or "As an AI language model...".
   - Section Headings (`###`): For any explanation with multiple parts or steps, organize sections using `###` headings (with a relevant emoji when helpful, e.g., `### 🌱 1. What is Photosynthesis?`). For short 2–3 line answers, use natural prose without headings.
   - Parallel Bullet Points with Bold Lead-Ins: Keep bullet points scannable. Start every bullet with a **Bold Key Term** followed by a colon and a concise 1–2 line explanation:
     * **Key Concept:** Clear, simple explanation in 1–2 lines.
   - Numbered Step-by-Step Guides: When explaining a workflow, tutorial, or process, use numbered steps (`1.`, `2.`, `3.`) where each step explains what to do and why.
   - Markdown Comparison Tables: Whenever comparing 2 or more options, tools, concepts, or pros/cons across shared attributes, use a clean Markdown pipe table (`| Feature | Option A | Option B |`) instead of long repetitive paragraphs.
   - Blockquotes & Callouts (`>`): Use `>` blockquotes for key formulas, important tips, or exact quotes/prompts.
   - Clean Code Blocks: Always wrap code or terminal commands in fenced code blocks with the language tag (e.g., ```python, ```javascript, ```bash).
   - Actionable Next Step (1 Sentence): End complex explanations with a brief, natural 1-sentence next step or question to help the user move forward."""

    if intent_type == INTENT_IMAGE_GENERATION:
        if deterministic_hero_block:
            system_instruction += f"""\n\nAI IMAGE GENERATION MODE:
You have just generated and displayed an AI visual of '{classification.get('prompt', msg_req.content)}'.
The generated visual card is ALREADY rendered at the top of the chat.
Now provide a helpful, warm breakdown explaining the key elements, visual design, and details shown in this image.
NEVER say 'I cannot provide images' or 'I am a text-based AI'. The image is already generated and displayed."""
        else:
            system_instruction += f"""\n\nAI IMAGE GENERATION NOTICE:
The AI image generation engine encountered a temporary timeout or connection issue.
Explain the topic '{classification.get('prompt', msg_req.content)}' clearly and politely mention that image generation had a temporary delay and the user can click retry to regenerate."""

    elif intent_type == INTENT_VISUAL_EXPLANATION and visual_enrichment:
        system_instruction += "\n\n" + build_visual_system_prompt(visual_enrichment)

    elif intent_type == INTENT_CODE:
        system_instruction += "\n\nCODING ASSISTANT MODE: Provide clean, idiomatic, well-commented code blocks. Keep introductory/closing remarks concise. Do NOT generate or look for images."

    elif intent_type == INTENT_TEXT:
        system_instruction += "\n\nTEXT EXPLANATION MODE: Answer directly, clearly, and concisely. Do NOT invoke image search, diagrams, or placeholder visual blocks."

    # Format for AI Provider and inject System Persona
    formatted_history = [
        {
            "role": "system",
            "content": system_instruction
        }
    ]
    for m in history_msgs:
        formatted_history.append({
            "role": m.role,
            "content": m.content,
            "image_base64": getattr(m, "image_base64", None)
        })
        
    # SSE Stream Generator
    async def sse_generator():
        import logging
        import re
        logger = logging.getLogger(__name__)
        logger.debug("[DEBUG] Chat: connecting to stream endpoint")
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"
        
        full_assistant_response = ""
        final_model = ""
        final_provider = ""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        
        # Deterministically yield Hero Visual Card at start if present
        hero_yielded = False
        if deterministic_hero_block:
            full_assistant_response += deterministic_hero_block
            yield f"data: {json.dumps({'type': 'chunk', 'content': deterministic_hero_block})}\n\n"
            hero_yielded = True

        buffering_prefix = hero_yielded
        prefix_buffer = ""
        
        import time
        start_time = time.time()
        
        try:
            # We catch disconnects inside the stream
            stream = gateway.stream(formatted_history)
            sent_provider_event = False
            async for chunk in stream:
                if await request.is_disconnected():
                    break # Client disconnected, stop generating
                
                # Emit provider event once before the first content chunk
                if not sent_provider_event and chunk.provider and chunk.provider != "none":
                    provider_payload = {
                        "type": "provider",
                        "provider": chunk.provider,
                        "fallback": getattr(chunk, "fallback", False)
                    }
                    yield f"data: {json.dumps(provider_payload)}\n\n"
                    sent_provider_event = True
                    
                if chunk.content:
                    if buffering_prefix:
                        prefix_buffer += chunk.content
                        if prefix_buffer.strip().startswith(":::visual-hero") or prefix_buffer.strip().startswith(":::generated-image"):
                            end_match = re.search(r":::(visual-hero|generated-image)\s*[\s\S]*?:::\s*", prefix_buffer)
                            if end_match:
                                remaining = prefix_buffer[end_match.end():]
                                buffering_prefix = False
                                prefix_buffer = ""
                                if remaining:
                                    full_assistant_response += remaining
                                    yield f"data: {json.dumps({'type': 'chunk', 'content': remaining})}\n\n"
                            elif len(prefix_buffer) > 600:
                                buffering_prefix = False
                                full_assistant_response += prefix_buffer
                                yield f"data: {json.dumps({'type': 'chunk', 'content': prefix_buffer})}\n\n"
                                prefix_buffer = ""
                        elif len(prefix_buffer.strip()) > 15:
                            buffering_prefix = False
                            full_assistant_response += prefix_buffer
                            yield f"data: {json.dumps({'type': 'chunk', 'content': prefix_buffer})}\n\n"
                            prefix_buffer = ""
                    else:
                        full_assistant_response += chunk.content
                        payload = json.dumps({"type": "chunk", "content": chunk.content})
                        yield f"data: {payload}\n\n"
                    
            if buffering_prefix and prefix_buffer:
                clean_rem = re.sub(r":::(visual-hero|generated-image)\s*[\s\S]*?:::\s*", "", prefix_buffer)
                if clean_rem:
                    full_assistant_response += clean_rem
                    yield f"data: {json.dumps({'type': 'chunk', 'content': clean_rem})}\n\n"

            if chunk.is_done:
                    # Final chunk with metrics
                    final_model = chunk.model
                    final_provider = chunk.provider
                    total_tokens = chunk.total_tokens
                    prompt_tokens = chunk.prompt_tokens
                    completion_tokens = chunk.completion_tokens
                    
            # 4. Success - Save Assistant Message
            latency = time.time() - start_time
            if not full_assistant_response.strip():
                full_assistant_response = "[Response was empty or interrupted. Please try again.]"
            
            # Re-open session since we are in a generator
            from database import SessionLocal
            stream_db = SessionLocal()
            try:
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_assistant_response,
                    provider=final_provider,
                    model=final_model,
                    tokens_used=total_tokens
                )
                stream_db.add(assistant_msg)
                
                # Update conversation updated_at
                conv = stream_db.query(Conversation).filter(Conversation.id == conversation_id).first()
                if conv:
                    from sqlalchemy.sql import func
                    conv.updated_at = func.now()
                
                # 5. Log AI Usage
                usage = AIUsage(
                    user_id=current_user.id,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    provider=final_provider,
                    model=final_model,
                    latency=latency,
                    estimated_cost=0.0 # Calculate based on provider/model later
                )
                stream_db.add(usage)
                
                stream_db.commit()
            finally:
                stream_db.close()
                
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            # Failure occurred that gateway couldn't handle
            # Save failure message to preserve state
            import logging
            logging.getLogger(__name__).error(f"Stream generation failed: {e}")
            import traceback
            with open("stream_debug.log", "a") as f:
                f.write(f"Stream failed: {e}\n{traceback.format_exc()}\n")
            
            safe_err = "[ERROR: The AI service encountered an unexpected error. Please try again.]"
            from database import SessionLocal
            err_db = SessionLocal()
            try:
                err_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=safe_err,
                    provider="error",
                    model="error",
                    tokens_used=0
                )
                err_db.add(err_msg)
                err_db.commit()
            finally:
                err_db.close()
                
            yield f"data: {json.dumps({'type': 'error', 'content': safe_err})}\n\n"

    return StreamingResponse(
        sse_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
