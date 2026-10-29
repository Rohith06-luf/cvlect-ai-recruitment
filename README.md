# CVlect AI — Recruitment & Talent Matching Platform

![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)

![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)

![React](https://img.shields.io/badge/React-19-61DAFB.svg)

![TypeScript](https://img.shields.io/badge/TypeScript-7-3178C6.svg)

![Vite](https://img.shields.io/badge/Vite-8-646CFF.svg)

![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)CVlect AI is a full-stack recruitment web application with **role-based candidate and recruiter workflows**, deterministic resume/job processing, explainable multi-factor matching, and optional NVIDIA NIM LLM assistance. It is intended as a decision-support tool: match results and analytics help people review candidates and jobs, but the application does not itself hire, reject, or advance anyone.

---

## What the application does

- **Candidates** register, upload PDF/DOCX resumes, inspect extracted profile fields, browse/search/save jobs, apply, track application status, view recommendations, and use an authenticated career assistant.
- **Recruiters** create and manage jobs, rank analyzed resumes against their jobs, inspect applicant/resume details, review pipeline metrics, request aggregate/diagnostic fairness reports, and use the assistant.
- **Matching** is computed pairwise for a resume/job pair using skill, semantic, experience, education, and project signals. Results and explanations are persisted.
- **Optional LLM features** (resume summaries, assistant chat) use NVIDIA NIM. Core parsing, embeddings, and matching run without an API key.

---

## Architecture

```text
Browser (React SPA)
  |
  | JSON/HTTP, bearer JWT
  v
Vite dev proxy (:5173) or Nginx (:3000)
  |
  | /api/*
  v
FastAPI routers (:8000)
  |-- authentication & role checks
  |-- SQLAlchemy session
  |-- services: parsing, NLP, embeddings, matching, explanations, fairness, LLM
  v
SQLite (local default) or PostgreSQL (Compose)
  |-- relational records and JSON fields
  |-- serialized embedding bytes

Resume files --> configured upload directory / Compose named volume
Optional LLM calls --> NVIDIA NIM via OpenAI-compatible client
```

---

## Technology stack

| Layer | Technologies |
| --- | --- |
| Backend framework | Python 3.13, FastAPI 0.115+, Uvicorn, Pydantic v2, Pydantic Settings |
| Database / ORM | SQLAlchemy 2.0, PostgreSQL 16 (Compose), SQLite / aiosqlite (local) |
| Authentication | Passlib (bcrypt), Python-Jose (JWT), HTTP Bearer tokens, PBKDF2 fallback if Passlib is unavailable |
| Document processing | PyMuPDF (`fitz`), python-docx |
| NLP / semantics | spaCy (`en_core_web_sm`), Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Search / ranking utilities | FAISS-CPU, NumPy, scikit-learn |
| Deep learning | PyTorch 2.5 |
| Explainability / fairness | SHAP, Fairlearn (optional/diagnostic) |
| LLM integration | NVIDIA NIM (`z-ai/glm-5.3-flash`) via OpenAI SDK, HTTPX |
| Frontend | React 19, TypeScript 7, Vite 8, React Router 7, Axios |
| Styling / UI | Tailwind CSS 4, Framer Motion, Lucide React |
| Visualization | Recharts |
| Containerization | Docker multi-stage builds, Docker Compose, Nginx Alpine |

---

## Prerequisites

1. **Python 3.13+** (ensure Python is added to PATH on Windows).
2. **Node.js 20+ (24 recommended) and npm**.
3. **Git**.
4. **Docker Desktop** (optional, for containerized deployment).

---

## Local development setup (Windows PowerShell)

### 1. Prepare the environment

```powershell
Set-Location D:\CVLect

# Copy the template to backend/.env (run from the repository root)
Copy-Item .env.example backend\.env
```

Review `backend\.env` privately before starting. Do not commit real secrets.

### 2. Backend

The backend loads `.env` from its current working directory, so run it from `backend/`.

```powershell
Set-Location D:\CVLect\backend

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm

# Optional: explicitly seed sample users/resumes/jobs
python -m sample_data.seed_db

# Start the API
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

On startup, if the database is empty, the backend also attempts to seed the sample data automatically and may generate embeddings if the model is available.

Backend endpoints:

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/api/health`

### 3. Frontend

In a second PowerShell window:

```powershell
Set-Location D:\CVLect\frontend
npm install
npm run dev
```

The development server runs at `http://localhost:5173` and proxies `/api` requests to `http://localhost:8000`.

**Frontend API base:** `VITE_API_URL` defaults to `/api`. A bare backend origin (for example `http://localhost:8000`) is automatically normalized to `/api`; you may also set the complete base explicitly as `http://localhost:8000/api`. In local development, the default uses the Vite `/api` proxy; in Docker, Nginx proxies the same path to FastAPI.

---

## Docker deployment

```powershell
Set-Location D:\CVLect

docker compose up --build -d
docker compose ps
docker compose logs -f
```

Exposed services:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- PostgreSQL: host port **5433** by default, database `${POSTGRES_DB:-cvlect_db}`, user `${POSTGRES_USER:-cvlect}`

Shut down with:

```powershell
docker compose down
```

Named volumes preserve PostgreSQL data and uploaded files.

---

## Sample accounts

The seed script creates the following accounts with password `Password123!`:

| Email | Role | Name |
| --- | --- | --- |
| `avery.sterling@example.com` | Candidate | Avery Sterling |
| `maya.linnea@example.com` | Candidate | Maya Linnea |
| `devon.vance@example.com` | Candidate | Devon Vance |
| `recruiter@example.com` | Recruiter | Sarah Jenkins |
| `techrecruiter@example.com` | Recruiter | Marcus Vance |

If the frontend login page quick-fill buttons use different credentials, use the accounts listed here (or create your own) because only seeded/created accounts will work.

---

## Configuration

Key environment variables (see `.env.example`):

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL (`sqlite:///./cvlect.db` default; PostgreSQL in Compose) |
| `JWT_SECRET_KEY` | JWT signing secret |
| `JWT_ALGORITHM` | JWT algorithm (default `HS256`) |
| `JWT_EXPIRATION_MINUTES` | Token lifetime (default `1440`) |
| `NVIDIA_API_KEY` | Enables optional LLM features |
| `NVIDIA_BASE_URL` | NIM base URL |
| `NVIDIA_MODEL` | NIM model name |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit (default `10`) |
| `UPLOAD_DIR` | Upload storage directory (default `./uploads`) |
| `SPACY_MODEL` | spaCy model name |
| `SENTENCE_TRANSFORMER_MODEL` | Embedding model name |
| `HOST`, `PORT`, `DEBUG` | Server settings |
| `CORS_ORIGINS` | Comma-separated trusted origins |
| `VITE_API_URL` | Frontend API base URL (a bare backend origin is automatically given the `/api` prefix) |

Rotating any credential that has been exposed in `.env` files is recommended. Do not commit secrets.

---

## The 5-stage matching pipeline

```text
[Raw document] -> [Stage A: Parser] -> [Stage B: Embeddings] -> [Stage C: Features] -> [Stage D: Ranking] -> [Stage E: Explanation]
```

1. **Stage A — Document processing / fact extraction:** extracts PDF/DOCX text, contact details, skills, education, work history, projects, certifications, and quality suggestions using dictionaries, regex, and section heuristics. Skills are normalized against a 150+ token taxonomy (aliases such as `k8s` → `kubernetes`, `reactjs` → `react`).
2. **Stage B — Dense semantic representations:** optional Sentence-Transformers `all-MiniLM-L6-v2` vectors (384 dimensions). Vectors are stored as serialized bytes. A FAISS utility exists, but the current API matching/recommendation code scores pairs directly.
3. **Stage C — Feature engineering:** skill coverage (required 85% + preferred 15%), semantic similarity, experience alignment, education alignment, and project relevance.
4. **Stage D — Ranking:** weighted baseline by default (Skill 30%, Semantic 25%, Experience 20%, Project 15%, Education 10%) or an optional PyTorch neural ranker loaded from `backend/app/ml/ranking_model.pt`. `is_demo_mode` is reported with results.
5. **Stage E — Explainability:** matched/missing/partial skills, factor contributions, recommendations, and evidence snippets.

---

## API overview

All application endpoints are under `/api`; the API also serves `/`, `/docs`, `/redoc`, `/openapi.json`, and `/api/health`.

| Method | Path | Access | Behavior |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | Public | Create candidate/recruiter, return JWT |
| `POST` | `/api/auth/login` | Public | Authenticate, return JWT |
| `GET` | `/api/auth/me` | Authenticated | Current user profile |
| `POST` | `/api/resumes/upload` | Candidate | Upload `.pdf`/`.docx` |
| `GET` | `/api/resumes` | Candidate | List candidate resumes |
| `GET` | `/api/resumes/{id}` | Authenticated | Resume and extracted profile |
| `POST` | `/api/resumes/{id}/analyze` | Candidate owner | Parse, embed, optionally summarize |
| `POST` | `/api/jobs` | Recruiter | Create job (extracts missing requirements) |
| `GET` | `/api/jobs` | Public | List/search/filter jobs with pagination |
| `GET` | `/api/jobs/{id}` | Public | Retrieve job |
| `PUT` | `/api/jobs/{id}` | Recruiter owner | Update job |
| `DELETE` | `/api/jobs/{id}` | Recruiter owner | Delete job |
| `POST` | `/api/matching/analyze` | Authenticated | Score one resume/job pair |
| `GET` | `/api/matching/jobs/{id}/candidates` | Recruiter owner | Rank analyzed resumes for a job |
| `GET` | `/api/matching/resumes/{id}/jobs` | Candidate owner | Rank active jobs for a resume |
| `GET` | `/api/matching/{id}/explanation` | Related parties | Detailed explanation |
| `POST` | `/api/applications` | Candidate | Apply to active job |
| `GET` | `/api/applications` | Authenticated | Candidate submissions or recruiter job applications |
| `PATCH` | `/api/applications/{id}/status` | Candidate or recruiter owner | Update/withdraw status |
| `GET` | `/api/analytics/candidate` | Candidate | Candidate dashboard metrics |
| `GET` | `/api/analytics/recruiter` | Recruiter | Recruiter dashboard metrics |
| `GET` | `/api/analytics/fairness[...]` | Recruiter | Diagnostic fairness/score-distribution report |
| `POST` | `/api/assistant/chat` | Authenticated | LLM assistant with role-checked context |
| `GET` | `/api/saved-jobs` | Candidate | List saved jobs |
| `POST` | `/api/saved-jobs/{id}` | Candidate | Save job |
| `DELETE` | `/api/saved-jobs/{id}` | Candidate | Remove saved job |

---

## Running tests

Backend:

```powershell
Set-Location D:\CVLect\backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

Frontend:

```powershell
Set-Location D:\CVLect\frontend
npm run build
npm run lint
```

Tests cover authentication, jobs/RBAC, uploads, parser heuristics, and matching. They do not replace full browser, migration, production, security, or model-calibration validation.

---

## Project structure

```text
D:\CVLect\
├── .env.example
├── docker-compose.yml
├── PROJECT_EXPLANATION.md
├── README.md
├── archive/                    # Large resume corpus (data asset, not runtime-wired)
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI routers
│   │   ├── ml/                 # PyTorch ranker, training, evaluation
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Parsing, NLP, embeddings, matching, LLM, etc.
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── sample_data/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   └── types/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
└── uploads/
```

---

## Known implementation notes

These points are worth understanding before presenting the project as production-ready:

1. **Ranking is pairwise.** FAISS and NumPy utilities exist, but the API matching endpoints calculate pairwise scores; they do not build/query a vector index to shortlist.
2. **Recruiter ranking includes all analyzed resumes.** `GET /api/matching/jobs/{job_id}/candidates` ranks every analyzed resume in the database, not only applicants to that job.
3. **Access rules differ.** The matching endpoint verifies recruiter ownership of the job; resume-detail access is restricted to applicants of one of that recruiter's jobs.
4. **Some frontend controls are partial.** `min_score` is sent but not filtered server-side; recruiter candidate shortlist/interview/reject modal buttons update local UI state only and do not call the application status API.
5. **Health is not a database probe.** `/api/health` returns a fixed database label, although startup logs initialization errors.
6. **Fairness is diagnostic.** The endpoint returns aggregate score statistics; it does not infer protected traits, and small-sample fallback can include records outside a recruiter's jobs.
7. **Model weights are not empirically calibrated by default.** The training/evaluation tools use synthetic data. Treat outputs as decision support, not validated hiring instruments.
8. **Optional features depend on installed libraries/network.** Missing optional dependencies, spaCy model downloads, or model cache issues can disable embeddings, SHAP, or LLM features gracefully.
9. **The JWT secret in local/Compose defaults must be changed** for real deployment.

---

## Data handling and operational notes

- Resume files are stored on disk; parsed text, contact data, skills, and embeddings are stored in the database. Protect both.
- The parser is heuristic and can be wrong; human review is required.
- Optional LLM features send constructed context to the configured provider. Review privacy, retention, and provider terms first.
- Docker Compose publishes database/API/frontend ports to the host. Restrict exposure and configure TLS/reverse proxy/firewalls as appropriate in production.

---

## Contributing

1. Fork the repository.
2. Create a descriptive branch.
3. Commit clear, focused changes.
4. Run the backend tests and frontend build/lint before opening a pull request.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.