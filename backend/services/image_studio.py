"""
image_studio.py — Smart Image Studio router for Grak AI.

Handles:
  1. 100+ line long detailed prompts:
       Gemini Native Image (untruncated verbatim prompt)
       -> fallback on quota/error: LLM condensation (<350 words) + NVIDIA flux-3-image-klein -> Pollinations
  2. Multi-turn iterative image editing (v1 -> v2 -> v3...):
       Gemini Native Image with [source_image_bytes, edit_instruction]
       -> fallback on quota/error: Vision/context LLM prompt merge (<350 words) + NVIDIA flux-3-image-klein -> Pollinations
  3. Fresh standard text-to-image:
       NVIDIA flux-3-image-klein (NVIDIA_API_KEY2 -> NVIDIA_API_KEY)
       -> fallback: Gemini Native Image -> Pollinations
"""

import os
import re
import base64
import logging
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import httpx

from services.gemini_image import generate_gemini_image
from services.nvidia_image import generate_nvidia_image, DOWNLOADS_DIR
from services.image_generation import generate_ai_image

logger = logging.getLogger(__name__)

# Thresholds for classifying a prompt as a long/detailed multi-line prompt
LONG_PROMPT_MIN_LINES = 6
LONG_PROMPT_MIN_WORDS = 120
LONG_PROMPT_MIN_CHARS = 800
MAX_DIFFUSION_WORDS = 320

_GENERATED_IMAGE_BLOCK_RE = re.compile(
    r":::generated-image\s*([\s\S]*?):::",
    re.MULTILINE,
)

_FRESH_CREATION_PREFIX_RE = re.compile(
    r"^\s*(create\s+(a\s+)?(brand\s+)?new\s+(image|picture|photo|pic)|"
    r"generate\s+(a\s+)?(brand\s+)?new\s+(image|picture|photo|pic)|"
    r"draw\s+(a\s+)?(brand\s+)?new\s+|"
    r"create\s+image\s+of\s+|generate\s+image\s+of\s+)\b",
    re.IGNORECASE,
)

_EDIT_INTENT_RE = re.compile(
    r"\b("
    r"change|edit|modify|update|adjust|replace|swap|turn|convert|transform|"
    r"make\s+it|make\s+the|make\s+this|add|remove|delete|erase|put|place|"
    r"recolor|brighter|darker|zoom|crop|background|instead|on\s+top|"
    r"at\s+the\s+top|at\s+the\s+bottom|in\s+the\s+corner|same\s+image|"
    r"keep\s+everything|from\s+the\s+previous|wearing|holding|"
    r"badal|badlo|kar\s+do|kardo|lagao|laga\s+do|hatao|hata\s+do|hatado|"
    r"isme|is\s+mein|iska|iski|iske|is\s+par|is\s+pe|upar|peeche|rang"
    r")\b",
    re.IGNORECASE,
)

_SELF_REFERENCE_RE = re.compile(
    r"\b(it|this|that|same|previous|above|image|photo|picture|shirt|hair|sky|car|face|dress|text)\b",
    re.IGNORECASE,
)


def is_long_detailed_prompt(prompt: str) -> bool:
    """True when the prompt is a multi-line / highly detailed description."""
    if not prompt:
        return False
    non_empty_lines = [ln for ln in prompt.splitlines() if ln.strip()]
    words = prompt.split()
    return (
        len(non_empty_lines) >= LONG_PROMPT_MIN_LINES
        or len(words) > LONG_PROMPT_MIN_WORDS
        or len(prompt) > LONG_PROMPT_MIN_CHARS
    )


def sanitize_block_prompt(prompt: str, max_len: int = 240) -> str:
    """
    Sanitize a potentially 100-line prompt for single-line storage inside
    `:::generated-image` metadata without breaking the frontend block parser.
    """
    single = re.sub(r"\s+", " ", (prompt or "")).replace(":::", "").strip()
    if len(single) > max_len:
        return single[: max_len - 3].rstrip() + "..."
    return single or "AI Generated Visual"


