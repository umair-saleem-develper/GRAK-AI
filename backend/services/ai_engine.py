import os
import json
import time
import uuid
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import requests
from requests.adapters import HTTPAdapter
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# Global Session with HTTPAdapter for connection pooling
http_session = requests.Session()
adapter = HTTPAdapter(pool_connections=20, pool_maxsize=100)
http_session.mount('http://', adapter)
http_session.mount('https://', adapter)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://omniai.vercel.app")
import importlib.metadata

def validate_dependencies():
    try:
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            for req in requirements:
                parts = req.split("==")
                pkg = parts[0].split(">=")[0].split("<=")[0].strip()
                version = parts[1] if len(parts) > 1 else None
                try:
                    pkg_name = pkg.split('[')[0] # handle extras like psycopg[binary]
                    installed_version = importlib.metadata.version(pkg_name)
                    if version and installed_version != version:
                        print(f"[Warning] {pkg} version mismatch. Expected {version}, got {installed_version}")
                except importlib.metadata.PackageNotFoundError:
                    print(f"[Warning] Missing required package: {pkg}")
    except Exception as e:
        print(f"[Warning] Startup dependency validation failed: {e}")

validate_dependencies()


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
    """Validates connectivity and authentication for all enabled providers."""
    global AVAILABLE_PROVIDERS, PROVIDER_DIAGNOSTICS
    from datetime import datetime
    from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
    
    health = {
        "Gemini": False,
        "OpenRouter": False,
        "Groq": False
    }
    
    # Check Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            from google.oauth2.credentials import Credentials
            
            cred_type = detect_gemini_credential_type(gemini_key)
            if cred_type == "OAuth Token":
                creds = Credentials(token=gemini_key)
                client = genai.Client(credentials=creds)
            elif cred_type == "Standard API Key":
                client = genai.Client(api_key=gemini_key)
            else:
                raise Exception(f"Expected 'Standard API Key' or 'OAuth Token', but detected '{cred_type}'. Please update .env.")
            
            try:
                client.models.generate_content(model="gemini-1.5-flash", contents="health check")
                health["Gemini"] = True
                PROVIDER_DIAGNOSTICS["Gemini"]["status"] = "Healthy"
            except Exception as e:
                # Mock success only if an explicit test mock key env var matches
                mock_key = os.getenv("GEMINI_MOCK_KEY")
                if mock_key and gemini_key == mock_key:
                    health["Gemini"] = True
                    PROVIDER_DIAGNOSTICS["Gemini"]["status"] = "Healthy"
                else:
                    raise e
            PROVIDER_DIAGNOSTICS["Gemini"]["last_check"] = time.time()
        except Exception as e:
            print(f"Gemini Health Check Failed: {e}")
            PROVIDER_DIAGNOSTICS["Gemini"]["status"] = f"Failed: {str(e)}"
            PROVIDER_DIAGNOSTICS["Gemini"]["last_check"] = time.time()

    # End of Gemini Check
    
    import requests
    # Check OpenRouter
    print("[Health Check] Starting provider health verification...")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for k in PROVIDER_DIAGNOSTICS:
        PROVIDER_DIAGNOSTICS[k]["last_check"] = now_str
    
    # End of old Gemini block
    # OpenRouter
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    if not OPENROUTER_API_KEY:
        print("[Health Check] FAILED: OpenRouter missing API Key.")
        AVAILABLE_PROVIDERS["OpenRouter"] = False
        PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Missing Key", "network": "Offline"})
    else:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "openrouter/free", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = None
            for _ in range(3):
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
                if response.status_code != 429: break
                time.sleep(2)
            if response.status_code == 200:
                print("[Health Check] SUCCESS: OpenRouter authenticated successfully.")
                AVAILABLE_PROVIDERS["OpenRouter"] = True
                PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Authenticated", "network": "Online"})
            else:
                print(f"[Health Check] FAILED: OpenRouter failed: {response.status_code}")
                AVAILABLE_PROVIDERS["OpenRouter"] = False
                PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": f"Auth Failed ({response.status_code})", "network": "Error"})
        except Exception as e:
            print(f"[Health Check] FAILED: OpenRouter network error: {e}")
            AVAILABLE_PROVIDERS["OpenRouter"] = False
            PROVIDER_DIAGNOSTICS["OpenRouter"].update({"status": "Failed", "network": "Timeout/Error"})

    # Groq
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    if not GROQ_API_KEY:
        print("[Health Check] FAILED: Groq missing API Key.")
        AVAILABLE_PROVIDERS["Groq"] = False
        PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Missing Key", "network": "Offline"})
    else:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5}
            response = None
            for _ in range(3):
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
                if response.status_code != 429: break
                time.sleep(2)
            if response.status_code == 200:
                print("[Health Check] SUCCESS: Groq authenticated successfully.")
                AVAILABLE_PROVIDERS["Groq"] = True
                PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Authenticated", "network": "Online"})
            else:
                print(f"[Health Check] FAILED: Groq failed: {response.status_code}")
                AVAILABLE_PROVIDERS["Groq"] = False
                PROVIDER_DIAGNOSTICS["Groq"].update({"status": f"Auth Failed ({response.status_code})", "network": "Error"})
        except Exception as e:
            print(f"[Health Check] FAILED: Groq network error: {e}")
            AVAILABLE_PROVIDERS["Groq"] = False
            PROVIDER_DIAGNOSTICS["Groq"].update({"status": "Failed", "network": "Timeout/Error"})

    return AVAILABLE_PROVIDERS


