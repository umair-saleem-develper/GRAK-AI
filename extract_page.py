import json
import re

log_path = r"C:\Users\us761\.gemini\antigravity\brain\b886d5fe-0b73-4b8f-b9f9-94f3e892aea4\.system_generated\logs\transcript_full.jsonl"
out_path = r"C:\Users\us761\.gemini\antigravity\scratch\OmniAI\extracted_page.txt"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found_content = []
for idx, line in enumerate(lines):
    try:
        data = json.loads(line)
        if data.get('type') == 'PLANNER_RESPONSE' or data.get('type') == 'TOOL_CALL':
            content = data.get('content', '')
            if content:
                found_content.append(content)
            
            tool_calls = data.get('tool_calls', [])
            for tc in tool_calls:
                args = tc.get('arguments', {})
                # Look for write_to_file or replace_file_content for page.jsx
                if isinstance(args, dict):
                    target = args.get('TargetFile', '')
                    if 'page.jsx' in target:
                        found_content.append(f"TOOL CALL MATCH at step {data.get('step_index')}: {target}")
                        code = args.get('CodeContent', '')
                        if code:
                            found_content.append("CODE CONTENT:\n" + code[:1000] + "\n...")
                        replacements = args.get('ReplacementChunks', [])
                        if replacements:
                            found_content.append(f"REPLACEMENT: {replacements}")
    except Exception as e:
        pass

with open(out_path, 'w', encoding='utf-8') as out:
    for item in found_content[-50:]:  # last 50 matches
        out.write(str(item) + "\n-------------------------\n")

print("Done. Check extracted_page.txt")
