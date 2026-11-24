import os
import re

file_path = os.path.join(os.path.dirname(__file__), "services", "ai_engine.py")
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add validation and health check at the top after imports
header_addition = """
import pkg_resources

def validate_dependencies():
    try:
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            for req in requirements:
                pkg_resources.require(req)
    except Exception as e:
        raise RuntimeError(f"Startup dependency validation failed: {e}")

validate_dependencies()

AVAILABLE_PROVIDERS = {"Gemini": True, "OpenRouter": True, "Groq": True}

def check_provider_health():
    global AVAILABLE_PROVIDERS
    print("[Health Check] Starting provider health verification...")
    
    # Check Env Vars
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    if not GEMINI_API_KEY:
        print("[Health Check] Gemini missing API Key.")
        AVAILABLE_PROVIDERS["Gemini"] = False
    else:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
            if response.text:
                print("[Health Check] Gemini authenticated successfully.")
        except Exception as e:
            print(f"[Health Check] Gemini failed: {e}")
            AVAILABLE_PROVIDERS["Gemini"] = False

    if not OPENROUTER_API_KEY:
        print("[Health Check] OpenRouter missing API Key.")
        AVAILABLE_PROVIDERS["OpenRouter"] = False
    else:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "openrouter/free", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("[Health Check] OpenRouter authenticated successfully.")
            else:
                print(f"[Health Check] OpenRouter failed: {response.status_code}")
                AVAILABLE_PROVIDERS["OpenRouter"] = False
        except Exception as e:
            print(f"[Health Check] OpenRouter failed: {e}")
            AVAILABLE_PROVIDERS["OpenRouter"] = False

    if not GROQ_API_KEY:
        print("[Health Check] Groq missing API Key.")
        AVAILABLE_PROVIDERS["Groq"] = False
    else:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                print("[Health Check] Groq authenticated successfully.")
            else:
                print(f"[Health Check] Groq failed: {response.status_code}")
                AVAILABLE_PROVIDERS["Groq"] = False
        except Exception as e:
            print(f"[Health Check] Groq failed: {e}")
            AVAILABLE_PROVIDERS["Groq"] = False

    return AVAILABLE_PROVIDERS
"""

content = content.replace("load_dotenv(override=True)\n", "load_dotenv(override=True)\n" + header_addition)

