"""
SQLite3 database connection and schema initialization for CVlect backend.
"""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cvlect.db")


def get_connection():
    """Return a sqlite3 connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db():
    """Context manager that yields a connection and commits/closes automatically."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
-- =========================================================
-- USERS (recruiters and candidates share this table)
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('recruiter', 'candidate')),
    avatar_initials TEXT,
    phone           TEXT,
    location        TEXT,
    company         TEXT,
    job_title       TEXT,
    team            TEXT,
    about           TEXT,
    verified        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================================
-- JOBS (posted by recruiters)
-- =========================================================
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    company       TEXT NOT NULL,
    location      TEXT,
    salary         TEXT,
    description   TEXT,
    status        TEXT NOT NULL DEFAULT 'open',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================================
-- CANDIDATE PROFILES (resume-derived data)
-- =========================================================
CREATE TABLE IF NOT EXISTS candidate_profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name       TEXT NOT NULL,
    role            TEXT,
    location        TEXT,
    experience      TEXT,
    summary         TEXT,
    resume_path     TEXT,
    resume_score    INTEGER DEFAULT 0,
    ats_score       INTEGER DEFAULT 0,
    keywords_score  INTEGER DEFAULT 0,
    experience_match INTEGER DEFAULT 0,
    projects_score  INTEGER DEFAULT 0,
    education_score INTEGER DEFAULT 0,
    achievements_score INTEGER DEFAULT 0,
    career_health   INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================================
-- SKILLS (master list) + profile skills (current/missing)
-- =========================================================
CREATE TABLE IF NOT EXISTS skills (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS profile_skills (
    profile_id  INTEGER NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    skill_id    INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('current', 'missing')),
    PRIMARY KEY (profile_id, skill_id, kind)
);

-- =========================================================
-- APPLICATIONS (candidate applies to a job)
-- =========================================================
CREATE TABLE IF NOT EXISTS applications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id        INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'Applied'
                  CHECK (status IN ('Applied', 'Under Review', 'Interview', 'Selected', 'Rejected')),
    applied_date  TEXT NOT NULL DEFAULT (date('now')),
    UNIQUE (candidate_id, job_id)
);

-- =========================================================
-- PIPELINE (recruiter's screening pipeline for a job)
-- holds ranked candidates with AI score, reason, matched/missing skills
-- =========================================================
CREATE TABLE IF NOT EXISTS pipeline (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id        INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id    INTEGER REFERENCES candidate_profiles(id) ON DELETE SET NULL,
    score         INTEGER NOT NULL DEFAULT 0,
    rank          INTEGER NOT NULL DEFAULT 0,
    top_match     INTEGER NOT NULL DEFAULT 0,
    reason        TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'shortlisted', 'selected', 'rejected')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (job_id, candidate_id)
);

-- =========================================================
-- PIPELINE SKILLS (matched / missing per pipeline entry)
-- =========================================================
CREATE TABLE IF NOT EXISTS pipeline_skills (
    pipeline_id  INTEGER NOT NULL REFERENCES pipeline(id) ON DELETE CASCADE,
    skill_id     INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    kind         TEXT NOT NULL CHECK (kind IN ('matched', 'missing')),
    PRIMARY KEY (pipeline_id, skill_id, kind)
);

-- =========================================================
-- ACTIVITIES (audit log of recruiter actions)
-- =========================================================
CREATE TABLE IF NOT EXISTS activities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text         TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================================
-- SESSIONS (simple token -> user map for auth)
-- =========================================================
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db():
    """Create all tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)
    print(f"[db] Initialized database at {DB_PATH}")


def reset_db():
    """Drop and recreate all tables (use with caution)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


if __name__ == "__main__":
    init_db()
