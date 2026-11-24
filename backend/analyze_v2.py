import json

with open('qa_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
passed = sum(1 for d in data if d['pass'])
accuracy = sum(d['accuracy'] for d in data) / total if total > 0 else 0
adherence = sum(d['adherence'] for d in data) / total if total > 0 else 0
latency = sum(d['latency'] for d in data) / total if total > 0 else 0
errors = sum(1 for d in data if d['error_token'] or d['empty'])
hallucination_failures = sum(1 for d in data if not d['pass'] and not d['error_token'] and not d['empty'])

provider_counts = {'Gemini': 0, 'OpenRouter': 0, 'Groq': 0}
provider_successes = {'Gemini': 0, 'OpenRouter': 0, 'Groq': 0}

for d in data:
    p = d['provider']
    if p in provider_counts:
        provider_counts[p] += 1
        if d['provider_success']:
            provider_successes[p] += 1

fallback_triggers = sum(1 for d in data if d.get('fallback'))
fallback_successes = sum(1 for d in data if d.get('fallback') and d['provider_success'])

failed_cases = [(d['category'], d['prompt'], d['accuracy'], d['provider'], d.get('fallback', False), d.get('empty', False)) for d in data if not d['pass']]

print(f'Total: {total}')
print(f'Overall Accuracy: {accuracy:.2f}%')
print(f'Prompt Adherence: {adherence:.2f}%')
print(f'Average Latency: {latency:.2f}s')
print(f'Error Rate: {(errors/total)*100:.2f}% ({errors} cases)')
print(f'Hallucination Rate: {(hallucination_failures/total)*100:.2f}% ({hallucination_failures} cases)')
print(f"Fallback/Retry Success Rate: {(fallback_successes/fallback_triggers*100) if fallback_triggers else 0:.2f}% ({fallback_successes}/{fallback_triggers})")

for p in ['Gemini', 'OpenRouter', 'Groq']:
    rate = (provider_successes[p]/provider_counts[p]*100) if provider_counts[p] else 0
    print(f"Provider Success [{p}]: {rate:.2f}% ({provider_successes[p]}/{provider_counts[p]})")

print(f'Failed Cases: {len(failed_cases)}')
for c in failed_cases:
    print(f'- [{c[0]}] {c[1][:50]}... | Acc: {c[2]} | Prov: {c[3]} | Fallback: {c[4]} | Empty: {c[5]}')
