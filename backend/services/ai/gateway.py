import os
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from .providers.base import BaseAIProvider, AIResponse, AIStreamChunk
from .providers.gemini import GeminiProvider
from .providers.groq import GroqProvider
from .providers.openrouter import OpenRouterProvider
from .identity import apply_grak_identity

logger = logging.getLogger(__name__)

class AIGateway:
    """
    Lightweight AI orchestration layer managing fallback routing across providers.
    Provider Order: Gemini -> Groq
    """
    def __init__(self):
        self.providers: List[BaseAIProvider] = []
        
        # Initialize providers securely, skipping if keys are missing (but shouldn't be in production)
        try:
            self.providers.append(GeminiProvider())
        except Exception as e:
            logger.warning(f"Failed to init Gemini: {e}")

        try:
            self.providers.append(GroqProvider())
        except Exception as e:
            logger.warning(f"Failed to init Groq: {e}")
            
        # try:
        #     self.providers.append(OpenRouterProvider())
        # except Exception as e:
        #     logger.warning(f"Failed to init OpenRouter: {e}")

    def get_model_for_provider(self, provider_name: str) -> str:
        """Map generic fallback logic to specific models for each provider."""
        mapping = {
            "gemini": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview"),
            "groq": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            # "openrouter": "nvidia/nemotron-3.5-lightning:free"
        }
        return mapping.get(provider_name, "gemini-3.1-flash-lite-preview")

    async def chat(self, messages: List[Dict[str, str]], apply_identity: bool = True) -> AIResponse:
        """Execute a synchronous chat generation with automatic failover."""
        last_error = None
        prepared_messages = apply_grak_identity(messages) if apply_identity else messages
        
        for provider in self.providers:
            model = self.get_model_for_provider(provider.provider_name)
            logger.info(f"[AIGateway] Attempting chat via {provider.provider_name} ({model})")
            try:
                response = await provider.chat(messages=prepared_messages, model=model)
                return response
            except Exception as e:
                logger.error(f"[AIGateway] {provider.provider_name} failed: {e}")
                last_error = e
                continue
                
        # If we reach here, all providers failed
        raise RuntimeError(f"All AI providers failed. Last error: {last_error}")

    async def stream(self, messages: List[Dict[str, str]], apply_identity: bool = True) -> AsyncGenerator[AIStreamChunk, None]:
        """Execute a streaming chat generation with automatic failover at the connection level."""
        last_error = None
        has_failed_previously = False
        prepared_messages = apply_grak_identity(messages) if apply_identity else messages
        
        for idx, provider in enumerate(self.providers):
            model = self.get_model_for_provider(provider.provider_name)
            is_fallback = has_failed_previously or (idx > 0)
            logger.info(f"[AIGateway] Attempting stream via {provider.provider_name} ({model}) [fallback={is_fallback}]")
            content_yielded = False
            try:
                stream_gen = provider.stream(messages=prepared_messages, model=model)
                
                async for chunk in stream_gen:
                    if chunk.content:
                        content_yielded = True
                    chunk.provider = provider.provider_name
                    chunk.fallback = is_fallback
                    yield chunk
                    
                return # Successfully finished streaming, exit function
                
            except Exception as e:
                error_msg = str(e).lower()
                is_transient = any(k in error_msg for k in ["429", "timeout", "connection", "rate limit", "502", "503", "exhausted", "too many requests"])
                
                if is_transient:
                    logger.warning(f"[AIGateway] Transient failure with {provider.provider_name}: {e}")
                else:
                    logger.error(f"[AIGateway] Unexpected failure with {provider.provider_name}: {e}")
                
                last_error = e
                
                if content_yielded:
                    logger.warning(f"[AIGateway] {provider.provider_name} failed mid-stream after partial content. Yielding user-friendly interruption message.")
                    yield AIStreamChunk(
                        content="\n\n[Sorry, the response was interrupted. Please try again.]",
                        is_done=True,
                        model=model,
                        provider=provider.provider_name,
                        fallback=is_fallback
                    )
                    return
                # If no content yielded yet, record failure and continue to next provider (seamless failover)
                has_failed_previously = True
                continue
                
        # If all providers failed before yielding anything
        logger.warning(f"[AIGateway] All configured AI providers failed. Last error: {last_error}")
        
        # Categorize the error cleanly and safely
        err_lower = str(last_error).lower() if last_error else ""
        if any(k in err_lower for k in ["429", "rate limit", "exhausted", "too many requests", "quota"]):
            safe_error_msg = "The AI service is currently at capacity or quota limit. Please try again in a few moments."
        elif any(k in err_lower for k in ["401", "403", "api key", "unauthorized", "authentication"]):
            safe_error_msg = "AI provider authentication failed. Please check your API key configuration."
        elif any(k in err_lower for k in ["404", "model_not_found", "does not exist"]):
            safe_error_msg = "Configured AI model was not found. Please verify the model configuration."
        else:
            safe_error_msg = "Unable to connect to AI providers. Please check your connection and try again."
            
        yield AIStreamChunk(
            content=safe_error_msg,
            is_done=True,
            model="error",
            provider="none"
        )
