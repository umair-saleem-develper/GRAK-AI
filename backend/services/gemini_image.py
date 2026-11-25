"""
gemini_image.py — Native Gemini image generation & multi-turn image editing for Grak AI.

Models (tried in order):
  1. gemini-2.5-flash-image (primary native image generation & editing model)
  2. gemini-2.0-flash-exp-image-generation (secondary Gemini image fallback)
  (Plus optional GEMINI_IMAGE_MODEL env override prepended if configured.)

Supports:
  - Full, untruncated 100+ line prompts (scene descriptions, camera, lighting, details)
  - Image-to-image multi-turn editing via (source_image_bytes, edit_instruction)
  - Fast fail (attempts=1) on 429 / 404 / error so Image Studio falls back cleanly
    to NVIDIA flux-3-image-klein -> Pollinations without stalling SSE streams.
"""

import os
import uuid
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

DEFAULT_GEMINI_IMAGE_MODELS: Tuple[str, ...] = (
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
)

_MIME_TO_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}


def _get_gemini_image_models() -> List[str]:
    models: List[str] = []
    override = os.getenv("GEMINI_IMAGE_MODEL", "").strip()
    if override:
        models.append(override)
    for m in DEFAULT_GEMINI_IMAGE_MODELS:
        if m not in models:
            models.append(m)
    return models


def _build_edit_instruction(prompt: str) -> str:
    return (
        "Edit the attached reference image according to the user's exact instruction below. "
        "Preserve the original subject identity, framing, lighting, perspective, and unmentioned details "
        "while applying the requested modifications cleanly and naturally.\n\n"
        f"Edit instruction:\n{prompt}"
    )


def _extract_image_part(response: Any) -> Tuple[Optional[bytes], str, str]:
    """
    Extract (image_bytes, mime_type, optional_text) from a google-genai GenerateContentResponse.
    """
    candidates = getattr(response, "candidates", None) or []
    text_notes: List[str] = []

    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            txt = getattr(part, "text", None)
            if txt:
                text_notes.append(txt.strip())

            inline = getattr(part, "inline_data", None)
            if inline is not None:
                raw_data = getattr(inline, "data", None)
                mime_type = getattr(inline, "mime_type", None) or "image/png"
                if isinstance(raw_data, (bytes, bytearray)) and len(raw_data) > 0:
                    return bytes(raw_data), mime_type, "\n".join(text_notes)
                if isinstance(raw_data, str) and raw_data.strip():
                    b64_payload = raw_data.split(",", 1)[1] if "," in raw_data else raw_data
                    try:
                        decoded = base64.b64decode(b64_payload)
                        if len(decoded) > 0:
                            return decoded, mime_type, "\n".join(text_notes)
                    except Exception:
                        pass

    return None, "image/png", "\n".join(text_notes)


async def generate_gemini_image(
    prompt: str,
    source_image_bytes: Optional[bytes] = None,
    source_image_mime: str = "image/png",
    timeout_ms: int = 60000,
) -> Dict[str, Any]:
    """
    Generate or edit an image using Google GenAI native image models.
    Never truncates `prompt` — 100+ line prompts are sent verbatim.
    """
    raw_prompt = (prompt or "").strip()
    if not raw_prompt:
        return {
            "success": False,
            "error": "Empty prompt",
            "url": None,
            "provider": "none",
            "model": "none",
        }

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        reason = "GEMINI_API_KEY is not configured"
        logger.warning(f"[GeminiImage] {reason}")
        return {
            "success": False,
            "error": reason,
            "url": None,
            "provider": "none",
            "model": "none",
        }

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        reason = f"google-genai SDK unavailable: {exc}"
        logger.warning(f"[GeminiImage] {reason}")
        return {
            "success": False,
            "error": reason,
            "url": None,
            "provider": "none",
            "model": "none",
        }

    is_edit = bool(source_image_bytes)
    models = _get_gemini_image_models()

    if is_edit:
        contents: Any = [
            types.Part.from_bytes(data=source_image_bytes, mime_type=source_image_mime or "image/png"),
            types.Part.from_text(text=_build_edit_instruction(raw_prompt)),
        ]
    else:
        # Preserve the full prompt verbatim (supports 100+ line descriptions)
        contents = [types.Part.from_text(text=raw_prompt)]

    http_opts = types.HttpOptions(
        timeout=timeout_ms,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
    client = genai.Client(api_key=api_key, http_options=http_opts)
    config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])

    last_error = "unknown error"
    for idx, model_name in enumerate(models):
        logger.info(
            f"[GeminiImage] Calling model={model_name} edit={is_edit} "
            f"prompt_chars={len(raw_prompt)} prompt_lines={len(raw_prompt.splitlines())}"
        )
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            img_bytes, out_mime, caption = _extract_image_part(response)
            if img_bytes:
                ext = _MIME_TO_EXT.get(out_mime.lower(), "png")
                fname = f"gemini_{uuid.uuid4().hex[:12]}.{ext}"
                out_path = os.path.join(DOWNLOADS_DIR, fname)
                with open(out_path, "wb") as f:
                    f.write(img_bytes)

                image_url = f"/api/images/{fname}"
                logger.info(
                    f"[GeminiImage] SUCCESS model={model_name} edit={is_edit} "
                    f"file={fname} bytes={len(img_bytes)}"
                )
                return {
                    "success": True,
                    "url": image_url,
                    "prompt": raw_prompt,
                    "enhanced_prompt": raw_prompt,
                    "provider": "gemini",
                    "model": model_name,
                    "edited": is_edit,
                    "fallback": idx > 0,
                    "caption": caption or None,
                }

            last_error = f"{model_name} returned no image data (text={caption[:120]})"
            logger.warning(f"[GeminiImage] {last_error}")

        except Exception as exc:
            last_error = f"{model_name} error: {exc}"
            logger.warning(f"[GeminiImage] FAILED model={model_name}: {str(exc)[:300]}")

    return {
        "success": False,
        "error": last_error,
        "url": None,
        "provider": "none",
        "model": "none",
        "edited": is_edit,
    }