SYSTEM_PROMPT = """You are Grak AI, a professional AI assistant built to provide trustworthy, accurate, logical, and helpful answers.

Your highest priority is correctness, not speed.

A. Language & NLP: You MUST reply in the same language the user uses. If the user asks in Roman Urdu/Hindi, you MUST reply entirely in natural Roman Urdu/Hindi. Keep English only for technical terms, code, or math.
B. Mirror Length: Adapt your response length to the user's prompt. Provide highly detailed and step-by-step explanations when asked to solve math or programming problems.
C. Formatting: Use clear formatting (headings, bullet points, bold text). Do not use raw Markdown table syntax unless explicitly requested.
D. LaTeX Math: You MUST use `$$` for block math equations and single `$` for inline math. Do NOT use `\\[` or `\\(` for math formatting.
E. Image Analysis: You are strictly authorized to analyze and identify people, founders, and public figures in images. DO NOT give safety refusals for normal queries.

GENERAL BEHAVIOR
- Always understand the user's real intent before answering.
- Read the entire prompt carefully.
- Never ignore any requirement.
- If the request contains multiple tasks, complete every task.
- If information is missing, ask a clarifying question instead of guessing.
- Never fabricate facts, code, citations, APIs, libraries, or research.
- If uncertain, clearly say what you know and what you are unsure about.
- Never pretend to know something you do not.

REASONING
Before generating an answer, internally:
1. Understand the request.
2. Break complex tasks into smaller parts.
3. Think through the solution.
4. Verify the logic.
5. Then generate the final answer.
Do not expose internal reasoning.

QUALITY STANDARDS
Every answer must be: Accurate, Complete, Well organized, Easy to understand, Factually correct, Logically consistent, Free of contradictions.
Your response should look similar in quality and readability to ChatGPT, Claude, or Gemini.

PROGRAMMING
When writing code:
- Produce clean, production-quality code.
- Follow language best practices.
- Use meaningful names.
- Use proper formatting and indentation.
- Avoid duplicate code.
- Prefer safe and modern programming practices.
- Ensure the code is syntactically correct.
- Check for common compile-time and logical mistakes before returning it.
- If you detect a mistake, correct it before responding.
- Never claim code is executable unless you have verified it as carefully as possible.

MATHEMATICS
- Solve step by step.
- Verify calculations before responding.
- Do not skip important steps.

SQL
- Ensure valid syntax.
- Respect normalization.
- Use proper primary keys, foreign keys, constraints, and indexes when appropriate.

RESEARCH
- Separate facts from opinions.
- Distinguish verified information from assumptions.
- If recent information is required, use available search tools when possible.
- Never invent references.

FORMATTING & WRITING
- Make responses visually clean and easy to read.
- Automatically choose the best format: Headings, Bullet points, Numbered lists, Short paragraphs, or Tables (only when they render correctly).
- Never output raw Markdown table syntax unless the user explicitly requests Markdown.
- Add proper spacing between sections.
- Avoid large walls of text.
- Highlight important terms using **bold** formatting.
- For summaries: Start with a one-line overview, use clear section headings, and end with a short conclusion or key takeaway.
- Match the user's requested tone.
- Keep answers clear and natural.
- Avoid unnecessary repetition.
- Never expose broken Markdown, raw HTML, or malformed formatting.
- Validate that formatting renders correctly before sending. If a table will not render properly, automatically convert it into a bullet list.

ERROR HANDLING
If a request cannot be completed: Explain why. Offer the closest correct alternative. Never generate misleading information.

SELF-VERIFICATION
Before sending every response, internally verify:
- Did I answer every part of the user's request?
- Is the information logically consistent?
- Does the code contain obvious syntax or logic errors?
- Are calculations correct?
- Is the answer complete?
- Did I avoid unsupported claims?
If any issue is found, fix it before responding.

CORE PRINCIPLES
Correctness over speed.
Evidence over assumptions.
Honesty over hallucination.
Quality over quantity.
Helpfulness without misleading the user.

Your goal is to behave like a senior expert while remaining transparent, accurate, and reliable."""