def extract_latest_generated_image(history_msgs: List[Any]) -> Optional[Tuple[str, str]]:
    """
    Walk conversation history backwards and return (image_url_or_b64, prior_prompt)
    for the most recent generated image (or user-attached image).
    """
    if not history_msgs:
        return None

    for msg in reversed(history_msgs):
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        img_b64 = msg.get("image_base64") if isinstance(msg, dict) else getattr(msg, "image_base64", None)

        if role == "assistant" and content:
            matches = list(_GENERATED_IMAGE_BLOCK_RE.finditer(content))
            if matches:
                body = matches[-1].group(1)
                img_m = re.search(r"^image:\s*(.+)$", body, re.MULTILINE)
                prompt_m = re.search(r"^prompt:\s*(.+)$", body, re.MULTILINE)
                if img_m:
                    url = img_m.group(1).strip()
                    prior_prompt = prompt_m.group(1).strip() if prompt_m else ""
                    if url:
                        return url, prior_prompt

        if role == "user" and img_b64:
            return img_b64, content or ""

    return None


def is_followup_edit_request(
    query: str,
    history_msgs: List[Any],
    mode: Optional[str] = None,
) -> Optional[Tuple[str, str]]:
    """
    Detect conversational follow-up image edit requests right after a generated image.
    Returns (target_image_ref, prior_prompt) if this turn should edit the previous image,
    else None.
    """
    if not query or not query.strip():
        return None

    latest = extract_latest_generated_image(history_msgs)
    if not latest:
        return None

    # Do not match if the query starts with an explicit "create a brand new image..." phrase
    # unless it explicitly refers back to "same" / "previous" / "this".
    q = query.strip()
    if _FRESH_CREATION_PREFIX_RE.search(q) and not re.search(
        r"\b(same|previous|this|above|from\s+before)\b", q, re.IGNORECASE
    ):
        return None

    # Ignore very long fresh 100-line descriptions unless explicitly phrased as an edit
    is_long = is_long_detailed_prompt(q)
    if is_long and not re.match(r"^\s*(edit|change|modify|update|keep)\b", q, re.IGNORECASE):
        return None

    if _EDIT_INTENT_RE.search(q):
        return latest

    # In Create Image mode, concise modifier phrases like "with sunglasses" or "at sunset"
    # immediately following an image also act as edits.
    if mode == "create_image":
        words = q.split()
        if len(words) <= 10 and (
            q.lower().startswith(("with ", "without ", "in ", "at ", "on ", "more ", "less "))
            or _SELF_REFERENCE_RE.search(q)
        ):
            return latest

    return None


def _guess_mime_from_path(path: str) -> str:
    lower = path.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/png"


async def load_image_for_edit(
    image_ref: Optional[str] = None,
    image_base64: Optional[str] = None,
) -> Tuple[Optional[bytes], str]:
    """
    Resolve an image reference (data URI, `/api/images/...`, `/downloads/...`, or HTTP URL)
    into raw (bytes, mime_type).
    """
    raw_b64_source = image_base64 or (
        image_ref if image_ref and image_ref.strip().startswith("data:") else None
    )
    if raw_b64_source:
        try:
            mime = "image/png"
            payload = raw_b64_source.strip()
            if "base64," in payload:
                prefix, payload = payload.split("base64,", 1)
                if "data:" in prefix and ";" in prefix:
                    mime = prefix.split("data:", 1)[1].split(";", 1)[0].strip() or "image/png"
            decoded = base64.b64decode(payload)
            if decoded:
                return decoded, mime
        except Exception as exc:
            logger.warning(f"[ImageStudio] Failed to decode base64 source image: {exc}")

    if not image_ref or not image_ref.strip():
        return None, "image/png"

    ref = image_ref.strip()
    parsed = urllib.parse.urlparse(ref)
    path = parsed.path or ref

    # Local downloads lookup (/api/images/<file> or /downloads/<file>)
    for prefix in ("/api/images/", "/downloads/"):
        if path.startswith(prefix) or prefix in path:
            fname = os.path.basename(path.split("?")[0])
            if fname:
                local_path = os.path.join(DOWNLOADS_DIR, fname)
                if os.path.isfile(local_path):
                    try:
                        with open(local_path, "rb") as f:
                            return f.read(), _guess_mime_from_path(local_path)
                    except Exception as exc:
                        logger.warning(f"[ImageStudio] Could not read local image {local_path}: {exc}")

    # Remote HTTP/HTTPS URL (e.g., Pollinations fallback image)
    if ref.startswith(("http://", "https://")):
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(ref)
                if resp.status_code == 200 and len(resp.content) > 100:
                    ctype = resp.headers.get("content-type", "").split(";")[0].strip()
                    mime = ctype if ctype.startswith("image/") else _guess_mime_from_path(path)
                    return resp.content, mime
        except Exception as exc:
            logger.warning(f"[ImageStudio] Failed to fetch remote source image {ref[:80]}: {exc}")

    return None, "image/png"


