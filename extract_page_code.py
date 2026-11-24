import json

log_path = r"C:\Users\us761\.gemini\antigravity\brain\b886d5fe-0b73-4b8f-b9f9-94f3e892aea4\.system_generated\logs\transcript_full.jsonl"

versions = []
targets = set()
try:
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'TargetFile' in line:
                data = json.loads(line)
                for tc in data.get('tool_calls', []):
                    name = tc.get('name', '')
                    if 'write' in name or 'replace' in name:
                        args = tc.get('args', {})
                        target = args.get('TargetFile', '')
                        if 'page.jsx' in target:
                            versions.append({
                                'step': data.get('step_index'),
                                'tool': name,
                                'target': target,
                                'code': args.get('CodeContent', ''),
                                'chunks': args.get('ReplacementChunks', [])
                            })
except Exception as e:
    print(e)

with open(r"C:\Users\us761\.gemini\antigravity\scratch\OmniAI\page_versions.json", "w") as f:
    json.dump(versions, f, indent=2)

print(f"Extracted {len(versions)} versions")
