import os
from typing import AsyncGenerator, Dict, Any, List
from .base import BaseAIProvider, AIResponse, AIStreamChunk

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ValueError("google-genai package is not installed")

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _convert_messages(self, messages: List[Dict[str, Any]]):
        # Extract system instructions separately for Gemini GenerateContentConfig and map user/model turns
        import base64
        import logging
        from google.genai import types
        logger = logging.getLogger(__name__)

        system_parts = []
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                sys_text = msg.get("content", "")
                if sys_text:
                    system_parts.append(sys_text)
                continue
            elif role == "assistant":
                role = "model"
            
            parts = []
            img_b64 = msg.get("image_base64")
            if img_b64:
                try:
                    mime_type = "image/png"
                    raw_b64 = img_b64
                    if "base64," in img_b64:
                        prefix, raw_b64 = img_b64.split("base64,", 1)
                        if "data:" in prefix and ";" in prefix:
                            mime_type = prefix.split("data:", 1)[1].split(";", 1)[0]
                    img_bytes = base64.b64decode(raw_b64)
                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))
                    logger.info(f"[GeminiProvider] Attached inline image part ({len(img_bytes)} bytes, {mime_type})")
                except Exception as img_err:
                    logger.warning(f"[GeminiProvider] Failed to parse inline image: {img_err}")

            text_content = msg.get("content", "")
            if text_content:
                parts.append(types.Part.from_text(text=text_content))
            elif not parts:
                parts.append(types.Part.from_text(text=""))

            gemini_messages.append({
                "role": role,
                "parts": parts
            })

        system_instruction = "\n\n".join(system_parts).strip() if system_parts else None
        if not gemini_messages:
            gemini_messages.append({"role": "user", "parts": [types.Part.from_text(text="")]})
        return gemini_messages, system_instruction

    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AIResponse:
        from google.genai import types
        contents, system_instruction = self._convert_messages(messages)
        config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        # Token usage from response.usage_metadata
        usage = response.usage_metadata
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        total_tokens = getattr(usage, "total_token_count", 0) if usage else 0

        return AIResponse(
            content=response.text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            provider=self.provider_name
        )

    async def stream(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[AIStreamChunk, None]:
        from google.genai import types
        contents, system_instruction = self._convert_messages(messages)
        config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
        
        response_stream = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        )
        
        async for chunk in response_stream:
            # Check if this is the final chunk with usage
            usage = chunk.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
            completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
            total_tokens = getattr(usage, "total_token_count", 0) if usage else 0
            
            yield AIStreamChunk(
                content=chunk.text or "",
                is_done=False, # We will yield a final empty chunk with is_done=True later
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=model,
                provider=self.provider_name
            )
            
        yield AIStreamChunk(content="", is_done=True, model=model, provider=self.provider_name)

    async def embeddings(self, text: str, model: str, **kwargs) -> List[float]:
        raise NotImplementedError()

    async def image(self, prompt: str, model: str, **kwargs) -> str:
        raise NotImplementedError()
