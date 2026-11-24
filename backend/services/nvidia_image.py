"""
nvidia_image.py — NVIDIA FLUX text-to-image service for Grak AI.

Endpoint:  https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-3-image-klein
Payload:   {"prompt": "...", "width": 1024, "height": 1024, "seed": 0, "steps": 50}
           (exact match of build.nvidia.com Python sample)

Key env:   NVIDIA_API_KEY  (must start with nvapi-)
           Legacy fallback: NVIDIA_IMAGE_MODEL  (if NVIDIA_API_KEY absent)

Fallback:  Pollinations, used ONLY on error / 429 / timeout.
           A WARNING is always logged when fallback fires.

Provider:  Every return dict contains "provider": "nvidia" | "pollinations" | "none"
           so callers can log / debug without touching the UI.
"""

import os
import uuid
import base64
import logging
import httpx
from typing import Dict, Any

from services.image_generation import generate_ai_image as _pollinations

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ── Model config (from build.nvidia.com sample) ──────────────────────────────
NVIDIA_MODEL_ID   = "black-forest-labs/flux-3-image-klein"
NVIDIA_INVOKE_URL = f"https://ai.api.nvidia.com/v1/genai/{NVIDIA_MODEL_ID}"

# ── API key ───────────────────────────────────────────────────────────────────
def _get_key() -> str:
    """Returns the NVIDIA API key. Never logs it."""
    key = os.getenv("NVIDIA_API_KEY", "").strip().strip('"').strip("'")
    if not key.startswith("nvapi-"):
        # Legacy: key stored under old name; strip accidental leading '=' chars
        candidate = os.getenv("NVIDIA_IMAGE_MODEL", "").strip().strip('"').strip("'").lstrip("=")
        if candidate.startswith("nvapi-"):
            key = candidate
    return key

# ── Prompt cleaning ───────────────────────────────────────────────────────────
_STRIP_PREFIXES = [
    "create image of ", "create image ", "generate image of ", "generate image ",
    "make image of ", "make an image of ", "make a image of ",
    "draw an image of ", "draw image of ", "draw a ", "draw an ",
    "generate a photo of ", "generate photo of ",
    "create a photo of ", "create photo of ",
    "photo of ", "image of ", "picture of ",
    "like a ", "like an ", "like ",
]

_QUALITY = ", detailed photo, soft natural lighting, high quality, 8k resolution, photorealistic"


def _clean_prompt(raw: str) -> str:
    """
    Strip chip/command prefixes, then expand short subjects with quality modifiers.
    The user's subject is ALWAYS preserved verbatim (cat stays cat).
    """
    s = raw.strip()
    changed = True
    while changed:
        changed = False
        lower = s.lower()
        for prefix in _STRIP_PREFIXES:
            if lower.startswith(prefix):
                s = s[len(prefix):].strip()
                changed = True
                break

    if not s:
        s = raw.strip()

    words = s.split()
    if len(words) <= 5:
        article = "an" if s[0].lower() in "aeiou" else "a"
        return f"{article} {s}{_QUALITY}"
    return s + _QUALITY


