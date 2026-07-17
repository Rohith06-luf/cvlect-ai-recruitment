import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  Gauge,
  Briefcase,
  BarChart3,
  Settings,
  Upload,
  Send,
  Sparkles,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { ProgressRing } from "@/components/ProgressRing";
import { api, type CandidateProfile, type Application } from "@/lib/api";

export const Route = createFileRoute("/candidate/dashboard")({
  head: () => ({ meta: [{ title: "Candidate Dashboard — CVlect" }] }),
  component: CandidateDashboard,
});

type SectionId = "dashboard" | "applications" | "resume" | "resume-score" | "skill-gap" | "settings";

const items: SidebarItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "applications", label: "Applications", icon: Briefcase },
  { id: "resume", label: "Resume", icon: FileText },
  { id: "resume-score", label: "AI Resume Score", icon: Gauge },
  { id: "skill-gap", label: "Skill Gap", icon: BarChart3 },
  { id: "settings", label: "Settings", icon: Settings },
];

const jobs = [
  { company: "Linear", role: "Senior Product Engineer", location: "Remote", match: 96 },
  { company: "Vercel", role: "Frontend Platform Engineer", location: "New York", match: 91 },
  { company: "Stripe", role: "UI Engineer, Dashboard", location: "London", match: 87 },
];

const timeline = [
  { label: "Applied", tone: "muted" as const },
  { label: "Under Review", tone: "muted" as const },
  { label: "Interview", tone: "active" as const },
  { label: "Selected", tone: "idle" as const },
  { label: "Rejected", tone: "idle" as const },
];

function CandidateDashboard() {
  const [section, setSection] = useState<SectionId>("dashboard");

  // Fetch candidate profile (for the logged-in user)
  const { data: profile } = useQuery({
    queryKey: ["my-profile"],
    queryFn: () => api.getMyProfile(),
  });

  // Fetch applications
  const { data: applications } = useQuery({
    queryKey: ["my-applications"],
    queryFn: () => api.listMyApplications(),
  });

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar
        items={items}
        activeId={section}
        onSelect={(id) => setSection(id as SectionId)}
      />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="Candidate Dashboard" subtitle="Your applications, insights and career health" profileTo="/candidate/profile" />

        <main className="p-6 space-y-6 pb-32">
          <motion.div
            key={section}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {section === "dashboard" && <DashboardSection profile={profile} />}
            {section === "applications" && <ApplicationsSection applications={applications ?? []} />}
            {section === "resume" && <ResumeSection profile={profile} />}
            {section === "resume-score" && <ResumeScoreSection profile={profile} />}
            {section === "skill-gap" && <SkillGapSection profile={profile} />}
            {section === "settings" && <SettingsSection />}
          </motion.div>
        </main>
      </div>
    </div>
  );
}

/* ---------- Sections ---------- */

function DashboardSection({ profile }: { profile?: CandidateProfile }) {
  const name = profile?.full_name ?? "Priya Sharma";
  const careerHealth = profile?.career_health ?? 92;
  const resumeScore = profile?.resume_score ?? 88;
  const applicationsCount = 24; // Could come from API
  const shortlistedCount = 7;
  const interviewsCount = 3;

  return (
    <>
      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <GlassCard className="p-8 relative overflow-hidden">
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full blur-3xl opacity-40" style={{ background: "radial-gradient(closest-side, rgba(168,182,232,0.4), transparent)" }} />
          <div className="relative flex items-center justify-between gap-6 flex-wrap">
            <div className="min-w-0">
              <div className="text-xs uppercase tracking-wider text-muted-foreground">Welcome back</div>
              <h2 className="mt-1 text-3xl font-semibold tracking-tight">{name}</h2>
              <p className="mt-2 text-sm text-muted-foreground max-w-md">
                Your career health is trending up. Three new roles matched your profile this week.
              </p>
            </div>
            <div className="flex items-center gap-4">
              <ProgressRing value={careerHealth} size={92} label="Career" />
              <div className="text-xs text-muted-foreground max-w-[140px]">
                Career Health Score<br />
                <span className="text-white font-semibold text-sm">{careerHealth}/100</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Resume Score", value: resumeScore },
          { label: "Applications", value: applicationsCount },
          { label: "Shortlisted", value: shortlistedCount },
          { label: "Interviews", value: interviewsCount },
        ].map((s) => (
          <GlassCard key={s.label} hover className="p-5 flex items-center gap-4">
            <ProgressRing value={typeof s.value === "number" && s.value > 100 ? 100 : s.value} size={56} />
            <div>
              <div className="text-2xl font-semibold">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </div>
          </GlassCard>
        ))}
      </div>
    </>
  );
}