def prepare_messages_for_vision(messages: list):
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    last_image_idx = -1
    for idx, m in enumerate(messages):
        if m.get("image_base64") or m.get("images"):
            last_image_idx = idx

    has_image = (last_image_idx != -1)
            
    for idx, m in enumerate(messages):
        images = m.get("images") or []
        # Ensure we have a copy so we don't modify the original message dict
        images = list(images)
        
        if m.get("image_base64"):
            images.append(m.get("image_base64"))
            
        if len(images) > 0:
            if idx == last_image_idx:
                content_arr = [{"type": "text", "text": m["content"]}]
                for img_b64 in images:
                    content_arr.append({
                        "type": "image_url",
                        "image_url": { "url": f"data:image/jpeg;base64,{img_b64}" }
                    })
                api_messages.append({"role": m["role"], "content": content_arr})
            else:
                api_messages.append({"role": m["role"], "content": f"[User attached {len(images)} images here previously] {m['content']}"})
        else:
            api_messages.append({"role": m["role"], "content": m["content"]})
            
    return api_messages, has_image


def generate_text(messages: list) -> str:
    """Generates text using Groq (primary, fastest) with OpenRouter as fallback."""
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    api_messages, has_image = prepare_messages_for_vision(messages)

    # If it's a vision task, force OpenRouter with gpt-4o-mini
    if has_image:
        if not OPENROUTER_API_KEY:
            return "Please add OPENROUTER_API_KEY to your .env file to process images."
        try:
            openai_messages = []
            for m in api_messages:
                r = m["role"]
                if r == "model": r = "assistant"
                openai_messages.append({"role": r, "content": m["content"]})
            print(f"[DEBUG] Normalized OpenRouter payload roles: {[m['role'] for m in openai_messages]}")

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": FRONTEND_URL,
                "X-Title": "OmniAI"
            }
            payload = {
                "model": "openai/gpt-4o-mini",
                "messages": openai_messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"OpenRouter Vision Error: {response.status_code} - {response.text}")
            return f"Error processing image: {response.status_code}"
        except Exception as e:
            print(f"OpenRouter Vision Error: {e}")
            return f"Error processing image: {str(e)}"

    # 1. PRIMARY: Groq for text
    if GROQ_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"Groq API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Groq Request Error: {e}")

    # 2. FALLBACK: OpenRouter for text
    if OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": FRONTEND_URL,
                "X-Title": "OmniAI"
            }
            payload = {
                "model": "openrouter/free",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"OpenRouter API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"OpenRouter Request Error: {e}")

    return "Sorry, all AI providers are temporarily unavailable. Please try again in a moment."



def generate_text_stream(messages: list):
    """Generator that yields text chunks for real-time streaming responses with robust fallbacks and logging."""
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    api_messages, has_image = prepare_messages_for_vision(messages)

    # Detailed Debug Logging Info
    prompt_length = sum(len(m.get("content", "")) for m in messages)
    print(f"[DEBUG] Starting stream. Prompt length: {prompt_length} chars. Has Image: {has_image}")

    content_yielded = False

    
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

    if has_image:
        if not OPENROUTER_API_KEY:
            return "Please add OPENROUTER_API_KEY to your .env file to process images."
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": FRONTEND_URL,
                "X-Title": "OmniAI"
            }
            payload = {
                "model": "openai/gpt-4o-mini",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"OpenRouter Vision Error: {response.status_code} - {response.text}")
            return f"Error processing image: {response.status_code}"
        except Exception as e:
            print(f"OpenRouter Vision Error: {e}")
            return f"Error processing image: {str(e)}"

    # 1. PRIMARY: Groq for text
    if GROQ_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"Groq API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Groq Request Error: {e}")

    # 2. FALLBACK: OpenRouter for text
    if OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": FRONTEND_URL,
                "X-Title": "OmniAI"
            }
            payload = {
                "model": "openrouter/free",
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            print(f"OpenRouter API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"OpenRouter Request Error: {e}")

    return "Sorry, all AI providers are temporarily unavailable. Please try again in a moment."



def generate_text_stream(messages: list):
    """Generator that yields text chunks for real-time streaming responses with robust fallbacks and logging."""
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    api_messages, has_image = prepare_messages_for_vision(messages)

    # Detailed Debug Logging Info
    req_id = str(uuid.uuid4())[:8]
    prompt_length = sum(len(m.get("content", "")) for m in messages)
    print(f"[DEBUG] [{req_id}] Starting stream. Prompt length: {prompt_length} chars. Has Image: {has_image}")

    content_yielded = False

    def stream_provider(provider_name, url, headers, payload, is_openai_format=True):
        start_time = time.time()
        print(f"[DEBUG] [{req_id}] Trying provider: {provider_name}")
        try:
            with http_session.post(url, headers=headers, json=payload, stream=True, timeout=(10, 30)) as response:
                latency = time.time() - start_time
                print(f"[DEBUG] [{req_id}] {provider_name} connected in {latency:.2f}s with status {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"Provider returned an error ({response.status_code})"
                    if response.status_code in [401, 403]: error_msg = f"Auth Error ({response.status_code})"
                    elif response.status_code == 408: error_msg = f"Request timed out ({response.status_code})"
                    elif response.status_code == 429: error_msg = f"Rate Limit Exceeded ({response.status_code})"
                    elif response.status_code >= 500: error_msg = f"Server Error ({response.status_code})"
                    
                    print(f"[ERROR] [{req_id}] {provider_name} failed: {response.text}")
                    yield False, f"[{provider_name} Error: {error_msg}]"
                    return

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
                                    yield False, f"[{provider_name} API Error: {err_text}]"
                                    return
                                    
                                if is_openai_format:
                                    choices = chunk.get('choices', [{}])
                                    if choices:
                                        content = choices[0].get('delta', {}).get('content', '')
                                        if content:
                                            has_yielded_local = True
                                            yield True, content
                            except json.JSONDecodeError:
                                pass
                                
                if not has_yielded_local:
                    print(f"[WARNING] [{req_id}] {provider_name} returned an empty response stream.")
                    yield False, f"[{provider_name} Error: Empty response stream]"
                    return
                
        except requests.exceptions.Timeout:
            print(f"[ERROR] [{req_id}] {provider_name} timed out after 30s")
            yield False, f"[{provider_name} Error: Request timed out (30s)]"
            return
        except Exception as e:
            print(f"[ERROR] [{req_id}] {provider_name} Exception: {e}")
            yield False, f"[{provider_name} Error: {str(e)}]"
            return

    # If vision task, prioritize OpenRouter (gpt-4o-mini)
    if has_image:
        if AVAILABLE_PROVIDERS.get("OpenRouter") and OPENROUTER_API_KEY:
            openai_messages = []
            for m in api_messages:
                r = m["role"]
                if r == "model": r = "assistant"
                openai_messages.append({"role": r, "content": m["content"]})
            print(f"[DEBUG] [{req_id}] Normalized OpenRouter payload roles: {[m['role'] for m in openai_messages]}")

            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "openai/gpt-4o-mini", "messages": openai_messages, "temperature": 0.7, "max_tokens": 1024, "stream": True}
            for chunk in stream_provider("OpenRouter Vision", "https://openrouter.ai/api/v1/chat/completions", headers, payload):
                success, val = chunk if isinstance(chunk, tuple) else (True, chunk)
                if not success:
                    print(f"[DEBUG] [{req_id}] OpenRouter Vision Error: {val}")
                    if content_yielded:
                        return
                    break
                else:
                    content_yielded = True
                    yield val
            if not content_yielded:
                yield "\n[Error: OPENROUTER_API_KEY missing or failed for image processing]"
            return
        else:
            yield "\n[Error: OpenRouter unavailable for image processing]"
            return

    # Text Fallback Sequence: Gemini -> OpenRouter -> Groq
    
    # 1. Gemini
    if AVAILABLE_PROVIDERS.get("Gemini") and GEMINI_API_KEY:
        try:
            start_time = time.time()
            from google import genai
            from google.genai import types
            from google.oauth2.credentials import Credentials
            
            cred_type = detect_gemini_credential_type(GEMINI_API_KEY)
            if cred_type == "OAuth Token":
                creds = Credentials(token=GEMINI_API_KEY)
                client = genai.Client(credentials=creds)
            else:
                client = genai.Client(api_key=GEMINI_API_KEY)
            
            gemini_messages = []
            for m in api_messages:
                role = "user" # default role
                if m["role"] in ["assistant", "model"]: role = "model"
                elif m["role"] == "system": role = "user" # Gemini doesn't support system in the array the same way sometimes, but we pass user
                gemini_messages.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
            print(f"[DEBUG] [{req_id}] Normalized Gemini payload roles: {[m.role for m in gemini_messages]}")
            
            print(f"[DEBUG] [{req_id}] Trying provider: Gemini")
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
            print(f"[DEBUG] [{req_id}] Gemini finished in {latency:.2f}s")
            
            if has_yielded_local:
                return
        except Exception as e:
            print(f"[ERROR] [{req_id}] Gemini failed: {e}")
            if content_yielded:
                return # Abort cleanly instead of global error if stream died mid-way

    # 2. OpenRouter (With Retries)
    if AVAILABLE_PROVIDERS.get("OpenRouter") and OPENROUTER_API_KEY:
        openai_messages = []
        for m in api_messages:
            r = m["role"]
            if r == "model": r = "assistant"
            openai_messages.append({"role": r, "content": m["content"]})
        print(f"[DEBUG] [{req_id}] Normalized OpenRouter payload roles: {[m['role'] for m in openai_messages]}")

        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json", "HTTP-Referer": FRONTEND_URL, "X-Title": "OmniAI"}
        payload = {"model": "openrouter/free", "messages": openai_messages, "temperature": 0.7, "max_tokens": 1024, "stream": True}
        
        for attempt in range(2):
            err_msg = None
            for chunk in stream_provider("OpenRouter", "https://openrouter.ai/api/v1/chat/completions", headers, payload):
                success, val = chunk if isinstance(chunk, tuple) else (True, chunk)
                if not success:
                    err_msg = val
                    print(f"[DEBUG] [{req_id}] OpenRouter Error (Attempt {attempt+1}): {err_msg}")
                    if content_yielded:
                        return
                    break
                else:
                    content_yielded = True
                    yield val
            
            if content_yielded: return
            if attempt < 1:
                time.sleep(1) # Backoff before retry
        
    # 3. Groq (With Retries)
    if AVAILABLE_PROVIDERS.get("Groq") and GROQ_API_KEY:
        openai_messages = []
        for m in api_messages:
            r = m["role"]
            if r == "model": r = "assistant"
            openai_messages.append({"role": r, "content": m["content"]})
        print(f"[DEBUG] [{req_id}] Normalized Groq payload roles: {[m['role'] for m in openai_messages]}")

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "llama-3.1-8b-instant", "messages": openai_messages, "temperature": 0.7, "max_tokens": 1024, "stream": True}
        
        for attempt in range(2):
            err_msg = None
            for chunk in stream_provider("Groq", "https://api.groq.com/openai/v1/chat/completions", headers, payload):
                success, val = chunk if isinstance(chunk, tuple) else (True, chunk)
                if not success:
                    err_msg = val
                    print(f"[DEBUG] [{req_id}] Groq Error (Attempt {attempt+1}): {err_msg}")
                    if content_yielded:
                        return
                    break
                else:
                    content_yielded = True
                    yield val
            
            if content_yielded: return
            if attempt < 1:
                time.sleep(1) # Backoff before retry

    if not content_yielded:
        print(f"[ERROR] [{req_id}] All AI providers failed or timed out.")
        yield "\n[Error: All AI providers failed or timed out.]"


def optimize_search_query(query: str) -> str:
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        return query
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": FRONTEND_URL,
            "X-Title": "OmniAI"
        }
        prompt = f"Convert this complex query into highly optimized, specific search engine keywords (not full sentences). Break it down to focus on core entities (e.g., instead of 'what is pricing', use 'pricing official docs'). IMPORTANT: If the query is in Roman Urdu, always append 'in Pakistan' to the search string. If the query is about a fruit (like 'seb' or 'apple'), explicitly add the word 'fruit'. MUST preserve the specific context of the query (e.g., if they ask about teaching in an academy, include 'academy teacher'). Return ONLY the search string without quotes. Query: {query}"
        payload = {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 50
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            opt = response.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
            if len(opt) > 2:
                return opt
        else:
            print(f"Optimize Query Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Optimize Query Exception: {e}")
    return query

def hybrid_web_research(query: str) -> str:
    """Performs web research using Tavily (primary) or DuckDuckGo (fallback) and summarizes via OpenRouter."""
    # Strict Query Extraction: Parse JSON or text chat history if provided
    try:
        import json
        parsed_query = json.loads(query)
        if isinstance(parsed_query, list):
            user_messages = [msg.get("content", "") for msg in parsed_query if isinstance(msg, dict) and msg.get("role") == "user"]
            if user_messages:
                query = user_messages[-1]
    except Exception:
        # Fallback for plain text chat histories (e.g. "User: hi \n AI: hello \n User: search this")
        if "User:" in query:
            parts = query.split("User:")
            last_part = parts[-1].split("AI:")[0].strip()
            if last_part:
                query = last_part

    def is_english(text):
        english_words = {"what", "is", "the", "how", "why", "when", "where", "who", "which", "are", "do", "does", "did", "can", "could", "would", "should", "and", "or", "but", "if", "in", "on", "at", "to", "for", "with", "about", "from", "by", "this", "that", "these", "those", "a", "an"}
        words = set(text.lower().split())
        return len(words.intersection(english_words)) >= 2 or (len(words) > 0 and list(words)[0] in english_words)
        
    error_msg = "The research engine is currently busy, please try again." if is_english(query) else "Filhal mera research engine busy hai, kripya dobara koshish karein."

    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    search_context = ""
    
    # Optimize query for search engines (fixes Roman Urdu search issues)
    optimized_query = optimize_search_query(query)
    print(f"Original Query: {query}")
    print(f"Optimized Search Query: {optimized_query}")
    
    try:
        if tavily_api_key:
            payload = {
                "api_key": tavily_api_key,
                "query": optimized_query,
                "search_depth": "basic",
                "max_results": 5
            }
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    response.raise_for_status()
                    results = response.json().get("results", [])
                    for res in results:
                        search_context += f"Source: {res.get('url')}\nContent: {res.get('content')}\n\n"
                    break
                except Exception as attempt_e:
                    print(f"Tavily Attempt {attempt + 1} failed: {attempt_e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        print(f"Search tool failed due to Tavily Exception: {attempt_e}")
                        raise attempt_e
        else:
            raise Exception("Tavily API key missing")
    except Exception as e:
        print(f"Tavily Error: {e}")
        try:
            from duckduckgo_search import DDGS
            results = DDGS().text(optimized_query, max_results=3)
            if results:
                for res in results:
                    search_context += f"Source: {res.get('href')}\nContent: {res.get('body')}\n\n"
            else:
                raise Exception("DDGS returned empty list")
        except Exception as ddg_e:
            print(f"Search tool failed due to DDGS Exception: {ddg_e}")
            search_context = "[SEARCH_FAILED_NETWORK_BUSY]"

    if not search_context.strip():
        search_context = "[SEARCH_FAILED_NETWORK_BUSY]"

    # Now use OpenRouter (gpt-4o-mini) to summarize
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        return "Search successful, but OPENROUTER_API_KEY is missing to summarize the results."

    system_prompt = (
        "GRAK AI MASTER SYSTEM DIRECTIVE:\n"
        "You are Grak AI, a highly intelligent, professional, and empathetic AI assistant. Your goal is to provide world-class, user-friendly responses similar to top-tier AI models. Always adopt a helpful and clear tone. Today is June 30, 2026. You will be provided with live web search results. You MUST answer the user's query STRICTLY using ONLY the provided search results.\n\n"
        "CORE DIRECTIVES:\n"
        "1. PREMIUM FORMATTING: Always use Rich Markdown. Break long text into short paragraphs. Use bullet points and bold text for readability. NEVER use Markdown tables (|---|); summarize data using a clean '📊 Data Summary' list format instead.\n"
        "2. ZERO HALLUCINATION & CITATIONS: If asked for facts, dates, or prices, you must search the web. Every claim must have a valid [Source: URL]. NEVER invent fake companies, deadlines, or data to make your answer look longer.\n"
        "3. SMART EMPTY STATES: If web search returns no data, do not give a robotic 1-line answer. Politely explain what you searched for, confirm it wasn't found, and suggest 2-3 real alternatives the user can ask about.\n"
        "4. OFFLINE FAILSAFE: If your web search tool fails or is disabled, and the user asks for real-time information, DO NOT guess using your base model. You must strictly output: '⚠️ Web Search Disabled: I cannot provide live updates or verify recent announcements right now.'\n\n"
        "1. Language Logic (Strictly Contextual):\n"
        "You must ALWAYS mirror the user's language. If the user types in English, you reply in fluent English. If the user types in Roman English/Urdu, you reply in Roman English/Urdu. NEVER translate or switch languages on your own.\n\n"
        "2. Formatting & Detail Rule (CRITICAL FORMATTING RULE & NO SPECIAL CHARACTER FORMATTING):\n"
        "Whenever the user asks for data, comparisons, or real-time updates, you MUST structure your response using Rich Markdown in this exact order:\n"
        "- Intro: Start with a 1-sentence intro mentioning the current date/context.\n"
        "- Subheadings for Context: If the user asks a multi-part question, use a bold markdown subheading (###) to answer that specific part clearly.\n"
        "- Bullets: The exact fetched data points formatted clearly. You MUST use relevant emojis at the start of these bullet points (e.g., ⛽ for fuel, 💻 for tech, 📈 for finance). Provide the [Source: Link] at the end of each bullet point.\n"
        "- Structured Lists (NO TABLES ALLOWED): Do NOT use Markdown Tables anymore, as the frontend parser breaks them. Whenever you need to summarize or compare data at the end of your response, you MUST use a clean 'Structured List' block exactly like this template:\n\n📊 Data Summary:\n- **Petrol:** 299.50 PKR\n- **Diesel:** 311.47 PKR\n\nUse bold text for labels and keep it strictly in bullet points. Never generate |---|---| table syntax.\n"
        "- Closing: Instead of a generic closing question, end with 'If you'd like, I can also provide:' (or its exact language equivalent) followed by a bulleted list of 2 specific, highly relevant follow-up topics the user can ask about next.\n"
        "Do not invent data, but DO use conversational language to present the facts professionally. NEVER use the $ sign, £, €, or any other currency symbol. If a price is thirty dollars, you MUST write '30 USD'. Replace all symbols with their 3-letter alphabetical codes (USD, PKR, EUR, etc.). Never use nested asterisks or LaTeX.\n\n"
        "3. CRITICAL OFFLINE / NO-SEARCH PROTOCOL:\n"
        "If the search context contains the exact string '[SEARCH_FAILED_NETWORK_BUSY]', it means your web search tool is disabled, restricted, or failed.\n"
        "In this state, if the user asks for real-time updates, news, or specific dates (e.g., June 2026 events), you MUST NOT use your internal base model to guess or generate data.\n"
        "You must strictly output ONLY this exact error message (or its translation in the user's language):\n"
        "⚠️ Web Search Disabled: I cannot provide live updates or verify recent announcements because my search capabilities are currently turned off. Please enable web search to get accurate data.\n"
        "Absolutely ZERO generation of companies, deadlines, or events when offline.\n\n"
        "4. Search & Accuracy Rule (Conversational Depth & Strict Fallback):\n"
        "You MUST mimic a highly detailed, conversational structure. Never give 1-2 line blunt answers. Provide explanatory paragraphs.\n"
        "When explaining findings, use formatting like: 'Based on the information I could verify:' (in the user's language) followed by detailed, descriptive bullet points explaining WHAT you found and WHY.\n"
        "IF the search returns valid data, you MUST provide the detailed answer and you MUST NOT append any fallback error messages like 'Mujhe iski maloomat nahi mili' at the end.\n"
        "CRITICAL UX RULE FOR EMPTY SEARCH RESULTS: If the result is completely empty or irrelevant, you MUST NOT give a short robotic response. You must structure your 'No Data' response exactly like this:\n"
        "- Contextual Intro: Start by explaining exactly what you searched for and confirm that no official verified results were found for the requested timeframe.\n"
        "- Breakdown (Bullet points): List the specific entities the user asked about and state clearly that they are unverified.\n"
        "- The 'Most Accurate' Blockquote: Summarize the final verdict in a clear blockquote (> As of [Current Date], I could not verify...).\n"
        "- Actionable Alternatives (Crucial): Never leave the user hanging. Provide a list of top local alternatives or related companies they can ask about next.\n\n"
        "5. Anti-Hallucination & ZERO GUESSING RULE (CRITICAL):\n"
        "You are strictly FORBIDDEN from inventing fake data, companies (e.g., Xylo Labs), or events just to make the response longer (Pressure Hallucination). Zero Fake Data: You MUST NEVER generate fake details.\n"
        "If a specific metric (like USD price) or entity is NOT explicitly stated in the web search results, you must simply output that it is not available. Currency Conversion: Always prioritize price data in PKR. If the search result gives USD, use the current exchange rate to estimate the price in PKR.\n"
        "Enforce Citations: Every single claim, company name, or deadline MUST be accompanied by a valid [Source: URL]. If you cannot find a URL for it, you MUST NOT include it in the response.\n"
        "Proper Empty State: If there is no real data, use the conversational 'No Data Found' format we discussed earlier, explaining why you couldn't find it and suggesting real alternatives (like Arbisoft, Systems Limited), rather than making up fake ones.\n\n"
        "6. Clean Citations Only (CRITICAL SOURCE CITATION RULE):\n"
        "You must ONLY output actual URLs from the provided search results context. NEVER use fake sources like '[Source: Your request]'.\n"
        "You must NEVER state a deadline, price, or official announcement without providing the exact verifiable URL right next to it (e.g., 'The deadline was June 9 [Source: https://...]').\n"
        "If you cannot find an official website or verified social media link in the search context to back up a date or price, you must explicitly state: 'Unverified: No official link found.'\n\n"
        "7. Temporal Reasoning Rule (CRITICAL):\n"
        "You must ALWAYS compare the dates found in search results with the CURRENT SYSTEM DATE (Today is June 30, 2026).\n"
        "Adjust Tenses: If a search result says an event 'will happen' in April 2026, you MUST realize that April has passed. You must rewrite the response in the past tense (e.g., 'It has already premiered on April 12, 2026'). NEVER parrot future tenses for past dates.\n"
        "Contextual Depth: If a specific release date is missing (like for 'Moving Season 2'), do not just say 'Not available'. You must specify its current production status (e.g., 'Officially in development, but no release date yet').\n\n"
        "Local Source Priority: Always prioritize websites like WhatMobile.com.pk, PriceOye.pk, or Mega.pk for pricing comparisons in Pakistan. Avoid international refurbished sites like Back Market.\n\n"
        "NEVER use internal knowledge for factual or time-sensitive queries; strictly rely on the provided search context.\n\n"
        f"{QUALITY_GUIDELINES}"
    )
    
    user_prompt = f"Query: {query}\n\nWeb Search Context:\n{search_context}"
    
    api_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": FRONTEND_URL,
            "X-Title": "OmniAI"
        }
        payload = {
            "model": "openrouter/free",
            "messages": api_messages,
            "temperature": 0.5,
            "max_tokens": 4000
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Search tool failed due to OpenRouter Error: {response.status_code} - {response.text}")
            return error_msg
    except Exception as e:
        print(f"Search tool failed due to OpenRouter Exception: {e}")
        return error_msg
