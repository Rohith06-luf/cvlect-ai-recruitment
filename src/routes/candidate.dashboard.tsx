import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  ExternalLink,
  CheckCircle,
  Clock,
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

type SectionId = "dashboard" | "applications" | "resume" | "resume-score" | "skill-gap" | "jobs" | "settings";

const items: SidebarItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "applications", label: "Applications", icon: Briefcase },
  { id: "jobs", label: "Browse Jobs", icon: Briefcase },
  { id: "resume", label: "Resume", icon: FileText },
  { id: "resume-score", label: "AI Resume Score", icon: Gauge },
  { id: "skill-gap", label: "Skill Gap", icon: BarChart3 },
  { id: "settings", label: "Settings", icon: Settings },
];

// Fake India job listings for candidates to browse and apply
const fakeIndiaJobs = [
  { id: "job-1", company: "TCS", role: "Senior Software Engineer", location: "Mumbai, Maharashtra", salary: "₹18-25 LPA", description: "Looking for experienced Java/Spring Boot developers to work on enterprise banking applications. 5+ years experience required.", match: 92, skills: ["Java", "Spring Boot", "Microservices", "AWS", "PostgreSQL"] },
  { id: "job-2", company: "Infosys", role: "Full Stack Developer", location: "Bangalore, Karnataka", salary: "₹12-18 LPA", description: "React/Node.js developer needed for digital transformation projects. Strong frontend skills with modern React patterns.", match: 88, skills: ["React", "Node.js", "TypeScript", "MongoDB", "Docker"] },
  { id: "job-3", company: "Wipro", role: "DevOps Engineer", location: "Hyderabad, Telangana", salary: "₹15-22 LPA", description: "Cloud infrastructure automation role. Experience with Kubernetes, CI/CD pipelines, and AWS/GCP required.", match: 85, skills: ["Kubernetes", "Docker", "AWS", "Terraform", "Jenkins", "Python"] },
  { id: "job-4", company: "HCL Technologies", role: "Data Scientist", location: "Pune, Maharashtra", salary: "₹20-30 LPA", description: "ML/AI role focusing on predictive analytics for retail clients. Strong Python, TensorFlow/PyTorch experience needed.", match: 90, skills: ["Python", "TensorFlow", "PyTorch", "SQL", "Pandas", "Scikit-learn"] },
  { id: "job-5", company: "Tech Mahindra", role: "Backend Developer (Go)", location: "Chennai, Tamil Nadu", salary: "₹14-20 LPA", description: "High-performance backend services using Go. Experience with gRPC, distributed systems, and PostgreSQL.", match: 87, skills: ["Go", "gRPC", "PostgreSQL", "Redis", "Docker", "Kubernetes"] },
  { id: "job-6", company: "Cognizant", role: "Frontend Architect", location: "Gurugram, Haryana", salary: "₹22-30 LPA", description: "Lead frontend architecture for large-scale applications. Expert in React, Next.js, micro-frontends, and performance optimization.", match: 89, skills: ["React", "Next.js", "TypeScript", "Micro-frontends", "Webpack", "GraphQL"] },
  { id: "job-7", company: "Capgemini", role: "Cloud Solutions Architect", location: "Noida, Uttar Pradesh", salary: "₹25-35 LPA", description: "Design and implement cloud migration strategies. AWS/Azure certified with strong architecture background.", match: 86, skills: ["AWS", "Azure", "Cloud Architecture", "Terraform", "Kubernetes", "Security"] },
  { id: "job-8", company: "Accenture", role: "AI/ML Engineer", location: "Kolkata, West Bengal", salary: "₹18-28 LPA", description: "Build and deploy ML models at scale. Experience with MLOps, feature stores, and model monitoring required.", match: 91, skills: ["Python", "MLOps", "Kubeflow", "MLflow", "Docker", "Kubernetes", "TensorFlow"] },
  { id: "job-9", company: "Zoho", role: "Product Engineer", location: "Coimbatore, Tamil Nadu", salary: "₹16-24 LPA", description: "Build SaaS products used by millions. Full-stack role with focus on clean architecture and developer experience.", match: 88, skills: ["Java", "React", "PostgreSQL", "Elasticsearch", "Kafka", "System Design"] },
  { id: "job-10", company: "Freshworks", role: "Senior Backend Engineer", location: "Chennai, Tamil Nadu", salary: "₹20-28 LPA", description: "Scale backend services for customer engagement platform. Strong in distributed systems, databases, and API design.", match: 90, skills: ["Node.js", "Go", "PostgreSQL", "Redis", "Kafka", "Microservices", "GraphQL"] },
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

  const { data: profile } = useQuery({
    queryKey: ["my-profile"],
    queryFn: () => api.getMyProfile(),
  });

  const { data: applications } = useQuery({
    queryKey: ["my-applications"],
    queryFn: () => api.listMyApplications(),
  });

  const counts = useMemo(() => {
    const visibleApps = applications ?? [];
    const shortlisted = visibleApps.filter((app) => (app.status || "").toLowerCase() === "shortlisted").length;
    const applied = visibleApps.length;
    const interviews = visibleApps.filter((app) => (app.status || "").toLowerCase() === "interview").length;
    return { applied, shortlisted, interviews };
  }, [applications]);

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
            {section === "dashboard" && <DashboardSection profile={profile} counts={counts} />}
            {section === "applications" && <ApplicationsSection applications={applications ?? []} />}
            {section === "jobs" && <JobsSection profile={profile} />}
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

function DashboardSection({ profile, counts }: { profile?: CandidateProfile; counts: { applied: number; shortlisted: number; interviews: number } }) {
  const name = profile?.full_name ?? "Your Profile";
  const careerHealth = Math.max(0, Math.min(100, profile?.career_health ?? 0));
  const resumeScore = Math.max(0, Math.min(100, profile?.resume_score ?? 0));
  const applicationsCount = counts.applied;
  const shortlistedCount = counts.shortlisted;
  const interviewsCount = counts.interviews;

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
                {profile?.summary ? profile.summary : "Your AI resume insights will update as soon as you upload a resume."}
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
                <div className="text-sm font-medium truncate">{profile.resume_path ? profile.resume_path.split(/[\\/]/).pop() : "No resume uploaded yet"}</div>
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
            <MetricRing label="Overall" value={Math.max(0, Math.min(100, profile?.resume_score ?? 0))} />
            <MetricRing label="ATS" value={Math.max(0, Math.min(100, profile?.ats_score ?? 0))} />
            <MetricRing label="Keywords" value={Math.max(0, Math.min(100, profile?.keywords_score ?? 0))} />
          </div>

          <div className="mt-5 space-y-3">
            {[
              { label: "Experience Match", value: Math.max(0, Math.min(100, profile?.experience_match ?? 0)) },
              { label: "Projects", value: Math.max(0, Math.min(100, profile?.projects_score ?? 0)) },
              { label: "Education", value: Math.max(0, Math.min(100, profile?.education_score ?? 0)) },
              { label: "Achievements", value: Math.max(0, Math.min(100, profile?.achievements_score ?? 0)) },
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
        <MetricRing label="Overall" value={Math.max(0, Math.min(100, profile?.resume_score ?? 0))} />
        <MetricRing label="ATS" value={Math.max(0, Math.min(100, profile?.ats_score ?? 0))} />
        <MetricRing label="Keywords" value={Math.max(0, Math.min(100, profile?.keywords_score ?? 0))} />
      </div>

      <div className="space-y-3">
        {[
          { label: "Experience Match", value: Math.max(0, Math.min(100, profile?.experience_match ?? 0)) },
          { label: "Projects", value: Math.max(0, Math.min(100, profile?.projects_score ?? 0)) },
          { label: "Education", value: Math.max(0, Math.min(100, profile?.education_score ?? 0)) },
          { label: "Achievements", value: Math.max(0, Math.min(100, profile?.achievements_score ?? 0)) },
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
  const currentSkills = profile?.current_skills && profile.current_skills.length > 0
    ? profile.current_skills
    : ["Upload a resume to generate skills"];
  const missingSkills = profile?.missing_skills && profile.missing_skills.length > 0
    ? profile.missing_skills
    : ["Resume insights will appear after analysis"];

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
        {(profile?.missing_skills && profile.missing_skills.length > 0 ? profile.missing_skills : ["Upload a resume to surface tailored gaps"]).map((skill) => (
          <div key={skill}>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">{skill}</span>
              <span>Focus</span>
            </div>
            <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: "60%", background: "var(--color-warning)" }} />
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

function JobsSection() {
  const queryClient = useQueryClient();
  const [appliedJobs, setAppliedJobs] = useState<Set<string>>(new Set());

  const applyMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await fetch(`/api/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!response.ok) throw new Error("Failed to apply");
      return response.json();
    },
    onSuccess: (_, jobId) => {
      setAppliedJobs(prev => new Set(prev).add(jobId));
      queryClient.invalidateQueries({ queryKey: ["my-applications"] });
    },
    onError: (error) => {
      alert(`Failed to apply: ${error.message}`);
    },
  });

  return (
    <GlassCard className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Browse Jobs (India)</h2>
        <span className="text-xs text-muted-foreground">{fakeIndiaJobs.length} opportunities</span>
      </div>
      <div className="space-y-4">
        {fakeIndiaJobs.map((job) => {
          const isApplied = appliedJobs.has(job.id);
          return (
            <div key={job.id} className="rounded-xl border border-border bg-white/[0.03] p-5 hover:bg-white/[0.06] transition">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="font-semibold text-lg">{job.role}</h3>
                    <span className="text-xs font-medium px-2 py-1 rounded-full bg-[var(--color-secondary)]/20 text-[var(--color-secondary)]">
                      {job.match}% Match
                    </span>
                    {isApplied && (
                      <span className="text-xs font-medium px-2 py-1 rounded-full bg-[var(--color-success)]/20 text-[var(--color-success)]">
                        Applied
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">{job.company} · {job.location}</p>
                  <p className="text-sm font-medium text-[var(--color-warning)] mb-2">{job.salary}</p>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{job.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {job.skills.map((skill) => (
                      <span key={skill} className="rounded-full px-2 py-0.5 text-[10px] bg-white/5 border border-white/10">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => applyMutation.mutate(job.id)}
                    disabled={isApplied || applyMutation.isPending}
                    className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
                      isApplied
                        ? "bg-[var(--color-success)]/20 text-[var(--color-success)] border border-[var(--color-success)]/30 cursor-not-allowed"
                        : "btn-glow bg-[var(--color-primary)] hover:brightness-110"
                    }`}
                  >
                    {applyMutation.isPending && applyMutation.variables === job.id ? (
                      <span className="flex items-center gap-1.5">
                        <span className="animate-spin h-3 w-3 border-2 border-current border-t-transparent rounded-full" />
                        Applying...
                      </span>
                    ) : isApplied ? (
                      <span className="flex items-center gap-1.5">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Applied
                      </span>
                    ) : (
                      "Apply Now"
                    )}
                  </button>
                  <button className="rounded-xl border border-border bg-white/[0.03] px-4 py-2 text-sm font-medium hover:bg-white/[0.06] transition">
                    <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
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