function ApplicationsSection({ applications }: { applications: Application[] }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "Applied":
        return "text-[var(--color-secondary)]";
      case "Interview":
        return "text-[var(--color-success)]";
      case "Under Review":
        return "text-[var(--color-warning)]";
      case "Rejected":
        return "text-[var(--color-error)]";
      default:
        return "text-muted-foreground";
    }
  };

  return (
    <>
      <GlassCard className="p-6">
        <h2 className="text-lg font-semibold mb-4">Enrolled Jobs</h2>
        <div className="space-y-4">
          {applications.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No applications yet. Browse jobs and apply!
            </div>
          ) : (
            applications.map((job) => (
              <div key={job.id} className="rounded-xl border border-border bg-white/[0.03] p-4 hover:bg-white/[0.06] transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h3 className="font-semibold">{job.job_title ?? "Unknown Role"}</h3>
                      <span className={`text-xs font-medium ${getStatusColor(job.status)}`}>{job.status}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{job.company} · {job.location}</p>
                    <p className="text-xs text-muted-foreground mt-1">Applied: {job.applied_date}</p>
                    <p className="text-sm font-medium mt-2">{job.salary}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium hover:bg-white/5 transition">
                      View
                    </button>
                    <button className="rounded-lg border border-border px-3 py-2 text-xs font-medium hover:bg-white/5 transition">
                      Details
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </GlassCard>
    </>
  );
}

function ResumeSection({ profile }: { profile?: CandidateProfile }) {
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await api.uploadResume(file);
      window.location.reload();
    } catch (err) {
      console.error("Upload failed:", err);
      alert("Failed to upload resume");
    }
  };

  return (
    <>
      {/* Two column: Upload + AI Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <GlassCard className="p-6 lg:col-span-2">
          <div className="text-sm font-semibold">Upload Resume</div>
          <div className="mt-4 rounded-xl border border-dashed border-border bg-white/[0.02] p-8 text-center">
            <input type="file" accept=".pdf,.doc,.docx" onChange={handleUpload} className="hidden" id="resume-upload" />
            <label htmlFor="resume-upload" className="cursor-pointer">
              <div className="mx-auto h-11 w-11 rounded-xl bg-white/5 grid place-items-center">
                <Upload className="h-5 w-5 text-[var(--color-secondary)]" />
              </div>
              <div className="mt-3 text-sm">Drag & drop your resume</div>
              <div className="mt-1 text-xs text-muted-foreground">PDF or DOCX · up to 5MB</div>
              <button type="button" onClick={() => document.getElementById("resume-upload")?.click()} className="btn-glow mt-4 rounded-xl bg-[var(--color-primary)] px-4 py-2 text-xs font-medium">
                Choose file
              </button>
            </label>
          </div>

          {profile && (
            <div className="mt-4 rounded-xl border border-border bg-white/[0.03] p-4 flex items-center gap-3">
              <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium truncate">{profile.full_name}_Resume.pdf</div>
                <div className="text-[11px] text-muted-foreground">Uploaded · AI score {profile.resume_score}</div>
                <div className="mt-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${profile.resume_score}%`, background: "var(--color-secondary)" }} />
                </div>
              </div>
            </div>
          )}
        </GlassCard>
        <GlassCard className="p-6 lg:col-span-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">AI Resume Analysis</div>
            <button className="text-xs text-[var(--color-highlight)] hover:underline">Improve resume →</button>
          </div>
          <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-5">
            <MetricRing label="Overall" value={profile?.resume_score ?? 88} />
            <MetricRing label="ATS" value={profile?.ats_score ?? 92} />
            <MetricRing label="Keywords" value={profile?.keywords_score ?? 81} />
          </div>

          <div className="mt-5 space-y-3">
            {[
              { label: "Experience Match", value: profile?.experience_match ?? 90 },
              { label: "Projects", value: profile?.projects_score ?? 84 },
              { label: "Education", value: profile?.education_score ?? 78 },
              { label: "Achievements", value: profile?.achievements_score ?? 72 },
            ].map((r) => (
              <div key={r.label}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{r.label}</span>
                  <span>{r.value}%</span>
                </div>
                <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${r.value}%`, background: "var(--color-secondary)" }} />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </>
  );
}

function ResumeScoreSection({ profile }: { profile?: CandidateProfile }) {
  return (
    <GlassCard className="p-6">
      <h2 className="text-lg font-semibold mb-4">AI Resume Score</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-5 mb-6">
        <MetricRing label="Overall" value={profile?.resume_score ?? 88} />
        <MetricRing label="ATS" value={profile?.ats_score ?? 92} />
        <MetricRing label="Keywords" value={profile?.keywords_score ?? 81} />
      </div>

      <div className="space-y-3">
        {[
          { label: "Experience Match", value: profile?.experience_match ?? 90 },
          { label: "Projects", value: profile?.projects_score ?? 84 },
          { label: "Education", value: profile?.education_score ?? 78 },
          { label: "Achievements", value: profile?.achievements_score ?? 72 },
        ].map((r) => (
          <div key={r.label}>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{r.label}</span>
              <span>{r.value}%</span>
            </div>
            <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${r.value}%`, background: "var(--color-secondary)" }} />
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function SkillGapSection({ profile }: { profile?: CandidateProfile }) {
  const currentSkills = profile?.current_skills ?? ["React", "TypeScript", "Node.js", "Testing", "Design Systems"];
  const missingSkills = profile?.missing_skills ?? ["GraphQL", "Rust", "System Design"];

  return (
    <GlassCard className="p-6">
      <div className="text-sm font-semibold">Skill Gap</div>
      <div className="mt-4">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Current Skills</div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {currentSkills.map((s) => (
            <span key={s} className="rounded-full px-2.5 py-1 text-[11px] bg-white/5 border border-white/5">
              {s}
            </span>
          ))}
        </div>
      </div>
      <div className="mt-4">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Missing Skills</div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {missingSkills.map((s) => (
            <span key={s} className="rounded-full px-2.5 py-1 text-[11px]" style={{ background: "color-mix(in oklab, var(--color-warning) 15%, transparent)", color: "var(--color-warning)" }}>
              {s}
            </span>
          ))}
        </div>
      </div>
      <div className="mt-5 space-y-2">
        {[{ n: "GraphQL Fundamentals", v: 20 }, { n: "System Design Deep Dive", v: 55 }].map((c) => (
          <div key={c.n}>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">{c.n}</span>
              <span>{c.v}%</span>
            </div>
            <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${c.v}%`, background: "var(--color-secondary)" }} />
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function SettingsSection() {
  return (
    <GlassCard className="p-6">
      <h2 className="text-lg font-semibold">Settings</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Notifications, integrations, and workspace preferences will live here.
      </p>
    </GlassCard>
  );
}

function MetricRing({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <ProgressRing value={value} size={80} />
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
