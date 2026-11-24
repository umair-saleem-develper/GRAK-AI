import json

with open('qa_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
passed = sum(1 for d in data if d['pass'])
accuracy = sum(d['accuracy'] for d in data) / total if total > 0 else 0
adherence = sum(d['adherence'] for d in data) / total if total > 0 else 0
latency = sum(d['latency'] for d in data) / total if total > 0 else 0
errors = sum(1 for d in data if d['error_token'] or d['empty'])
hallucination_failures = sum(1 for d in data if d['accuracy'] == 0 and not d['error_token'] and not d['empty'])

failed_cases = [(d['category'], d['prompt'], d['accuracy'], d['provider'], d.get('fallback', False), d.get('empty', False), d.get('error_token', False)) for d in data if not d['pass']]

print(f'Total: {total}')
print(f'Overall Accuracy: {accuracy:.2f}%')
print(f'Prompt Adherence: {adherence:.2f}%')
print(f'Average Latency: {latency:.2f}s')
print(f'Error Rate: {(errors/total)*100:.2f}% ({errors} cases)')
print(f'Hallucination Rate: {(hallucination_failures/total)*100:.2f}% ({hallucination_failures} cases)')

fallbacks = sum(1 for d in data if d.get('fallback'))
print(f'Fallbacks triggered: {fallbacks}')

print(f'Failed Cases: {len(failed_cases)}')
for c in failed_cases:
    print(f'- [{c[0]}] {c[1][:50]}... | Acc: {c[2]} | Prov: {c[3]} | Fallback: {c[4]} | Empty: {c[5]} | Err: {c[6]}')
