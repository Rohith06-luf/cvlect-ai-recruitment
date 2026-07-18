"""
e2e_test.py – Full end-to-end smoke test for the CVlect FastAPI modular backend.
Run from the backend/ directory with the venv active:
    python e2e_test.py
"""
import sys, json
from urllib import request, error

BASE = "http://127.0.0.1:8000"
results = []

def req(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def chk(name, cond, detail=""):
    ok = bool(cond)
    results.append((ok, name, str(detail)[:120]))
    print(f"{'[PASS]' if ok else '[FAIL]'} {name}" + (f" -> {detail}" if not ok else ""))
    return ok

print("=" * 60)
print("CVlect Backend End-to-End Test")
print("=" * 60)

# 1. Health
status, body = req("GET", "/health")
chk("GET /health returns 200", status == 200, body)
chk("GET /health success=true", body.get("success") is True, body)

# 2. Register new user
status, body = req("POST", "/auth/signup", {"name":"Test User","email":"testuser_e2e@example.com","password":"password123","role":"candidate"})
chk("POST /auth/signup 200", status == 200, body)
token = body.get("token") or (body.get("data", {}) or {}).get("access_token")
chk("POST /auth/signup returns token", bool(token), body)

# 3. Login existing candidate
status, body = req("POST", "/auth/login", {"email":"priya.sharma@example.com","password":"candidate123"})
chk("POST /auth/login (candidate) 200", status == 200, body)
cand_token = body.get("token") or (body.get("data", {}) or {}).get("access_token")
chk("POST /auth/login returns token", bool(cand_token), body)

# 4. Login existing recruiter
status, body = req("POST", "/auth/login", {"email":"alex.reed@cvlect.com","password":"recruiter123"})
chk("POST /auth/login (recruiter) 200", status == 200, body)
rec_token = body.get("token") or (body.get("data", {}) or {}).get("access_token")
rec_user = body.get("user", {})
rec_id = rec_user.get("id")
chk("POST /auth/login (recruiter) returns token", bool(rec_token), body)

# 5. GET /auth/me
status, body = req("GET", "/auth/me", token=cand_token)
chk("GET /auth/me 200", status == 200, body)
cand_user = body
cand_id = cand_user.get("id") if isinstance(body, dict) else None
chk("GET /auth/me returns user with id", bool(cand_id), body)

# 6. GET /users/me
status, body = req("GET", "/users/me", token=cand_token)
chk("GET /users/me 200", status == 200, body)
chk("GET /users/me has email", "email" in (body if isinstance(body, dict) else {}), body)

# 7. GET /profiles/me
status, body = req("GET", "/profiles/me", token=cand_token)
chk("GET /profiles/me 200", status == 200, body)
chk("GET /profiles/me has ats_score", "ats_score" in (body if isinstance(body, dict) else {}), body)

# 8. GET /jobs
status, body = req("GET", "/jobs", token=cand_token)
chk("GET /jobs 200", status == 200, body)
jobs = body if isinstance(body, list) else []
chk("GET /jobs returns list with items", len(jobs) > 0, f"count={len(jobs)}")
job_id = jobs[0]["id"] if jobs else None

# 9. GET /jobs/:id
if job_id:
    status, body = req("GET", f"/jobs/{job_id}", token=cand_token)
    chk("GET /jobs/:id 200", status == 200, body)
    chk("GET /jobs/:id has title", "title" in (body if isinstance(body, dict) else {}), body)

# 10. GET /applications/me
status, body = req("GET", "/applications/me", token=cand_token)
chk("GET /applications/me 200", status == 200, body)
apps = body if isinstance(body, list) else []
chk("GET /applications/me returns list", isinstance(body, list), body)

# 11. POST /applications (apply to a job)
if job_id:
    status, body = req("POST", "/applications", {"job_id": job_id}, token=cand_token)
    chk("POST /applications 200 or 200 (already applied)", status in (200, 409, 201), body)

# 12. GET /stats (recruiter)
status, body = req("GET", f"/stats?recruiter_id={rec_id}", token=rec_token)
chk("GET /stats 200", status == 200, body)
chk("GET /stats has total_resumes", "total_resumes" in (body if isinstance(body, dict) else {}), body)

# 13. GET /pipeline
if job_id:
    status, body = req("GET", f"/pipeline?job_id={job_id}", token=rec_token)
    chk("GET /pipeline 200", status == 200, body)
    chk("GET /pipeline returns list", isinstance(body, list), body)

# 14. GET /pipeline/count
if job_id:
    status, body = req("GET", f"/pipeline/count?job_id={job_id}", token=rec_token)
    chk("GET /pipeline/count 200", status == 200, body)
    chk("GET /pipeline/count has total", "total" in (body if isinstance(body, dict) else {}), body)

# 15. GET /activities
status, body = req("GET", "/activities", token=rec_token)
chk("GET /activities 200", status == 200, body)
chk("GET /activities returns list", isinstance(body, list), body)

# 16. Invalid PDF upload rejection (send non-PDF)
import io, urllib.parse
boundary = "----TestBoundary12345"
content = b"fake content that is not a pdf"
multipart = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
    f"Content-Type: text/plain\r\n\r\n"
).encode() + content + f"\r\n--{boundary}--\r\n".encode()

r = request.Request(
    f"{BASE}/profiles/upload-resume",
    data=multipart,
    headers={"Authorization": f"Bearer {cand_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST"
)
try:
    with request.urlopen(r, timeout=10) as resp:
        status, body = resp.status, json.loads(resp.read())
except error.HTTPError as e:
    status, body = e.code, json.loads(e.read().decode())
chk("POST /profiles/upload-resume non-PDF returns 400", status == 400, body)

# 17. Auth token refresh
status, body = req("POST", "/api/auth/refresh", {"refresh_token": "invalid_token"})
chk("POST /api/auth/refresh with invalid token returns 401", status == 401, body)

# 18. Protected route without token returns 401
status, body = req("GET", "/auth/me")
chk("GET /auth/me without token returns 401", status == 401, body)

# 19. API docs available (/docs returns HTML)
r2 = request.Request(f"{BASE}/docs")
try:
    with request.urlopen(r2, timeout=5) as resp:
        docs_status = resp.status
except:
    docs_status = 0
chk("GET /docs returns 200 (Swagger UI)", docs_status == 200, f"status={docs_status}")

# 20. Admin login via /api/auth/login
status, body = req("POST", "/api/auth/login", {"email":"admin@example.com","password":"admin123"})
chk("POST /api/auth/login (admin) 200", status == 200, body)
admin_token = (body.get("data") or {}).get("access_token")
chk("POST /api/auth/login admin token returned", bool(admin_token), body)

# 21. GET /api/auth/me with admin token
status, body = req("GET", "/api/auth/me", token=admin_token)
chk("GET /api/auth/me (admin JWT) 200", status == 200, body)

print()
print("=" * 60)
passed = sum(1 for ok, _, _ in results if ok)
total = len(results)
print(f"Result: {passed}/{total} passed")
print("=" * 60)
for ok, name, detail in results:
    print(f"  {'[PASS]' if ok else '[FAIL]'} {name}")
    if not ok:
        print(f"         -> {detail}")

if passed < total:
    sys.exit(1)
