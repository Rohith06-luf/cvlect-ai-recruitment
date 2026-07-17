"""
CVlect FastAPI backend.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations
import os
import hashlib
import secrets
from typing import List, Optional
from datetime import date

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import init_db, get_db
from models import (
    UserCreate, UserLogin, UserOut, TokenOut,
    JobCreate, JobOut,
    CandidateProfileOut,
    ApplicationCreate, ApplicationOut,
    PipelineEntryOut, PipelineStatusUpdate,
    ActivityOut, StatsOut,
    MessageOut, IdOut,
)
from pdf_ingest import ingest_pdf, parse_resume_pdf, ingest_candidate

app = FastAPI(
    title="CVlect API",
    description="Backend for the CVlect AI recruitment platform.",
    version="1.0.0",
)

# CORS — allow the Vite dev server and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

security = HTTPBearer(auto_error=False)


# =========================================================
# Helpers
# =========================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def row_to_user(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "avatar_initials": row["avatar_initials"],
        "phone": row["phone"],
        "location": row["location"],
        "company": row["company"],
        "job_title": row["job_title"],
        "team": row["team"],
        "about": row["about"],
        "verified": bool(row["verified"]),
        "created_at": str(row["created_at"]) if row["created_at"] else None,
    }


def get_or_create_skill(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO skills (name) VALUES (?)", (name,))
    return cur.lastrowid


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Dependency: extract and validate the bearer token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    with get_db() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return row_to_user(row)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    token = credentials.credentials
    with get_db() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
        return row_to_user(row) if row else None


def require_role(user: dict, role: str):
    if user["role"] != role:
        raise HTTPException(status_code=403, detail=f"This endpoint requires {role} role")


# =========================================================
# Root
# =========================================================
@app.get("/", tags=["root"])
def root():
    return {"message": "CVlect API is running", "docs": "/docs"}


@app.post("/init", tags=["root"], response_model=MessageOut)
def init_database():
    init_db()
    return {"message": "Database initialized"}


# =========================================================
# Auth
# =========================================================
@app.post("/auth/signup", response_model=TokenOut, tags=["auth"])
def signup(payload: UserCreate):
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (payload.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        initials = "".join([w[0] for w in payload.name.split()[:2]]).upper()
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, avatar_initials, phone, location, company, job_title, team, about, verified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
            (
                payload.name, payload.email, hash_password(payload.password), payload.role,
                initials, payload.phone, payload.location, payload.company,
                payload.job_title, payload.team, payload.about,
            ),
        )
        user_id = cur.lastrowid
        token = secrets.token_hex(24)
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user_id))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return {"token": token, "user": row_to_user(row)}


@app.post("/auth/login", response_model=TokenOut, tags=["auth"])
def login(payload: UserLogin):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
        if not row or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = secrets.token_hex(24)
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, row["id"]))
        return {"token": token, "user": row_to_user(row)}


@app.post("/auth/logout", response_model=MessageOut, tags=["auth"])
def logout(user: dict = Depends(get_current_user)):
    # In a real app you'd pass the token; here we delete all sessions for the user
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
    return {"message": "Logged out"}


@app.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(user: dict = Depends(get_current_user)):
    return user


# =========================================================
# Users / Profile
# =========================================================
@app.get("/users/{user_id}", response_model=UserOut, tags=["users"])
def get_user(user_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return row_to_user(row)


@app.put("/users/me", response_model=UserOut, tags=["users"])
def update_me(
    payload: dict,
    user: dict = Depends(get_current_user),
):
    allowed = {"name", "phone", "location", "company", "job_title", "team", "about"}
    fields = {k: v for k, v in payload.items() if k in allowed}
    if not fields:
        return user
    with get_db() as conn:
        set_clause = ", ".join([f"{k} = ?" for k in fields])
        values = list(fields.values()) + [user["id"]]
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        return row_to_user(row)


# =========================================================
# Jobs
# =========================================================
@app.get("/jobs", response_model=List[JobOut], tags=["jobs"])
def list_jobs(recruiter_id: Optional[int] = None):
    with get_db() as conn:
        if recruiter_id:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE recruiter_id = ? ORDER BY created_at DESC",
                (recruiter_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


@app.post("/jobs", response_model=JobOut, tags=["jobs"])
def create_job(payload: JobCreate, user: dict = Depends(get_current_user)):
    require_role(user, "recruiter")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (recruiter_id, title, company, location, salary, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], payload.title, payload.company, payload.location, payload.salary, payload.description),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


@app.get("/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
def get_job(job_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(row)


# =========================================================
# Candidate Profiles
# =========================================================
@app.get("/profiles", response_model=List[CandidateProfileOut], tags=["profiles"])
def list_profiles(user_id: Optional[int] = None):
    with get_db() as conn:
        if user_id:
            rows = conn.execute(
                "SELECT * FROM candidate_profiles WHERE user_id = ?", (user_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM candidate_profiles").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            current = conn.execute(
                "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
                "WHERE ps.profile_id = ? AND ps.kind = 'current'",
                (r["id"],),
            ).fetchall()
            missing = conn.execute(
                "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
                "WHERE ps.profile_id = ? AND ps.kind = 'missing'",
                (r["id"],),
            ).fetchall()
            d["current_skills"] = [x["name"] for x in current]
            d["missing_skills"] = [x["name"] for x in missing]
            results.append(d)
        return results


@app.get("/profiles/me", response_model=CandidateProfileOut, tags=["profiles"])
def get_my_profile(user: dict = Depends(get_current_user)):
    require_role(user, "candidate")
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM candidate_profiles WHERE user_id = ?", (user["id"],)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found. Upload a resume first.")
        d = dict(row)
        current = conn.execute(
            "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.profile_id = ? AND ps.kind = 'current'",
            (row["id"],),
        ).fetchall()
        missing = conn.execute(
            "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.profile_id = ? AND ps.kind = 'missing'",
            (row["id"],),
        ).fetchall()
        d["current_skills"] = [x["name"] for x in current]
        d["missing_skills"] = [x["name"] for x in missing]
        return d


@app.post("/profiles/upload-resume", response_model=CandidateProfileOut, tags=["profiles"])
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a resume PDF, parse it, and create/update the candidate profile."""
    require_role(user, "candidate")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save the file
    save_path = os.path.join(UPLOAD_DIR, f"{user['id']}_{file.filename}")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Parse and ingest
    data = parse_resume_pdf(save_path)
    data["role"] = data.get("role")
    uid, pid = ingest_candidate(data)
    # Link the profile to the logged-in user
    with get_db() as conn:
        conn.execute(
            "UPDATE candidate_profiles SET user_id = ?, resume_path = ? WHERE id = ?",
            (user["id"], save_path, pid),
        )
        row = conn.execute("SELECT * FROM candidate_profiles WHERE id = ?", (pid,)).fetchone()
        d = dict(row)
        current = conn.execute(
            "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.profile_id = ? AND ps.kind = 'current'", (pid,)
        ).fetchall()
        missing = conn.execute(
            "SELECT s.name FROM profile_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.profile_id = ? AND ps.kind = 'missing'", (pid,)
        ).fetchall()
        d["current_skills"] = [x["name"] for x in current]
        d["missing_skills"] = [x["name"] for x in missing]
        return d


