import os
import urllib.parse
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def generate_ai_image(
    prompt: str, 
    width: int = 1024, 
    height: int = 768, 
    model: str = "flux",
    is_diagram: bool = False
) -> Dict[str, Any]:
    """
    Real AI Image Generation using Pollinations FLUX.1/SDXL engine.
    Performs pre-flight verification to ensure the generated image is accessible.
    Never returns a fake success.
    """
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return {"success": False, "error": "Empty prompt provided", "url": None}

    # Enhance prompt for clarity and detail
    words = clean_prompt.split()
    subject = clean_prompt
    changed = True
    while changed:
        changed = False
        lower = subject.lower()
        for prefix in ["like a ", "like an ", "like ", "generate image of ", "generate photo of ", "generate a ", "generate an ", "generate ", "create image of ", "create photo of ", "create a ", "create an ", "create ", "draw an image of ", "draw a ", "draw an ", "draw ", "make an image of ", "make a ", "make ", "picture of ", "image of ", "photo of "]:
            if lower.startswith(prefix):
                subject = subject[len(prefix):].strip()
                changed = True
                break

    if is_diagram and "diagram" not in clean_prompt.lower():
        enhanced_prompt = f"schematic diagram of {subject}, labeled callouts, clean background, technical illustration"
    elif len(words) < 4:
        enhanced_prompt = f"a detailed photo of {subject}, professional lighting, high quality, 8k resolution"
    elif not is_diagram and len(words) < 7:
        enhanced_prompt = f"{clean_prompt}, highly detailed, 8k resolution, crisp lighting"
    else:
        enhanced_prompt = clean_prompt

    if len(enhanced_prompt) > 2200:
        enhanced_prompt = enhanced_prompt[:2200].rsplit(" ", 1)[0]

    encoded = urllib.parse.quote(enhanced_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model={model}&nologo=true&enhance=false"

    # Pre-flight check with a fast HEAD/GET request to verify the service is reachable
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            resp = await client.get(image_url)

            # ── Pollinations rate-limit / promo card detection ─────────────────
            # Rate-limited responses are typically tiny PNGs or HTML pages served
            # with a non-image content-type.  Reject anything that:
            #   (a) is not an image MIME type, OR
            #   (b) is suspiciously small (< 3 kB — real images are always larger)
            content_type = resp.headers.get("content-type", "").lower().split(";")[0].strip()
            is_image_ct = content_type.startswith("image/")
            is_too_small = len(resp.content) < 3000

            if resp.status_code == 200 and is_image_ct and not is_too_small:
                logger.info(
                    f"[ImageGeneration] Successfully generated image "
                    f"({len(resp.content)} bytes, ct={content_type}) for: {clean_prompt[:50]}"
                )
                return {
                    "success": True,
                    "url": image_url,
                    "prompt": clean_prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "width": width,
                    "height": height,
                    "model": model,
                    "size_bytes": len(resp.content),
                }

            if resp.status_code == 200 and (not is_image_ct or is_too_small):
                logger.warning(
                    f"[ImageGeneration] Pollinations returned a promo/rate-limit response "
                    f"(size={len(resp.content)}, ct={content_type}). Treating as failure."
                )
                return {
                    "success": False,
                    "error": (
                        "Image generation is currently rate-limited by Pollinations. "
                        "Please try again in a moment."
                    ),
                    "url": None,
                }

            logger.warning(f"[ImageGeneration] Provider returned status {resp.status_code}")
            return {
                "success": False,
                "error": f"Image generation service returned status {resp.status_code}",
                "url": None,
            }
    except httpx.TimeoutException:
        logger.error("[ImageGeneration] Generation timed out after 12s")
        return {
            "success": False,
            "error": "Image generation timed out. The model server might be busy, please retry.",
            "url": None
        }
    except Exception as e:
        logger.error(f"[ImageGeneration] Exception during generation: {e}")
        return {
            "success": False,
            "error": f"Failed to connect to image generation engine: {str(e)}",
            "url": None
        }
