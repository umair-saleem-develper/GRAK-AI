from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
from pydantic import BaseModel

class AIResponse(BaseModel):
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str
    provider: str

class AIStreamChunk(BaseModel):
    content: str
    is_done: bool = False
    # Usage metrics are only populated on the final chunk
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    fallback: bool = False

class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. gemini, groq, openrouter)"""
        pass
        
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AIResponse:
        """
        Synchronous chat response (used for background tasks like title generation).
        Messages format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        pass
        
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[AIStreamChunk, None]:
        """
        Stream chat response yielding AIStreamChunk.
        """
        pass
        
    @abstractmethod
    async def embeddings(self, text: str, model: str, **kwargs) -> List[float]:
        """Generate embeddings (stub)"""
        pass
        
    @abstractmethod
    async def image(self, prompt: str, model: str, **kwargs) -> str:
        """Generate image and return URL (stub)"""
        pass
