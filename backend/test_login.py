import json
import urllib.request

payload = json.dumps({"email": "admin@example.com", "password": "admin123"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/auth/login",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as response:
    print(response.read().decode())
