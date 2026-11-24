import asyncio
import os
import re
from dotenv import load_dotenv
from services.ai.providers.groq import GroqProvider

load_dotenv()

with open('routers/messages.py', 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(r'"content":\s*"""(.*?)"""', content, re.DOTALL)
if not matches:
    print('Could not find system prompt in messages.py')
    exit(1)
system_prompt = matches[0]

tests = {
    'B. Relativistic time dilation derivation': 'Why does time dilate at relativistic speeds? Keep it concise but accurate.',
    'C. Mars space elevator using Kevlar': 'If we built a space elevator on Mars today using Kevlar, how much payload could it lift per day?'
}

models_to_test = [
    'groq/compound-mini',
    'openai/gpt-oss-120b'
]

async def run_comparison():
    provider = GroqProvider()
    with open('compare_results.txt', 'w', encoding='utf-8') as f:
        f.write('=== EXACT SYSTEM PROMPT USED ===\n')
        f.write(system_prompt + '\n')
        f.write('================================\n\n')

        for test_name, user_msg in tests.items():
            f.write(f'\n\n==================================================\nTEST: {test_name}\nPROMPT: {user_msg}\n==================================================\n')
            for model in models_to_test:
                f.write(f'\n--- MODEL: {model} ---\n')
                messages = [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ]
                try:
                    full_resp = ''
                    async for chunk in provider.stream(messages=messages, model=model):
                        if chunk.content:
                            full_resp += chunk.content
                    f.write(full_resp.strip() + '\n')
                except Exception as e:
                    f.write(f'[ERROR] {e}\n')

if __name__ == "__main__":
    asyncio.run(run_comparison())
