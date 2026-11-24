import requests

for port in [8000, 8001]:
    try:
        res = requests.get(f'http://localhost:{port}/openapi.json')
        print(f"--- Port {port} ---")
        paths = list(res.json().get('paths', {}).keys())
        print(paths[:5])
    except Exception as e:
        print(f"Error on {port}: {e}")
