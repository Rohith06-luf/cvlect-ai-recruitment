"""Quick verification of database contents."""
from db import get_db

with get_db() as conn:
    print("=" * 60)
    print("CANDIDATE PROFILES")
    print("=" * 60)
    rows = conn.execute(
        "SELECT id, full_name, role, location, experience, resume_score, ats_score, keywords_score FROM candidate_profiles"
    ).fetchall()
    for r in rows:
        print(f"  #{r['id']} {r['full_name']} | role={r['role']} | loc={r['location']} | exp={r['experience']} | score={r['resume_score']}")

    print()
    print("=" * 60)
    print("PIPELINE (job_id=1)")
    print("=" * 60)
    rows = conn.execute(
        "SELECT p.id, p.rank, p.score, p.status, u.name FROM pipeline p JOIN users u ON u.id=p.candidate_id WHERE p.job_id=1 ORDER BY p.rank"
    ).fetchall()
    for r in rows:
        print(f"  rank #{r['rank']} | score={r['score']} | status={r['status']} | {r['name']}")

    print()
    print("=" * 60)
    print("SKILLS PER PROFILE")
    print("=" * 60)
    rows = conn.execute(
        "SELECT cp.full_name, s.name, ps.kind FROM profile_skills ps JOIN candidate_profiles cp ON cp.id=ps.profile_id JOIN skills s ON s.id=ps.skill_id ORDER BY cp.id"
    ).fetchall()
    current_name = None
    for r in rows:
        if r["full_name"] != current_name:
            current_name = r["full_name"]
            print(f"\n  {current_name}:")
        print(f"    [{r['kind']}] {r['name']}")

    print()
    print("=" * 60)
    print("TOTALS")
    print("=" * 60)
    total_profiles = conn.execute("SELECT COUNT(*) AS c FROM candidate_profiles").fetchone()["c"]
    total_pipeline = conn.execute("SELECT COUNT(*) AS c FROM pipeline WHERE job_id=1").fetchone()["c"]
    total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    print(f"  Users: {total_users}")
    print(f"  Profiles: {total_profiles}")
    print(f"  Pipeline entries (job 1): {total_pipeline}")
