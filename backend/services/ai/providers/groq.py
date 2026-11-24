import os
from typing import AsyncGenerator, Dict, Any, List
from groq import AsyncGroq
from .base import BaseAIProvider, AIResponse, AIStreamChunk

class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")
        self.client = AsyncGroq(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "groq"

    async def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AIResponse:
        clean_msgs = [{"role": m["role"], "content": m.get("content", "")} for m in messages]
        completion = await self.client.chat.completions.create(
            model=model,
            messages=clean_msgs,
            stream=False,
            **kwargs
        )
        
        usage = completion.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        return AIResponse(
            content=completion.choices[0].message.content or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            provider=self.provider_name
        )

    async def stream(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[AIStreamChunk, None]:
        clean_msgs = [{"role": m["role"], "content": m.get("content", "")} for m in messages]
        stream = await self.client.chat.completions.create(
            model=model,
            messages=clean_msgs,
            stream=True,
            **kwargs
        )
        
        # Groq currently doesn't natively send usage in streaming chunks via OpenAI standard flawlessly in all models,
        # but if it does (stream_options={"include_usage": True}), we capture it.
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        async for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
            
            # If usage is provided in the final chunk (OpenAI style)
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0
                total_tokens = chunk.usage.total_tokens or 0

            yield AIStreamChunk(
                content=content,
                is_done=False,
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