# =========================================================
# Applications
# =========================================================
@app.get("/applications", response_model=List[ApplicationOut], tags=["applications"])
def list_applications(candidate_id: Optional[int] = None):
    with get_db() as conn:
        if candidate_id:
            rows = conn.execute(
                "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
                "FROM applications a JOIN jobs j ON j.id = a.job_id "
                "WHERE a.candidate_id = ? ORDER BY a.applied_date DESC",
                (candidate_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
                "FROM applications a JOIN jobs j ON j.id = a.job_id "
                "ORDER BY a.applied_date DESC"
            ).fetchall()
        return [dict(r) for r in rows]


@app.get("/applications/me", response_model=List[ApplicationOut], tags=["applications"])
def list_my_applications(user: dict = Depends(get_current_user)):
    require_role(user, "candidate")
    with get_db() as conn:
        rows = conn.execute(
            "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
            "FROM applications a JOIN jobs j ON j.id = a.job_id "
            "WHERE a.candidate_id = ? ORDER BY a.applied_date DESC",
            (user["id"],),
        ).fetchall()
        return [dict(r) for r in rows]


@app.post("/applications", response_model=ApplicationOut, tags=["applications"])
def create_application(payload: ApplicationCreate, user: dict = Depends(get_current_user)):
    require_role(user, "candidate")
    with get_db() as conn:
        # Check job exists
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (payload.job_id,)).fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        # Check not already applied
        existing = conn.execute(
            "SELECT id FROM applications WHERE candidate_id = ? AND job_id = ?",
            (user["id"], payload.job_id),
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Already applied to this job")
        cur = conn.execute(
            "INSERT INTO applications (candidate_id, job_id, status, applied_date) "
            "VALUES (?, ?, 'Applied', ?)",
            (user["id"], payload.job_id, date.today().isoformat()),
        )
        row = conn.execute(
            "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
            "FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)


@app.put("/applications/{app_id}/status", response_model=ApplicationOut, tags=["applications"])
def update_application_status(app_id: int, status: str, user: dict = Depends(get_current_user)):
    valid = {"Applied", "Under Review", "Interview", "Selected", "Rejected"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")
    with get_db() as conn:
        row = conn.execute(
            "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
            "FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?",
            (app_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        row = conn.execute(
            "SELECT a.*, j.title AS job_title, j.company, j.location, j.salary "
            "FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?",
            (app_id,),
        ).fetchone()
        return dict(row)


# =========================================================
# Pipeline (Recruiter screening)
# =========================================================
@app.get("/pipeline", response_model=List[PipelineEntryOut], tags=["pipeline"])
def list_pipeline(
    job_id: Optional[int] = None,
    recruiter_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(3, ge=1, le=100),
):
    with get_db() as conn:
        query = (
            "SELECT p.*, u.name, cp.role, cp.location, cp.experience, cp.summary "
            "FROM pipeline p "
            "JOIN users u ON u.id = p.candidate_id "
            "LEFT JOIN candidate_profiles cp ON cp.id = p.profile_id "
        )
        conditions = []
        params = []
        if job_id:
            conditions.append("p.job_id = ?")
            params.append(job_id)
        if recruiter_id:
            conditions.append("p.recruiter_id = ?")
            params.append(recruiter_id)
        if conditions:
            query += "WHERE " + " AND ".join(conditions) + " "
        query += "ORDER BY p.rank ASC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["top_match"] = bool(d.get("top_match"))
            matched = conn.execute(
                "SELECT s.name FROM pipeline_skills ps JOIN skills s ON s.id = ps.skill_id "
                "WHERE ps.pipeline_id = ? AND ps.kind = 'matched'", (r["id"],)
            ).fetchall()
            missing = conn.execute(
                "SELECT s.name FROM pipeline_skills ps JOIN skills s ON s.id = ps.skill_id "
                "WHERE ps.pipeline_id = ? AND ps.kind = 'missing'", (r["id"],)
            ).fetchall()
            d["matched"] = [x["name"] for x in matched]
            d["missing"] = [x["name"] for x in missing]
            results.append(d)
        return results


@app.get("/pipeline/count", tags=["pipeline"])
def count_pipeline(job_id: Optional[int] = None, recruiter_id: Optional[int] = None):
    with get_db() as conn:
        query = "SELECT COUNT(*) AS total FROM pipeline "
        conditions = []
        params = []
        if job_id:
            conditions.append("job_id = ?")
            params.append(job_id)
        if recruiter_id:
            conditions.append("recruiter_id = ?")
            params.append(recruiter_id)
        if conditions:
            query += "WHERE " + " AND ".join(conditions)
        row = conn.execute(query, params).fetchone()
        return {"total": row["total"]}


@app.put("/pipeline/{pipeline_id}/status", response_model=PipelineEntryOut, tags=["pipeline"])
def update_pipeline_status(
    pipeline_id: int,
    payload: PipelineStatusUpdate,
    user: dict = Depends(get_current_user),
):
    require_role(user, "recruiter")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM pipeline WHERE id = ?", (pipeline_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pipeline entry not found")
        conn.execute("UPDATE pipeline SET status = ? WHERE id = ?", (payload.status, pipeline_id))

        # Log activity
        candidate = conn.execute("SELECT name FROM users WHERE id = ?", (row["candidate_id"],)).fetchone()
        action_map = {
            "shortlisted": "shortlisted",
            "selected": "selected",
            "rejected": "rejected",
        }
        if payload.status in action_map and candidate:
            conn.execute(
                "INSERT INTO activities (recruiter_id, text) VALUES (?, ?)",
                (user["id"], f"You {action_map[payload.status]} {candidate['name']}"),
            )

        # Return updated entry with joined fields
        r = conn.execute(
            "SELECT p.*, u.name, cp.role, cp.location, cp.experience, cp.summary "
            "FROM pipeline p JOIN users u ON u.id = p.candidate_id "
            "LEFT JOIN candidate_profiles cp ON cp.id = p.profile_id "
            "WHERE p.id = ?",
            (pipeline_id,),
        ).fetchone()
        d = dict(r)
        d["top_match"] = bool(d.get("top_match"))
        matched = conn.execute(
            "SELECT s.name FROM pipeline_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.pipeline_id = ? AND ps.kind = 'matched'", (pipeline_id,)
        ).fetchall()
        missing = conn.execute(
            "SELECT s.name FROM pipeline_skills ps JOIN skills s ON s.id = ps.skill_id "
            "WHERE ps.pipeline_id = ? AND ps.kind = 'missing'", (pipeline_id,)
        ).fetchall()
        d["matched"] = [x["name"] for x in matched]
        d["missing"] = [x["name"] for x in missing]
        return d


@app.post("/pipeline/ingest-pdf", tags=["pipeline"])
async def ingest_pdf_to_pipeline(
    job_id: int = Query(...),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a candidate resume PDF and add them to the recruiter's pipeline for a job."""
    require_role(user, "recruiter")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    save_path = os.path.join(UPLOAD_DIR, f"pipeline_{file.filename}")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    uid, pid = ingest_pdf(save_path, recruiter_id=user["id"], job_id=job_id)
    return {"message": "Candidate ingested into pipeline", "user_id": uid, "profile_id": pid}


# =========================================================
# Stats (Recruiter dashboard)
# =========================================================
@app.get("/stats", response_model=StatsOut, tags=["stats"])
def get_stats(recruiter_id: Optional[int] = None, job_id: Optional[int] = None):
    with get_db() as conn:
        conditions = []
        params = []
        if recruiter_id:
            conditions.append("recruiter_id = ?")
            params.append(recruiter_id)
        if job_id:
            conditions.append("job_id = ?")
            params.append(job_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        total = conn.execute(f"SELECT COUNT(*) AS c FROM pipeline {where}", params).fetchone()["c"]
        shortlisted = conn.execute(
            f"SELECT COUNT(*) AS c FROM pipeline {where} "
            + ("AND " if conditions else "WHERE ") + "status = 'shortlisted'",
            params,
        ).fetchone()["c"]
        selected = conn.execute(
            f"SELECT COUNT(*) AS c FROM pipeline {where} "
            + ("AND " if conditions else "WHERE ") + "status = 'selected'",
            params,
        ).fetchone()["c"]
        rejected = conn.execute(
            f"SELECT COUNT(*) AS c FROM pipeline {where} "
            + ("AND " if conditions else "WHERE ") + "status = 'rejected'",
            params,
        ).fetchone()["c"]
        return {
            "total_resumes": total,
            "shortlisted": shortlisted,
            "selected": selected,
            "rejected": rejected,
        }


# =========================================================
# Activities
# =========================================================
@app.get("/activities", response_model=List[ActivityOut], tags=["activities"])
def list_activities(recruiter_id: Optional[int] = None, limit: int = Query(20, ge=1, le=100)):
    with get_db() as conn:
        if recruiter_id:
            rows = conn.execute(
                "SELECT * FROM activities WHERE recruiter_id = ? ORDER BY created_at DESC LIMIT ?",
                (recruiter_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM activities ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


# =========================================================
# Startup
# =========================================================
@app.on_event("startup")
def startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
