import requests
import json
try:
    response = requests.get('https://openrouter.ai/api/v1/models')
    models = response.json()['data']
    free_models = [m['id'] for m in models if m['pricing']['prompt'] == '0' or ':free' in m['id']]
    print("Free models:", free_models)
except Exception as e:
    print("Error:", e)