def _deterministic_condense(prompt: str, max_words: int = MAX_DIFFUSION_WORDS) -> str:
    """Fast local fallback condensation preserving high-signal visual phrases under `max_words`."""
    lines = []
    seen = set()
    for raw_line in (prompt or "").splitlines():
        cleaned = re.sub(r"^\s*[-*•\d.)]+\s*", "", raw_line).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            lines.append(cleaned)

    joined = ", ".join(lines) if lines else (prompt or "").strip()
    words = joined.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return joined


async def condense_prompt_for_diffusion(
    prompt: str,
    max_words: int = MAX_DIFFUSION_WORDS,
    source_image_bytes: Optional[bytes] = None,
    source_image_mime: str = "image/png",
    prior_prompt: Optional[str] = None,
) -> str:
    """
    Condense a 100+ line detailed prompt (or synthesize an edit-merged prompt when editing
    falls back from Gemini Native Image) into <= max_words words via a fast text/vision LLM.
    Always falls back cleanly to deterministic condensation if LLM calls fail.
    """
    raw = (prompt or "").strip()
    if not raw:
        return ""

    if not source_image_bytes and len(raw.split()) <= max_words and len(raw.splitlines()) < LONG_PROMPT_MIN_LINES:
        return raw

    try:
        from services.ai.gateway import AIGateway

        gw = AIGateway()
        if source_image_bytes:
            b64 = base64.b64encode(source_image_bytes).decode("utf-8")
            data_uri = f"data:{source_image_mime};base64,{b64}"
            system_msg = (
                f"You are an expert visual prompt engineer. Describe the attached image in detail "
                f"and seamlessly apply the user's requested edit to produce ONE single cohesive image "
                f"generation prompt under {max_words} words. Preserve the original subject, pose, "
                f"composition, lighting, colors, and style for everything not changed by the edit. "
                f"Output ONLY the final prompt text — no intro, no bullet points, no markdown."
            )
            user_text = (
                f"Prior prompt context: {prior_prompt or 'N/A'}\n"
                f"Requested edit: {raw}"
            )
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text, "image_base64": data_uri},
            ]
        else:
            system_msg = (
                f"You are an expert diffusion prompt compressor. Condense the user's long detailed "
                f"scene description into ONE dense, high-signal visual prompt under {max_words} words. "
                f"Preserve every important subject, clothing, action, setting, background, lighting, "
                f"camera angle, lens/framing, color palette, mood, and art style. "
                f"Output ONLY the condensed visual prompt — no preamble, no markdown, no bullet list."
            )
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": raw},
            ]

        resp = await gw.chat(messages, apply_identity=False)
        condensed = re.sub(r"\s+", " ", (resp.content or "")).strip().strip('"')
        if condensed:
            words = condensed.split()
            if len(words) > max_words:
                condensed = " ".join(words[:max_words])
            logger.info(
                f"[ImageStudio] Condensed prompt via {resp.provider} ({resp.model}): "
                f"{len(raw.split())}w -> {len(condensed.split())}w"
            )
            return condensed
    except Exception as exc:
        logger.warning(f"[ImageStudio] LLM prompt condensation failed ({exc}); using deterministic fallback.")

    if source_image_bytes and prior_prompt:
        merged = f"{prior_prompt.strip()}, modified so that: {raw}"
        return _deterministic_condense(merged, max_words=max_words)
    return _deterministic_condense(raw, max_words=max_words)