# 2. Replace generate_text_stream entirely
new_generate_text_stream = """
def generate_text_stream(messages: list):
    \"\"\"Generator that yields text chunks for real-time streaming responses with robust fallbacks and logging.\"\"\"
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    api_messages, has_image = prepare_messages_for_vision(messages)

    # Detailed Debug Logging Info
    prompt_length = sum(len(m.get("content", "")) for m in messages)
    print(f"[DEBUG] Starting stream. Prompt length: {prompt_length} chars. Has Image: {has_image}")

    content_yielded = False

    def stream_provider(provider_name, url, headers, payload, is_openai_format=True):
        start_time = time.time()
        print(f"[DEBUG] Trying provider: {provider_name}")
        try:
            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            latency = time.time() - start_time
            print(f"[DEBUG] {provider_name} connected in {latency:.2f}s with status {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"Provider returned an error ({response.status_code})"
                if response.status_code in [401, 403]: error_msg = f"Auth Error ({response.status_code})"
                elif response.status_code == 408: error_msg = f"Request timed out ({response.status_code})"
                elif response.status_code == 429: error_msg = f"Rate Limit Exceeded ({response.status_code})"
                elif response.status_code >= 500: error_msg = f"Server Error ({response.status_code})"
                
                print(f"[ERROR] {provider_name} failed: {response.text}")
                return False, f"[{provider_name} Error: {error_msg}]"

            has_yielded_local = False
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        data = decoded[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get('error'):
                                err_text = chunk['error'].get('message', 'Unknown API Error')
                                return False, f"[{provider_name} API Error: {err_text}]"
                                
                            if is_openai_format:
                                choices = chunk.get('choices', [{}])
                                if choices:
                                    content = choices[0].get('delta', {}).get('content', '')
                                    if content:
                                        has_yielded_local = True
                                        yield content
                        except json.JSONDecodeError:
                            pass
                            
            if not has_yielded_local:
                print(f"[WARNING] {provider_name} returned an empty response stream.")
                return False, None
                
            return True, None
            
        except requests.exceptions.Timeout:
            print(f"[ERROR] {provider_name} timed out after 30s")
            return False, f"[{provider_name} Error: Request timed out (30s)]"
        except Exception as e:
            print(f"[ERROR] {provider_name} Exception: {e}")
            return False, f"[{provider_name} Error: {str(e)}]"

    # If vision task, prioritize OpenRouter (gpt-4o-mini)
    if has_image:
        if AVAILABLE_PROVIDERS.get("OpenRouter") and OPENROUTER_API_KEY:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "openai/gpt-4o-mini", "messages": api_messages, "temperature": 0.7, "max_tokens": 4000, "stream": True}
            for chunk in stream_provider("OpenRouter Vision", "https://openrouter.ai/api/v1/chat/completions", headers, payload):
                if isinstance(chunk, tuple):
                    success, err = chunk
                    if not success and err: 
                        print(f"[DEBUG] OpenRouter Vision Error: {err}")
                    break
                else:
                    content_yielded = True
                    yield chunk
            if not content_yielded:
                yield "\\n[Error: OPENROUTER_API_KEY missing or failed for image processing]"
            return
        else:
            yield "\\n[Error: OpenRouter unavailable for image processing]"
            return

    # Text Fallback Sequence: Gemini -> OpenRouter -> Groq
    # 1. Gemini
    if AVAILABLE_PROVIDERS.get("Gemini") and GEMINI_API_KEY:
        try:
            start_time = time.time()
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            gemini_messages = []
            for m in api_messages:
                role = "user" # default role
                # For basic generation, Gemini expects role "user" or "model". 
                # System prompt is passed to system_instruction usually, but we appended it.
                if m["role"] in ["assistant", "model"]: role = "model"
                gemini_messages.append(types.Content(role=role, parts=[types.Part.from_text(m["content"])]))
            
            print(f"[DEBUG] Trying provider: Gemini")
            response = client.models.generate_content_stream(
                model="gemini-1.5-flash",
                contents=gemini_messages
            )
            has_yielded_local = False
            for chunk in response:
                if chunk.text:
                    has_yielded_local = True
                    content_yielded = True
                    yield chunk.text
            latency = time.time() - start_time
            print(f"[DEBUG] Gemini finished in {latency:.2f}s")
            
            # If we yielded anything, do not fall back. Just return.
            if has_yielded_local:
                return
        except Exception as e:
            print(f"[ERROR] Gemini failed: {e}")
            if content_yielded:
                return # Abort cleanly instead of global error if stream died mid-way

    # 2. OpenRouter
    if AVAILABLE_PROVIDERS.get("OpenRouter") and OPENROUTER_API_KEY:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json", "HTTP-Referer": "http://localhost:3000", "X-Title": "OmniAI"}
        payload = {"model": "openrouter/free", "messages": api_messages, "temperature": 0.7, "max_tokens": 4000, "stream": True}
        for chunk in stream_provider("OpenRouter", "https://openrouter.ai/api/v1/chat/completions", headers, payload):
            if isinstance(chunk, tuple):
                success, err = chunk
                if err:
                    print(f"[DEBUG] OpenRouter Error: {err}")
                if content_yielded:
                    return
                break
            else:
                content_yielded = True
                yield chunk
        if content_yielded: return

    # 3. Groq
    if AVAILABLE_PROVIDERS.get("Groq") and GROQ_API_KEY:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant", "messages": api_messages, "temperature": 0.7, "max_tokens": 4000, "stream": True}
        for chunk in stream_provider("Groq", "https://api.groq.com/openai/v1/chat/completions", headers, payload):
            if isinstance(chunk, tuple):
                success, err = chunk
                if err:
                    print(f"[DEBUG] Groq Error: {err}")
                if content_yielded:
                    return
                break
            else:
                content_yielded = True
                yield chunk
        if content_yielded: return

    if not content_yielded:
        yield "\\n[Error: All AI providers failed or timed out.]"
"""

start_str = "import google.generativeai as genai"
end_str = "yield \"\\n[Error: All AI providers failed or timed out.]\""

idx_start = content.find(start_str)
idx_end = content.find(end_str) + len(end_str)

if idx_start != -1 and idx_end != -1:
    content = content[:idx_start] + new_generate_text_stream + content[idx_end:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to ai_engine.py successfully.")