# ── Main function ─────────────────────────────────────────────────────────────
async def generate_nvidia_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    use_fallback_on_error: bool = True,
) -> Dict[str, Any]:
    """
    Calls NVIDIA FLUX (flux-3-image-klein).
    Falls back to Pollinations on any error, logging a WARNING with the reason.
    Returns dict always including 'provider': 'nvidia' | 'pollinations' | 'none'.
    """
    raw = prompt.strip() if prompt else ""
    if not raw:
        return {"success": False, "error": "Empty prompt", "url": None, "provider": "none"}

    enhanced = _clean_prompt(raw)
    api_key  = _get_key()

    if not api_key.startswith("nvapi-"):
        reason = "NVIDIA_API_KEY missing or does not start with 'nvapi-'"
        logger.warning(f"[NVIDIA] {reason}")
        return await _fallback(raw, reason, width, height, use_fallback_on_error)

    # ── Exact payload from build.nvidia.com Python sample ────────────────────
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    payload = {
        "prompt": enhanced,
        "width":  width,
        "height": height,
        "seed":   0,
        "steps":  50,
    }

    logger.info(
        f"[NVIDIA] Calling provider=nvidia model={NVIDIA_MODEL_ID} "
        f"prompt='{enhanced[:80]}'"
    )

    nvidia_error: str | None = None
    image_url:    str | None = None

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(NVIDIA_INVOKE_URL, headers=headers, json=payload)

        logger.info(
            f"[NVIDIA] HTTP status={response.status_code} model={NVIDIA_MODEL_ID}"
        )

        if response.status_code == 200:
            data = response.json()
            b64 = None

            # Parse all known NVIDIA response shapes
            if "artifacts" in data and isinstance(data["artifacts"], list) and data["artifacts"]:
                art = data["artifacts"][0]
                b64 = art.get("base64") or art.get("b64_json")
            elif "image" in data:
                b64 = data["image"]
            elif "b64_json" in data:
                b64 = data["b64_json"]
            elif "data" in data and isinstance(data["data"], list) and data["data"]:
                b64 = data["data"][0].get("b64_json")
                if not b64:
                    image_url = data["data"][0].get("url")

            if b64:
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                try:
                    img_bytes = base64.b64decode(b64)
                    fname     = f"nvidia_{uuid.uuid4().hex[:12]}.png"
                    with open(os.path.join(DOWNLOADS_DIR, fname), "wb") as f:
                        f.write(img_bytes)
                    image_url = f"/api/images/{fname}"
                    logger.info(
                        f"[NVIDIA] SUCCESS provider=nvidia model={NVIDIA_MODEL_ID} "
                        f"file={fname} bytes={len(img_bytes)}"
                    )
                except Exception as e:
                    nvidia_error = f"base64 decode failed: {e}"
                    logger.error(f"[NVIDIA] {nvidia_error}")
            elif not image_url:
                nvidia_error = f"Unrecognised response keys: {list(data.keys())}"
                logger.warning(f"[NVIDIA] {nvidia_error} | body[:300]={response.text[:300]}")
        else:
            nvidia_error = (
                f"HTTP {response.status_code} from NVIDIA — "
                f"body: {response.text[:400]}"
            )
            logger.warning(f"[NVIDIA] FAILED {nvidia_error}")

    except httpx.TimeoutException:
        nvidia_error = "Request timed out after 90s"
        logger.error(f"[NVIDIA] {nvidia_error}")
    except Exception as exc:
        nvidia_error = str(exc)
        logger.error(f"[NVIDIA] Exception: {exc}")

    if image_url:
        return {
            "success":         True,
            "url":             image_url,
            "prompt":          raw,
            "enhanced_prompt": enhanced,
            "provider":        "nvidia",
            "fallback":        False,
        }

    return await _fallback(raw, nvidia_error or "unknown error", width, height, use_fallback_on_error)


async def _fallback(
    raw_prompt: str,
    reason: str,
    width: int,
    height: int,
    enabled: bool,
) -> Dict[str, Any]:
    """Logs a WARNING then calls Pollinations. Never silent."""
    if not enabled:
        return {"success": False, "error": reason, "url": None, "provider": "none"}

    logger.warning(
        f"[NVIDIA] ⚠ FALLBACK → Pollinations. Reason: {reason}"
    )
    result = await _pollinations(raw_prompt, width=width, height=height)
    if result.get("success"):
        logger.info(f"[NVIDIA] Fallback succeeded via Pollinations for prompt='{raw_prompt[:60]}'")
        return {
            "success":         True,
            "url":             result["url"],
            "prompt":          raw_prompt,
            "enhanced_prompt": result.get("enhanced_prompt", raw_prompt),
            "provider":        "pollinations",
            "fallback":        True,
        }
    return {
        "success":  False,
        "error":    "Both NVIDIA and Pollinations failed",
        "url":      None,
        "provider": "none",
        "fallback": True,
    }