async def generate_or_edit_image(
    prompt: str,
    source_image_ref: Optional[str] = None,
    source_image_b64: Optional[str] = None,
    prior_prompt: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    is_diagram: bool = False,
) -> Dict[str, Any]:
    """
    Unified smart entry point for Grak AI Image Studio:
      - Diagram intent -> Pollinations schematic pipeline
      - Editing / 100+ line detailed prompt -> Gemini Native Image first (untruncated / pixel-aware),
        automatic LLM-condensed fallback to NVIDIA flux-3-image-klein -> Pollinations
      - Fresh standard prompt -> NVIDIA flux-3-image-klein (NVIDIA_API_KEY2 -> NVIDIA_API_KEY) first,
        fallback to Gemini Native Image -> Pollinations
    """
    raw = (prompt or "").strip()
    if not raw:
        return {
            "success": False,
            "error": "Empty prompt",
            "url": None,
            "provider": "none",
            "model": "none",
            "fallback": False,
            "edited": False,
        }

    src_bytes, src_mime = await load_image_for_edit(source_image_ref, source_image_b64)
    is_edit = src_bytes is not None
    is_long = is_long_detailed_prompt(raw)

    logger.info(
        f"[ImageStudio] Routing request: is_edit={is_edit} is_long={is_long} "
        f"is_diagram={is_diagram} lines={len(raw.splitlines())} words={len(raw.split())}"
    )

    # Diagram requests (only when not editing a specific image)
    if is_diagram and not is_edit:
        diag_res = await generate_ai_image(raw, width=width, height=height, is_diagram=True)
        diag_res.setdefault("provider", "pollinations")
        diag_res.setdefault("model", "flux")
        diag_res["fallback"] = False
        diag_res["edited"] = False
        return diag_res

    # Path A: Image Editing OR Long Detailed Prompt -> Gemini Native Image Primary
    if is_edit or is_long:
        gem_res = await generate_gemini_image(
            prompt=raw,
            source_image_bytes=src_bytes,
            source_image_mime=src_mime,
        )
        if gem_res.get("success"):
            gem_res["edited"] = is_edit
            return gem_res

        logger.warning(
            f"[ImageStudio] ⚠ FALLBACK → Condensing prompt for NVIDIA/Pollinations. "
            f"Gemini reason: {gem_res.get('error')}"
        )
        diffusion_prompt = await condense_prompt_for_diffusion(
            prompt=raw,
            max_words=MAX_DIFFUSION_WORDS,
            source_image_bytes=src_bytes,
            source_image_mime=src_mime,
            prior_prompt=prior_prompt,
        )
        nv_res = await generate_nvidia_image(
            diffusion_prompt,
            width=width,
            height=height,
            use_fallback_on_error=True,
        )
        nv_res["prompt"] = raw
        nv_res["fallback"] = True
        nv_res["edited"] = is_edit
        return nv_res

    # Path B: Fresh Standard Prompt -> NVIDIA Primary -> Gemini Fallback -> Pollinations Fallback
    nv_res = await generate_nvidia_image(
        raw,
        width=width,
        height=height,
        use_fallback_on_error=False,
    )
    if nv_res.get("success"):
        nv_res["edited"] = False
        return nv_res

    logger.warning(
        f"[ImageStudio] ⚠ FALLBACK → Trying Gemini Native Image after NVIDIA failure: "
        f"{nv_res.get('error')}"
    )
    gem_res = await generate_gemini_image(prompt=raw)
    if gem_res.get("success"):
        gem_res["fallback"] = True
        gem_res["edited"] = False
        return gem_res

    logger.warning(
        f"[ImageStudio] ⚠ FALLBACK → Pollinations after NVIDIA and Gemini failures. "
        f"Gemini reason: {gem_res.get('error')}"
    )
    poll_res = await generate_ai_image(raw, width=width, height=height)
    if poll_res.get("success"):
        return {
            "success": True,
            "url": poll_res["url"],
            "prompt": raw,
            "enhanced_prompt": poll_res.get("enhanced_prompt", raw),
            "provider": "pollinations",
            "model": poll_res.get("model", "flux"),
            "fallback": True,
            "edited": False,
        }

    return {
        "success": False,
        "error": f"All image providers failed (NVIDIA: {nv_res.get('error')}; Gemini: {gem_res.get('error')})",
        "url": None,
        "provider": "none",
        "model": "none",
        "fallback": True,
        "edited": False,
    }
