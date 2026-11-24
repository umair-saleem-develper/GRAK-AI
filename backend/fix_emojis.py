import os

ai_engine_path = os.path.join(os.path.dirname(__file__), "services", "ai_engine.py")
with open(ai_engine_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("❌ ", "FAILED: ").replace("✅ ", "SUCCESS: ")

with open(ai_engine_path, "w", encoding="utf-8") as f:
    f.write(content)

bench_path = os.path.join(os.path.dirname(__file__), "run_qa_benchmark.py")
with open(bench_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("❌ ", "FAILED: ").replace("✅ ", "SUCCESS: ").replace("⚠️ ", "WARNING: ")

with open(bench_path, "w", encoding="utf-8") as f:
    f.write(content)
