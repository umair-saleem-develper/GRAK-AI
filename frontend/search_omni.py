import os

def search_dir(d):
    for root, dirs, files in os.walk(d):
        if '.venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if 'OmniAI Backend' in content:
                        print(f"Found in {path}")
            except Exception:
                pass

search_dir(r'C:\Users\us761\.gemini\antigravity\scratch\GrakAI')
