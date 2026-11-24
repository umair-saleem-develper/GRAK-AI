import os
import re

def search_dir(d):
    for root, dirs, files in os.walk(d):
        for f in files:
            if not f.endswith('.tsx') and not f.endswith('.ts'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = re.findall(r'[\'"`]/api/[a-zA-Z0-9_-]+', content)
                    if matches:
                        print(f"Found in {path}: {set(matches)}")
            except Exception:
                pass

search_dir(r'C:\Users\us761\.gemini\antigravity\scratch\OmniAI\frontend')
