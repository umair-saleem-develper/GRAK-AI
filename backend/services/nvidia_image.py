"""
nvidia_image.py — NVIDIA FLUX text-to-image service for Grak AI.

Primary Model: black-forest-labs/flux-3-image-klein
Endpoint:      https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux-3-image-klein
Payload:       {"prompt": "...", "width": 1024, "height": 1024, "steps": 50}
               (strictly omits unsupported fields such as `seed` that cause HTTP 422 extra_forbidden)

Key priority:
  1. NVIDIA_API_KEY2 (primary key for flux-3-image-klein)
  2. NVIDIA_API_KEY  (fallback if NVIDIA_API_KEY2 is missing or fails)
  3. NVIDIA_IMAGE_MODEL (legacy fallback if neither key above is set)

Fallback chain on error / 4xx / 5xx / 429 / timeout:
  1. Secondary NVIDIA key (if NVIDIA_API_KEY differs from NVIDIA_API_KEY2)
  2. Pollinations (services.image_generation.generate_ai_image)
  A WARNING is always logged explaining why fallback occurred.

Provider:
  Every return dict includes "provider": "nvidia" | "pollinations" | "none",
  "model": <model_id>, and "fallback": bool so callers can log/debug cleanly.
"""

import os
import uuid
import base64
import logging
import httpx
from typing import Dict, Any, List, Tuple

from services.image_generation import generate_ai_image as _pollinations

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ── Model config ─────────────────────────────────────────────────────────────
NVIDIA_MODEL_ID = "black-forest-labs/flux-3-image-klein"
NVIDIA_INVOKE_URL = f"https://ai.api.nvidia.com/v1/genai/{NVIDIA_MODEL_ID}"
NVIDIA_TIMEOUT_SECONDS = 60.0


def _clean_env_key(var_name: str) -> str:
    val = os.getenv(var_name, "").strip().strip('"').strip("'").lstrip("=")
    return val


def _get_key_candidates() -> List[Tuple[str, str]]:
    """
    Returns ordered (env_var_name, key_value) candidates without ever logging values.
    Priority: NVIDIA_API_KEY2 -> NVIDIA_API_KEY -> NVIDIA_IMAGE_MODEL (legacy).
    """
    candidates: List[Tuple[str, str]] = []
    seen = set()

    for var_name in ("NVIDIA_API_KEY2", "NVIDIA_API_KEY", "NVIDIA_IMAGE_MODEL"):
        key = _clean_env_key(var_name)
        if key.startswith("nvapi-") and key not in seen:
            candidates.append((var_name, key))
            seen.add(key)

    return candidates


def _get_key() -> str:
    """Returns the primary NVIDIA API key (NVIDIA_API_KEY2 first, then NVIDIA_API_KEY). Never logs it."""
    candidates = _get_key_candidates()
    return candidates[0][1] if candidates else ""


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
    The user's subject is ALWAYS preserved verbatim.
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


def _extract_nvidia_image(data: Dict[str, Any]) -> Tuple[str | None, str | None]:
    """
    Parse known NVIDIA NIM image response formats.
    Returns (base64_str, direct_url).
    """
    b64 = None
    direct_url = None

    if "artifacts" in data and isinstance(data["artifacts"], list) and data["artifacts"]:
        art = data["artifacts"][0]
        b64 = art.get("base64") or art.get("b64_json")
        if not b64:
            direct_url = art.get("url")
    elif "image" in data:
        val = data["image"]
        if isinstance(val, str) and val.startswith(("http://", "https://")):
            direct_url = val
        else:
            b64 = val
    elif "b64_json" in data:
        b64 = data["b64_json"]
    elif "url" in data or "image_url" in data:
        direct_url = data.get("url") or data.get("image_url")
    elif "data" in data and isinstance(data["data"], list) and data["data"]:
        b64 = data["data"][0].get("b64_json")
        if not b64:
            direct_url = data["data"][0].get("url")

    return b64, direct_url


