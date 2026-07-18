"""
Helper script to upload PDF resumes to the CVlect backend.

Usage:
  python upload.py <pdf-or-folder> [--recruiter <email>] [--job <id>]

Examples:
  python upload.py "C:\\resumes\\Priya.pdf"
  python upload.py "C:\\resumes_folder"
  python upload.py "C:\\resumes_folder" --recruiter alex.reed@cvlect.com --job 1
"""
import sys
import os
import json
import urllib.request

API = "http://127.0.0.1:8000"


def login(email: str, password: str) -> str:
    """Login and return the bearer token."""
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["token"]


def upload_pdf(pdf_path: str, token: str, job_id: int | None = None):
    """Upload a single PDF to the backend."""
    # Build multipart/form-data manually
    boundary = "----CVlectBoundary12345"
    filename = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()

    # Choose endpoint based on whether job_id is provided
    if job_id:
        url = f"{API}/pipeline/ingest-pdf?job_id={job_id}"
    else:
        url = f"{API}/profiles/upload-resume"

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"  ✓ {filename} -> {result}")
    except urllib.error.HTTPError as e:
        print(f"  ✗ {filename} -> ERROR {e.code}: {e.read().decode()}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python upload.py "<pdf-path-or-folder>" [--recruiter <email>] [--job <id>]')
        print()
        print("Examples:")
        print('  python upload.py "C:\\resumes\\Priya.pdf"')
        print('  python upload.py "C:\\resumes_folder" --recruiter alex.reed@cvlect.com --job 1')
        sys.exit(1)

    target = sys.argv[1]
    recruiter_email = "alex.reed@cvlect.com"
    recruiter_password = "recruiter123"
    job_id = None

    for i, arg in enumerate(sys.argv):
        if arg == "--recruiter" and i + 1 < len(sys.argv):
            recruiter_email = sys.argv[i + 1]
        if arg == "--job" and i + 1 < len(sys.argv):
            job_id = int(sys.argv[i + 1])

    print(f"Logging in as {recruiter_email}...")
    token = login(recruiter_email, recruiter_password)
    print(f"Token acquired.\n")

    # Collect PDFs
    pdfs = []
    if os.path.isfile(target) and target.lower().endswith(".pdf"):
        pdfs = [target]
    elif os.path.isdir(target):
        pdfs = [
            os.path.join(target, f)
            for f in sorted(os.listdir(target))
            if f.lower().endswith(".pdf")
        ]
    else:
        print(f"Error: {target} is not a valid PDF file or directory.")
        sys.exit(1)

    if not pdfs:
        print("No PDF files found.")
        sys.exit(1)

    print(f"Found {len(pdfs)} PDF(s) to upload:\n")
    for pdf in pdfs:
        print(f"Uploading {os.path.basename(pdf)}...")
        upload_pdf(pdf, token, job_id)

    print("\nDone! Check the database with:")
    print("  python -c \"from db import get_db; [print(dict(r)) for r in get_db().execute('SELECT id, full_name, resume_score FROM candidate_profiles').fetchall()]\"")


if __name__ == "__main__":
    main()
