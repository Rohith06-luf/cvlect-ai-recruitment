# AI Resume Screening API

A production-ready FastAPI backend for an AI resume screening system.

## Features
- JWT authentication with access and refresh tokens
- Role-based authorization for Admin, Recruiter, and Candidate
- Candidate, job, and resume management
- PDF upload handling with size validation
- Placeholder AI resume analysis service
- CORS configuration and environment-based settings

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment
Copy .env.example to .env and adjust values as needed.
