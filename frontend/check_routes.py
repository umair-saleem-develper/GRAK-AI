import requests

try:
    res = requests.get('http://localhost:8000/openapi.json')
    paths = res.json().get('paths', {}).keys()
    for p in paths:
        print(p)
except Exception as e:
    print(e)
