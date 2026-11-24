import os
from typing import AsyncGenerator, Dict, Any, List
from openai import AsyncOpenAI
from .base import BaseAIProvider, AIResponse, AIStreamChunk

class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0,
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AIResponse:
        # Some models on OpenRouter require 'HTTP-Referer' headers, but OpenAI client handles standard kwargs.
        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs
        )
        
        usage = completion.usage
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        return AIResponse(
            content=completion.choices[0].message.content or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            provider=self.provider_name
        )

    async def stream(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[AIStreamChunk, None]:
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs
        )

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        async for chunk in stream:
            content = ""
            if chunk.choices and len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content or ""
                
            if getattr(chunk, "usage", None):
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
