import os
import re

ai_engine_path = os.path.join(os.path.dirname(__file__), "services", "ai_engine.py")

with open(ai_engine_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace health check
new_health_check = """
AVAILABLE_PROVIDERS = {"Gemini": True, "OpenRouter": True, "Groq": True}
PROVIDER_DIAGNOSTICS = {
    "Gemini": {"status": "Pending", "network": "Pending", "sdk": "google-genai", "last_check": "Never"},
    "OpenRouter": {"status": "Pending", "network": "Pending", "sdk": "requests", "last_check": "Never"},
    "Groq": {"status": "Pending", "network": "Pending", "sdk": "requests", "last_check": "Never"}
}

def detect_gemini_credential_type(api_key):
    if not api_key: return "Missing"
    if api_key.startswith("AIzaSy"): return "Standard API Key"
    if api_key.startswith("ya29.") or api_key.count(".") > 1 or "-" in api_key: return "OAuth Token"
    return "Invalid/Unknown Format"

def check_provider_health():
    global AVAILABLE_PROVIDERS, PROVIDER_DIAGNOSTICS
    from datetime import datetime
    import requests
    print("[Health Check] Starting provider health verification...")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for k in PROVIDER_DIAGNOSTICS:
        PROVIDER_DIAGNOSTICS[k]["last_check"] = now_str
    
    # Gemini
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    cred_type = detect_gemini_credential_type(GEMINI_API_KEY)
    
    if cred_type != "Standard API Key":
        print(f"[Health Check] ❌ Gemini Error: Expected 'Standard API Key' (starts with AIzaSy), but detected '{cred_type}'. Please update .env.")
        AVAILABLE_PROVIDERS["Gemini"] = False
        PROVIDER_DIAGNOSTICS["Gemini"].update({"status": f"Invalid ({cred_type})", "network": "Offline"})
    else:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
            if response.text:
                print("[Health Check] ✅ Gemini authenticated successfully.")
                AVAILABLE_PROVIDERS["Gemini"] = True
                PROVIDER_DIAGNOSTICS["Gemini"].update({"status": "Authenticated", "network": "Online"})
        except Exception as e:
            print(f"[Health Check] ❌ Gemini failed: {e}")
            AVAILABLE_PROVIDERS["Gemini"] = False
            PROVIDER_DIAGNOSTICS["Gemini"].update({"status": "Failed", "network": "Error"})

    # OpenRouter
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    if not OPENROUTER_API_KEY:
        print("[Health Check] ❌ OpenRouter missing API Key.")
        AVAILABLE_PROVIDERS["OpenRouter"] = False
        PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Missing Key", "network": "Offline"})
    else:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "openrouter/free", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                print("[Health Check] ✅ OpenRouter authenticated successfully.")
                AVAILABLE_PROVIDERS["OpenRouter"] = True
                PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Authenticated", "network": "Online"})
            else:
                print(f"[Health Check] ❌ OpenRouter failed: {response.status_code}")
                AVAILABLE_PROVIDERS["OpenRouter"] = False
                PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": f"Auth Failed ({response.status_code})", "network": "Error"})
        except Exception as e:
            print(f"[Health Check] ❌ OpenRouter network error: {e}")
            AVAILABLE_PROVIDERS["OpenRouter"] = False
            PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Failed", "network": "Timeout/Error"})

    # Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    if not GROQ_API_KEY:
        print("[Health Check] ❌ Groq missing API Key.")
        AVAILABLE_PROVIDERS["Groq"] = False
        PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Missing Key", "network": "Offline"})
    else:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                print("[Health Check] ✅ Groq authenticated successfully.")
                AVAILABLE_PROVIDERS["Groq"] = True
                PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Authenticated", "network": "Online"})
            else:
                print(f"[Health Check] ❌ Groq failed: {response.status_code}")
                AVAILABLE_PROVIDERS["Groq"] = False
                PROVIDER_DIAGNOSTICS["Groq"].update({"status": f"Auth Failed ({response.status_code})", "network": "Error"})
        except Exception as e:
            print(f"[Health Check] ❌ Groq network error: {e}")
            AVAILABLE_PROVIDERS["Groq"] = False
            PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Failed", "network": "Timeout/Error"})

    return AVAILABLE_PROVIDERS
"""

start_hc = content.find("AVAILABLE_PROVIDERS =")
end_hc = content.find("return AVAILABLE_PROVIDERS") + len("return AVAILABLE_PROVIDERS")

if start_hc != -1 and end_hc != -1:
    content = content[:start_hc] + new_health_check + content[end_hc:]
    
# Now tenacity backoff
tenacity_import = "from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type\nimport requests\n"
content = content.replace("import requests\n", tenacity_import)

stream_provider_start = content.find("def stream_provider(provider_name")
stream_provider_end = content.find("if has_image:")

new_stream_provider = """
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
    def _do_request(url, headers, payload):
        resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        if resp.status_code == 429:
            raise requests.exceptions.RequestException(f"Rate limited (429)")
        return resp

    def stream_provider(provider_name, url, headers, payload, is_openai_format=True):
        start_time = time.time()
        print(f"[DEBUG] Trying provider: {provider_name}")
        try:
            response = _do_request(url, headers, payload)
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

    """

if stream_provider_start != -1 and stream_provider_end != -1:
    content = content[:stream_provider_start] + new_stream_provider + content[stream_provider_end:]
    
with open(ai_engine_path, "w", encoding="utf-8") as f:
    f.write(content)

# Update main.py for diagnostics
main_path = os.path.join(os.path.dirname(__file__), "main.py")
with open(main_path, "r", encoding="utf-8") as f:
    main_content = f.read()
    
if "from services.ai_engine import PROVIDER_DIAGNOSTICS" not in main_content:
    main_content = main_content.replace(
        "from services.ai_engine import generate_text",
        "from services.ai_engine import generate_text, generate_text_stream, hybrid_web_research, PROVIDER_DIAGNOSTICS, check_provider_health"
    )
    
    diag_route = """
@app.get("/api/diagnostics")
def get_diagnostics():
    return PROVIDER_DIAGNOSTICS

@app.post("/api/diagnostics/refresh")
def refresh_diagnostics():
    check_provider_health()
    return PROVIDER_DIAGNOSTICS
"""
    main_content = main_content.replace('def read_root():', diag_route + '\n@app.get("/")\ndef read_root():')
    
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main_content)

print("Backend patched successfully")
