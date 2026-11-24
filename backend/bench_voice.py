import time, os, requests
from dotenv import load_dotenv
load_dotenv(override=True)
groq_key = os.environ.get('GROQ_API_KEY')
openrouter_key = os.environ.get('OPENROUTER_API_KEY')

def get_voice_response(messages):
    voice_system = 'You are Grak, a friendly voice assistant. Respond in 1 to 2 short conversational sentences. No markdown.'
    payload_msgs = [{'role': 'system', 'content': voice_system}] + messages[-6:]
    
    # 1. Try Groq
    t0 = time.time()
    try:
        res = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {groq_key}', 'Content-Type': 'application/json'},
            json={'model': 'qwen/qwen3.8-27b', 'messages': payload_msgs, 'max_tokens': 70, 'temperature': 0.6},
            timeout=3.5
        )
        if res.status_code == 200:
            text = res.json()['choices'][0]['message']['content'].strip()
            text = text.replace('**', '').replace('*', '').replace('`', '').strip()
            return text, f'Groq qwen ({time.time()-t0:.2f}s)'
    except Exception as e:
        pass
        
    # 2. Try OpenRouter
    t1 = time.time()
    try:
        res = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {openrouter_key}', 'Content-Type': 'application/json'},
            json={'model': 'openrouter/free', 'messages': payload_msgs, 'max_tokens': 120, 'temperature': 0.6},
            timeout=4.0
        )
        if res.status_code == 200:
            msg = res.json()['choices'][0]['message']
            text = msg.get('content') or msg.get('reasoning') or ''
            text = text.replace('**', '').replace('*', '').replace('`', '').strip()
            if text:
                return text, f'OpenRouter ({time.time()-t1:.2f}s)'
    except Exception as e:
        pass
        
    return 'I hear you loud and clear. How can I help you?', 'Fallback (0.01s)'

for prompt in ['Hello Grak!', 'What is the capital of France?', 'Count to three.']:
    t = time.time()
    ans, prov = get_voice_response([{'role': 'user', 'content': prompt}])
    print(f'Prompt: "{prompt}" -> Answer: "{ans}" | Provider: {prov} | Total: {time.time()-t:.2f}s')
