
import asyncio
import logging
from typing import AsyncGenerator, Dict, List
from services.ai.gateway import AIGateway
from services.ai.providers.base import AIStreamChunk, BaseAIProvider

logging.basicConfig(level=logging.INFO)

class MockProvider(BaseAIProvider):
    def __init__(self, name, mode, model):
        self._provider_name = name
        self.mode = mode
        self._model = model

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def chat(self, messages, model, **kwargs):
        pass

    async def embeddings(self, text, model, **kwargs):
        pass

    async def image(self, prompt, model, **kwargs):
        pass

    async def stream(self, messages: List[Dict[str, str]], model: str, **kwargs) -> AsyncGenerator[AIStreamChunk, None]:
        if self.mode == "success":
            yield AIStreamChunk(content="Hello", is_done=False, model=model, provider=self.provider_name)
            yield AIStreamChunk(content=" World!", is_done=True, model=model, provider=self.provider_name)
        elif self.mode == "fail_immediate_429":
            raise Exception("429 Too Many Requests")
        elif self.mode == "fail_immediate_500":
            raise Exception("Internal Server Error")
        elif self.mode == "fail_midstream":
            yield AIStreamChunk(content="Half of ", is_done=False, model=model, provider=self.provider_name)
            raise Exception("Connection closed unexpectedly")

async def run_scenario(name, gateway):
    print(f"\n--- SCENARIO: {name} ---")
    messages = [{"role": "user", "content": "hi"}]
    stream = gateway.stream(messages)
    
    full_response = ""
    chunks = []
    
    try:
        async for chunk in stream:
            chunks.append(chunk)
            if chunk.content:
                full_response += chunk.content
    except Exception as e:
        print("UNCAUGHT EXCEPTION:", e)
        
    final_provider = chunks[-1].provider if chunks else "none"
    print("FINAL PROVIDER:", final_provider)
    print("FINAL RESPONSE:", full_response.strip())

async def main():
    # A. Primary provider success
    gw_a = AIGateway()
    gw_a.providers = [MockProvider("gemini", "success", "gemini"), MockProvider("groq", "success", "groq")]
    await run_scenario("A. Primary provider success", gw_a)

    # B. Primary provider failure before first chunk -> fallback succeeds
    gw_b = AIGateway()
    gw_b.providers = [MockProvider("gemini", "fail_immediate_429", "gemini"), MockProvider("groq", "success", "groq")]
    await run_scenario("B. Primary fails before first chunk -> fallback succeeds", gw_b)

    # C. Both providers fail -> graceful safe response
    gw_c = AIGateway()
    gw_c.providers = [MockProvider("gemini", "fail_immediate_429", "gemini"), MockProvider("groq", "fail_immediate_500", "groq")]
    await run_scenario("C. Both providers fail -> graceful safe response", gw_c)

    # D. Provider fails after partial output -> graceful interruption handling
    gw_d = AIGateway()
    gw_d.providers = [MockProvider("gemini", "fail_midstream", "gemini"), MockProvider("groq", "success", "groq")]
    await run_scenario("D. Primary fails mid-stream -> graceful interruption", gw_d)

if __name__ == "__main__":
    asyncio.run(main())

