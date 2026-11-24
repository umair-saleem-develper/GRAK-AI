import requests, json
res = requests.get('http://localhost:8000/openapi.json')
print(json.dumps(res.json(), indent=2))

