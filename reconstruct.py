import json

log_path = r"C:\Users\us761\.gemini\antigravity\brain\b886d5fe-0b73-4b8f-b9f9-94f3e892aea4\.system_generated\logs\transcript_full.jsonl"

content_lines = []

try:
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'page.jsx' in line and ('write' in line or 'replace' in line):
                data = json.loads(line)
                for tc in data.get('tool_calls', []):
                    name = tc.get('name', '')
                    if 'write' in name or 'replace' in name:
                        args = tc.get('args', {})
                        target = args.get('TargetFile', '')
                        target_norm = target.replace('\\', '/')
                        if target_norm == 'C:/Users/us761/.gemini/antigravity/scratch/OmniAI/frontend/app/page.jsx':
                            step = data.get('step_index')
                            if step < 652:
                                continue
                            if step > 5124:
                                continue
                            
                            if name == 'write_to_file':
                                code = args.get('CodeContent', '')
                                content_lines = code.split('\n')
                            elif name == 'replace_file_content':
                                start = args.get('StartLine', 1) - 1
                                end = args.get('EndLine', len(content_lines))
                                target_content = args.get('TargetContent', '')
                                repl = args.get('ReplacementContent', '').split('\n')
                                
                                # Search for target_content in the range
                                target_lines = target_content.split('\n')
                                found_idx = -1
                                for i in range(start, end - len(target_lines) + 2):
                                    if i < len(content_lines) and content_lines[i:i+len(target_lines)] == target_lines:
                                        found_idx = i
                                        break
                                if found_idx != -1:
                                    content_lines = content_lines[:found_idx] + repl + content_lines[found_idx + len(target_lines):]
                                else:
                                    print(f"Warning: TargetContent not found in replace_file_content at step {step}")
                                
                            elif name == 'multi_replace_file_content':
                                chunks = args.get('ReplacementChunks', [])
                                chunks.sort(key=lambda x: x.get('StartLine', 1), reverse=True)
                                for chunk in chunks:
                                    start = chunk.get('StartLine', 1) - 1
                                    end = chunk.get('EndLine', len(content_lines))
                                    target_content = chunk.get('TargetContent', '')
                                    repl = chunk.get('ReplacementContent', '').split('\n')
                                    
                                    target_lines = target_content.split('\n')
                                    found_idx = -1
                                    for i in range(start, end - len(target_lines) + 2):
                                        if i < len(content_lines) and content_lines[i:i+len(target_lines)] == target_lines:
                                            found_idx = i
                                            break
                                    if found_idx != -1:
                                        content_lines = content_lines[:found_idx] + repl + content_lines[found_idx + len(target_lines):]
                                    else:
                                        print(f"Warning: TargetContent not found in multi_replace at step {step}")

    with open(r"C:\Users\us761\.gemini\antigravity\scratch\OmniAI\frontend\app\page_recovered.jsx", "w", encoding='utf-8') as out:
        out.write('\n'.join(content_lines))
    print(f"Recovered to frontend/app/page_recovered.jsx (length: {len(content_lines)} lines)")
except Exception as e:
    print(e)
