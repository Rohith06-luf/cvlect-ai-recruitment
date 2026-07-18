"""
Seed the database with data matching the frontend mock data.

Run:  python seed.py
"""
import hashlib
import secrets
from db import init_db, get_db


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_or_create_skill(conn, name: str) -> int:
    row = conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO skills (name) VALUES (?)", (name,))
    return cur.lastrowid


def seed():
    init_db()

    with get_db() as conn:
        # ---------- Users ----------
        # Recruiter: Alex Reed (matches recruiter.profile.tsx)
        recruiter = conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role, avatar_initials, phone, location, company, job_title, team, about, verified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Alex Reed",
                "alex.reed@cvlect.com",
                hash_password("recruiter123"),
                "recruiter",
                "AR",
                "+1 (415) 555-0142",
                "San Francisco, CA",
                "CVlect Inc.",
                "Senior Recruiter",
                "Engineering Talent",
                "Recruiter focused on senior engineering hiring. Passionate about transparent, "
                "bias-aware screening and giving every candidate meaningful feedback.",
                1,
            ),
        )
        recruiter_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("alex.reed@cvlect.com",)
        ).fetchone()["id"]

        # Candidate: Priya Sharma (matches candidate.dashboard.tsx)
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, role, avatar_initials, phone, location, about, verified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "Priya Sharma",
                "priya.sharma@example.com",
                hash_password("candidate123"),
                "candidate",
                "PS",
                "+91 98765 43210",
                "Bengaluru, IN",
                "Product-focused engineer with deep React + design systems experience.",
                1,
            ),
        )
        priya_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("priya.sharma@example.com",)
        ).fetchone()["id"]

        # Pipeline candidates (match recruiter.dashboard.tsx baseCandidates)
        pipeline_candidates = [
            {
                "name": "Priya Sharma",
                "email": "priya.sharma@example.com",
                "role": "Senior Frontend Engineer",
                "location": "Bengaluru, IN",
                "experience": "6 yrs",
                "score": 94,
                "summary": "Product-focused engineer with deep React + design systems experience across two YC startups.",
                "reason": "Strong React, TypeScript, design system authorship; ships accessible, tested UI.",
                "matched": ["React", "TypeScript", "Design Systems", "Accessibility"],
                "missing": ["GraphQL"],
            },
            {
                "name": "Marcus Weiss",
                "email": "marcus.weiss@example.com",
                "role": "Frontend Engineer",
                "location": "Berlin, DE",
                "experience": "4 yrs",
                "score": 88,
                "summary": "Performance-obsessed engineer, contributed to core web vitals improvements at a fintech.",
                "reason": "Solid React, strong performance work, modest testing coverage on prior repos.",
                "matched": ["React", "TypeScript", "Performance"],
                "missing": ["Design Systems", "Testing"],
            },
            {
                "name": "Amelia Chen",
                "email": "amelia.chen@example.com",
                "role": "Full-stack Engineer",
                "location": "Toronto, CA",
                "experience": "5 yrs",
                "score": 82,
                "summary": "Full-stack engineer with Node + React, led a small platform team of three.",
                "reason": "Good breadth; frontend depth is lighter than the top match.",
                "matched": ["React", "Node.js", "TypeScript"],
                "missing": ["Design Systems", "Accessibility"],
            },
        ]

        # Create candidate users for pipeline (if not exist)
        for c in pipeline_candidates:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash, role, avatar_initials, location) "
                "VALUES (?, ?, ?, 'candidate', ?, ?)",
                (
                    c["name"],
                    c["email"],
                    hash_password("candidate123"),
                    "".join([w[0] for w in c["name"].split()[:2]]),
                    c["location"],
                ),
            )

        # ---------- Jobs ----------
        jobs_data = [
            {
                "title": "Senior Frontend Engineer",
                "company": "CVlect Inc.",
                "location": "Remote",
                "salary": "$150K - $200K",
                "description": "Senior Frontend Engineer — React, TypeScript, design systems, accessibility. "
                "Ship product surfaces with a small, senior team.",
            },
            # Jobs matching candidate.dashboard.tsx enrolledJobs
            {"title": "Senior Product Engineer", "company": "Linear", "location": "Remote", "salary": "$150K - $200K", "description": "Senior product engineer role."},
            {"title": "Frontend Platform Engineer", "company": "Vercel", "location": "New York", "salary": "$140K - $180K", "description": "Frontend platform role."},
            {"title": "UI Engineer, Dashboard", "company": "Stripe", "location": "London", "salary": "$130K - $170K", "description": "UI engineer for dashboard surfaces."},
            {"title": "Product Engineer", "company": "Figma", "location": "San Francisco", "salary": "$160K - $210K", "description": "Product engineer role."},
            {"title": "Frontend Engineer", "company": "GitHub", "location": "Remote", "salary": "$145K - $195K", "description": "Frontend engineer role."},
        ]

        job_ids = []
        for j in jobs_data:
            existing = conn.execute(
                "SELECT id FROM jobs WHERE title = ? AND company = ?", (j["title"], j["company"])
            ).fetchone()
            if existing:
                job_ids.append(existing["id"])
            else:
                cur = conn.execute(
                    "INSERT INTO jobs (recruiter_id, title, company, location, salary, description) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (recruiter_id, j["title"], j["company"], j["location"], j["salary"], j["description"]),
                )
                job_ids.append(cur.lastrowid)

        main_job_id = job_ids[0]  # Senior Frontend Engineer

        # ---------- Candidate Profiles ----------
        for c in pipeline_candidates:
            user_row = conn.execute(
                "SELECT id FROM users WHERE email = ?", (c["email"],)
            ).fetchone()
            if not user_row:
                continue
            uid = user_row["id"]

            existing_profile = conn.execute(
                "SELECT id FROM candidate_profiles WHERE user_id = ?", (uid,)
            ).fetchone()
            if existing_profile:
                pid = existing_profile["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO candidate_profiles (user_id, full_name, role, location, experience, summary, "
                    "resume_score, ats_score, keywords_score, experience_match, projects_score, "
                    "education_score, achievements_score, career_health) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        uid,
                        c["name"],
                        c["role"],
                        c["location"],
                        c["experience"],
                        c["summary"],
                        c["score"],
                        min(100, c["score"] + 4),
                        max(0, c["score"] - 7),
                        min(100, c["score"] - 4),
                        max(0, c["score"] - 10),
                        max(0, c["score"] - 16),
                        max(0, c["score"] - 22),
                        92 if c["name"] == "Priya Sharma" else 80,
                    ),
                )
                pid = cur.lastrowid

            # Insert skills
            for s in c["matched"]:
                sid = get_or_create_skill(conn, s)
                conn.execute(
                    "INSERT OR IGNORE INTO profile_skills (profile_id, skill_id, kind) VALUES (?, ?, 'current')",
                    (pid, sid),
                )
            for s in c["missing"]:
                sid = get_or_create_skill(conn, s)
                conn.execute(
                    "INSERT OR IGNORE INTO profile_skills (profile_id, skill_id, kind) VALUES (?, ?, 'missing')",
                    (pid, sid),
                )

        # ---------- Pipeline ----------
        for idx, c in enumerate(pipeline_candidates):
            user_row = conn.execute(
                "SELECT id FROM users WHERE email = ?", (c["email"],)
            ).fetchone()
            profile_row = conn.execute(
                "SELECT id FROM candidate_profiles WHERE user_id = ?", (user_row["id"],)
            ).fetchone()

            conn.execute(
                "INSERT OR IGNORE INTO pipeline (recruiter_id, job_id, candidate_id, profile_id, score, rank, top_match, reason, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                (
                    recruiter_id,
                    main_job_id,
                    user_row["id"],
                    profile_row["id"] if profile_row else None,
                    c["score"],
                    idx + 1,
                    1 if idx == 0 else 0,
                    c["reason"],
                ),
            )

            pipe_row = conn.execute(
                "SELECT id FROM pipeline WHERE job_id = ? AND candidate_id = ?",
                (main_job_id, user_row["id"]),
            ).fetchone()
            pipe_id = pipe_row["id"]

            for s in c["matched"]:
                sid = get_or_create_skill(conn, s)
                conn.execute(
                    "INSERT OR IGNORE INTO pipeline_skills (pipeline_id, skill_id, kind) VALUES (?, ?, 'matched')",
                    (pipe_id, sid),
                )
            for s in c["missing"]:
                sid = get_or_create_skill(conn, s)
                conn.execute(
                    "INSERT OR IGNORE INTO pipeline_skills (pipeline_id, skill_id, kind) VALUES (?, ?, 'missing')",
                    (pipe_id, sid),
                )

        # ---------- Applications (Priya's enrolled jobs) ----------
        enrolled = [
            (job_ids[1], "Applied", "2024-01-15"),   # Linear
            (job_ids[2], "Interview", "2024-01-10"), # Vercel
            (job_ids[3], "Under Review", "2024-01-08"), # Stripe
            (job_ids[4], "Applied", "2024-01-05"),   # Figma
            (job_ids[5], "Rejected", "2023-12-28"),  # GitHub
        ]
        for jid, status, applied in enrolled:
            conn.execute(
                "INSERT OR IGNORE INTO applications (candidate_id, job_id, status, applied_date) "
                "VALUES (?, ?, ?, ?)",
                (priya_id, jid, status, applied),
            )

        # ---------- Activities ----------
        activities = [
            "You shortlisted Priya Sharma",
            "AI re-ranked 12 candidates for Senior Frontend Engineer",
            "Marcus Weiss submitted a new resume",
            "You rejected 4 candidates from the pipeline",
        ]
        for text in activities:
            conn.execute(
                "INSERT INTO activities (recruiter_id, text) VALUES (?, ?)",
                (recruiter_id, text),
            )

    print("[seed] Database seeded successfully.")
    print("       Recruiter login:  alex.reed@cvlect.com / recruiter123")
    print("       Candidate login:  priya.sharma@example.com / candidate123")


if __name__ == "__main__":
    seed()
