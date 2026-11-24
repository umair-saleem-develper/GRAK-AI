import os
import re

file_path = os.path.join(os.path.dirname(__file__), "run_qa_benchmark.py")
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the imports to include new functions
content = content.replace(
    "from services.ai_engine import generate_text_stream",
    "from services.ai_engine import generate_text_stream, validate_dependencies, check_provider_health"
)

new_run_benchmark = """
def run_benchmark():
    print("Validating dependencies...")
    validate_dependencies()
    
    print("Running Provider Health Checks...")
    health = check_provider_health()
    print(f"Health Status: {health}")

    results = []
    results_file = os.path.join(os.path.dirname(__file__), "qa_results.json")
    # Resetting the benchmark from scratch as requested.
            
    print("Starting QA Pilot Benchmark (50 Prompts)...")
    
    for i, p in enumerate(PROMPTS):
        print(f"[{i+1}/50] Testing {p['cat']}...", flush=True)
        
        old_stdout = sys.stdout
        sys.stdout = stdout_capturer = StringIO()
        
        start_time = time.time()
        
        response_chunks = []
        try:
            for chunk in generate_text_stream([{"role": "user", "content": p["text"]}]):
                response_chunks.append(chunk)
        except Exception as e:
            response_chunks.append(f"\\n[Exception: {e}]")
            
        latency = time.time() - start_time
        
        sys.stdout = old_stdout
        captured_logs = stdout_capturer.getvalue()
        
        final_response = "".join(response_chunks)
        
        provider = "Unknown"
        fallback_occurred = False
        
        if "Gemini finished" in captured_logs or "Trying provider: Gemini" in captured_logs: provider = "Gemini"
        if "Groq connected" in captured_logs: provider = "Groq"
        if "OpenRouter connected" in captured_logs: provider = "OpenRouter"
        
        if captured_logs.count("Trying provider") > 1:
            fallback_occurred = True
            
        is_empty = (final_response.strip() == "")
        has_error_token = "[Error" in final_response or "[Exception" in final_response
        
        passed = False
        accuracy_score = 0
        adherence_score = 0
        
        has_req = p["req"].lower() in final_response.lower()
        if not is_empty:
            adherence_score = 100
            
        if has_req:
            if has_error_token:
                passed = True
                accuracy_score = 95 # Partial success
            else:
                passed = True
                accuracy_score = 100
        else:
            passed = False
            accuracy_score = 0
            
        provider_success = (passed and accuracy_score >= 95)
                
        if p["cat"] == "Python" and passed:
            try:
                code_blocks = final_response.split("```python")
                if len(code_blocks) > 1:
                    code = code_blocks[1].split("```")[0]
                    ast.parse(code)
            except SyntaxError:
                passed = False
                accuracy_score = 50
                final_response += "\\n\\n[QA_AUTO_DETECT]: Python SyntaxError"
                provider_success = False
                
        results.append({
            "category": p["cat"],
            "prompt": p["text"],
            "response": final_response,
            "pass": passed,
            "accuracy": accuracy_score,
            "adherence": adherence_score,
            "latency": latency,
            "provider": provider,
            "fallback": fallback_occurred,
            "empty": is_empty,
            "error_token": has_error_token,
            "provider_success": provider_success
        })
        
        with open(results_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        time.sleep(2)
        
    print("Benchmark complete. Results saved to qa_results.json")
"""

start_str = "def run_benchmark():"
end_str = "if __name__ == \"__main__\":"

idx_start = content.find(start_str)
idx_end = content.find(end_str)

if idx_start != -1 and idx_end != -1:
    content = content[:idx_start] + new_run_benchmark + "\n" + content[idx_end:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to run_qa_benchmark.py successfully.")