async def _call_nvidia_nim(
    api_key: str,
    key_source: str,
    enhanced_prompt: str,
    width: int,
    height: int,
) -> Tuple[str | None, str | None]:
    """
    Calls NVIDIA flux-3-image-klein with clean schema (no `seed` field).
    Auto-retries once with prompt-only payload if 422 extra_forbidden occurs.
    Returns (image_url, error_reason).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    payload = {
        "prompt": enhanced_prompt,
        "width": width,
        "height": height,
        "steps": 50,
    }

    logger.info(
        f"[NVIDIA] Calling provider=nvidia model={NVIDIA_MODEL_ID} "
        f"key_source={key_source} prompt='{enhanced_prompt[:80]}'"
    )

    try:
        async with httpx.AsyncClient(timeout=NVIDIA_TIMEOUT_SECONDS) as client:
            response = await client.post(NVIDIA_INVOKE_URL, headers=headers, json=payload)

            if response.status_code == 422:
                logger.warning(
                    f"[NVIDIA] HTTP 422 schema mismatch with full params ({response.text[:200]}). "
                    f"Retrying {NVIDIA_MODEL_ID} with minimal prompt-only payload."
                )
                response = await client.post(
                    NVIDIA_INVOKE_URL,
                    headers=headers,
                    json={"prompt": enhanced_prompt},
                )

        logger.info(
            f"[NVIDIA] HTTP status={response.status_code} model={NVIDIA_MODEL_ID} key_source={key_source}"
        )

        if response.status_code == 200:
            data = response.json()
            b64, direct_url = _extract_nvidia_image(data)

            if b64:
                if "," in b64:
                    b64 = b64.split(",", 1)[1]
                try:
                    img_bytes = base64.b64decode(b64)
                    fname = f"nvidia_{uuid.uuid4().hex[:12]}.png"
                    with open(os.path.join(DOWNLOADS_DIR, fname), "wb") as f:
                        f.write(img_bytes)
                    image_url = f"/api/images/{fname}"
                    logger.info(
                        f"[NVIDIA] SUCCESS provider=nvidia model={NVIDIA_MODEL_ID} "
                        f"key_source={key_source} file={fname} bytes={len(img_bytes)}"
                    )
                    return image_url, None
                except Exception as e:
                    err = f"base64 decode failed: {e}"
                    logger.error(f"[NVIDIA] {err}")
                    return None, err

            if direct_url:
                logger.info(
                    f"[NVIDIA] SUCCESS provider=nvidia model={NVIDIA_MODEL_ID} "
                    f"key_source={key_source} direct_url=true"
                )
                return direct_url, None

            err = f"Unrecognised response keys: {list(data.keys())}"
            logger.warning(f"[NVIDIA] {err} | body[:300]={response.text[:300]}")
            return None, err

        err = f"HTTP {response.status_code} from NVIDIA ({key_source}) — body: {response.text[:400]}"
        logger.warning(f"[NVIDIA] FAILED {err}")
        return None, err

    except httpx.TimeoutException:
        err = f"Request timed out after {int(NVIDIA_TIMEOUT_SECONDS)}s ({key_source})"
        logger.error(f"[NVIDIA] {err}")
        return None, err
    except Exception as exc:
        err = f"{key_source} exception: {exc}"
        logger.error(f"[NVIDIA] Exception: {exc}")
        return None, err


# ── Main function ─────────────────────────────────────────────────────────────
async def generate_nvidia_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    use_fallback_on_error: bool = True,
) -> Dict[str, Any]:
    """
    Primary: NVIDIA FLUX (black-forest-labs/flux-3-image-klein) using NVIDIA_API_KEY2
    (falling back to NVIDIA_API_KEY if NVIDIA_API_KEY2 is absent or fails).
    Automatic fallback: Pollinations on error / 4xx / 5xx / 429 / timeout.
    """
    raw = prompt.strip() if prompt else ""
    if not raw:
        return {"success": False, "error": "Empty prompt", "url": None, "provider": "none"}

    enhanced = _clean_prompt(raw)
    key_candidates = _get_key_candidates()

    if not key_candidates:
        reason = "NVIDIA_API_KEY2 / NVIDIA_API_KEY missing or does not start with 'nvapi-'"
        logger.warning(f"[NVIDIA] {reason}")
        return await _fallback(raw, reason, width, height, use_fallback_on_error)

    last_error = "unknown error"
    for idx, (key_source, api_key) in enumerate(key_candidates):
        if idx > 0:
            logger.warning(
                f"[NVIDIA] ⚠ FALLBACK → Retrying {NVIDIA_MODEL_ID} with {key_source}. "
                f"Previous failure: {last_error}"
            )
        image_url, err = await _call_nvidia_nim(api_key, key_source, enhanced, width, height)
        if image_url:
            return {
                "success": True,
                "url": image_url,
                "prompt": raw,
                "enhanced_prompt": enhanced,
                "provider": "nvidia",
                "model": NVIDIA_MODEL_ID,
                "fallback": idx > 0,
            }
        last_error = err or "unknown error"

    return await _fallback(raw, last_error, width, height, use_fallback_on_error)


async def _fallback(
    raw_prompt: str,
    reason: str,
    width: int,
    height: int,
    enabled: bool,
) -> Dict[str, Any]:
    """Logs a WARNING then calls Pollinations. Never silent."""
    if not enabled:
        return {"success": False, "error": reason, "url": None, "provider": "none", "model": "none"}

    logger.warning(
        f"[NVIDIA] ⚠ FALLBACK → Pollinations. Reason: {reason}"
    )
    result = await _pollinations(raw_prompt, width=width, height=height)
    if result.get("success"):
        logger.info(f"[NVIDIA] Fallback succeeded via Pollinations for prompt='{raw_prompt[:60]}'")
        return {
            "success": True,
            "url": result["url"],
            "prompt": raw_prompt,
            "enhanced_prompt": result.get("enhanced_prompt", raw_prompt),
            "provider": "pollinations",
            "model": result.get("model", "flux"),
            "fallback": True,
        }
    return {
        "success": False,
        "error": f"NVIDIA ({reason}) and Pollinations fallback both failed",
        "url": None,
        "provider": "none",
        "model": "none",
        "fallback": True,
    }
