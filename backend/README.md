# CVlect Backend (FastAPI + SQLite3)

Python backend for the CVlect AI recruitment frontend. Built with **FastAPI**, **SQLite3** (via the built-in `sqlite3` module), and **pdfplumber** for PDF resume ingestion.

## Features

- **Auth** — signup/login/logout with bearer tokens (recruiter & candidate roles)
- **Jobs** — recruiters post jobs; candidates browse and apply
- **Candidate profiles** — resume scores, skills (current/missing), career health
- **Applications** — candidates apply to jobs; recruiters update status
- **Pipeline** — recruiter screening pipeline with AI scores, ranks, matched/missing skills
- **Activities** — audit log of recruiter actions
- **Stats** — dashboard counts (total / shortlisted / selected / rejected)
- **PDF ingestion** — upload resume PDFs, extract data, and store in the database

## Quick start

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 1. Initialize + seed the database
python seed.py

# 2. (Optional) Ingest PDF resumes
python pdf_ingest.py path/to/resume.pdf
python pdf_ingest.py path/to/resumes_folder/

# 3. Run the API
uvicorn main:app --reload --port 8000
```

- API docs (Swagger UI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default logins (after seeding)

| Role      | Email                     | Password        |
|-----------|---------------------------|-----------------|
| Recruiter | `alex.reed@cvlect.com`    | `recruiter123`  |
| Candidate | `priya.sharma@example.com`| `candidate123`  |

## Ingesting PDF resumes

The `pdf_ingest.py` script extracts text from PDF resumes using `pdfplumber` and parses common fields (name, email, phone, skills, experience, summary, location) with simple heuristics.

```bash
# Single PDF
python pdf_ingest.py "C:\path\to\Priya_Sharma_Resume.pdf"

# All PDFs in a folder
python pdf_ingest.py "C:\path\to\resumes"

# Add to a recruiter's pipeline for a specific job
python pdf_ingest.py "C:\path\to\resume.pdf" --recruiter 1 --job 1
```

You can also upload PDFs via the API:

```
POST /profiles/upload-resume        (candidate uploads own resume)
POST /pipeline/ingest-pdf?job_id=1 (recruiter adds candidate to pipeline)
```

## API overview

| Method | Path                              | Description                          |
|--------|-----------------------------------|--------------------------------------|
| POST   | `/auth/signup`                    | Register a new user                  |
| POST   | `/auth/login`                     | Login, returns bearer token          |
| POST   | `/auth/logout`                    | Invalidate session                   |
| GET    | `/auth/me`                        | Current user                         |
| GET    | `/jobs`                           | List jobs                            |
| POST   | `/jobs`                           | Create job (recruiter)               |
| GET    | `/profiles`                       | List candidate profiles              |
| GET    | `/profiles/me`                    | Current candidate's profile          |
| POST   | `/profiles/upload-resume`         | Upload resume PDF (candidate)        |
| GET    | `/applications`                   | List applications                    |
| GET    | `/applications/me`                | Current candidate's applications     |
| POST   | `/applications`                   | Apply to a job (candidate)           |
| PUT    | `/applications/{id}/status`       | Update application status            |
| GET    | `/pipeline`                       | List pipeline entries (paginated)    |
| PUT    | `/pipeline/{id}/status`           | Shortlist/select/reject a candidate  |
| POST   | `/pipeline/ingest-pdf?job_id=`    | Ingest PDF into pipeline (recruiter) |
| GET    | `/stats`                           | Dashboard stats                      |
| GET    | `/activities`                     | Recent activity log                  |

## Project structure

```
backend/
├── main.py            # FastAPI app with all routes
├── db.py              # SQLite3 connection + schema
├── models.py          # Pydantic request/response models
├── seed.py            # Seed data matching the frontend
├── pdf_ingest.py      # PDF parsing + ingestion
├── requirements.txt
├── data/              # SQLite database file (auto-created)
│   └── cvlect.db
└── uploads/           # Uploaded resume PDFs
```

## Connecting the frontend

The API runs on `http://localhost:8000`. The Vite dev server runs on `http://localhost:5173`. CORS is pre-configured to allow the frontend origin. To wire the frontend to the backend, replace the mock data in the route components with `fetch`/`react-query` calls to these endpoints.
