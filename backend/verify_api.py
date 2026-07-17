import json
from urllib import request

BASE_URL = 'http://127.0.0.1:8000'


def login() -> str:
    payload = json.dumps({'email': 'admin@example.com', 'password': 'admin123'}).encode()
    req = request.Request(
        f'{BASE_URL}/auth/login',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with request.urlopen(req, timeout=20) as resp:
        body = json.load(resp)
    data = body.get('data', {}) if isinstance(body, dict) else {}
    token = data.get('access_token') or body.get('access_token') or body.get('token') or data.get('token')
    if not token:
        raise KeyError(f'No access token returned: {body}')
    return token


def health_check() -> dict:
    with request.urlopen(f'{BASE_URL}/health', timeout=10) as resp:
        return json.load(resp)


if __name__ == '__main__':
    print('health', health_check())
    token = login()
    print('token_ready', bool(token))
    print('token_prefix', token[:20])
