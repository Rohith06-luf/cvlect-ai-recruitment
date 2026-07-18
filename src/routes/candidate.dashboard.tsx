import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useMemo, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  BarChart3,
  Settings,
  Upload,
  ExternalLink,
  CheckCircle,
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

type SectionId = "dashboard" | "applications" | "resume" | "skill-gap" | "jobs" | "settings";

const items: SidebarItem[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "applications", label: "Applications", icon: Briefcase },
  { id: "jobs", label: "Browse Jobs", icon: Briefcase },
  { id: "resume", label: "Resume", icon: FileText },
  { id: "skill-gap", label: "Skill Gap", icon: BarChart3 },
  { id: "settings", label: "Settings", icon: Settings },
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
            {section === "jobs" && <JobsSection profile={profile} applications={applications ?? []} />}
            {section === "resume" && <ResumeSection profile={profile} />}
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
  const [expandedId, setExpandedId] = useState<string | number | null>(null);
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "applied":
        return "text-[var(--color-secondary)]";
      case "interview":
        return "text-[var(--color-success)]";
      case "shortlisted":
        return "text-[var(--color-success)]";
      case "under review":
        return "text-[var(--color-warning)]";
      case "rejected":
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
                      {typeof job.score === "number" && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--color-secondary)]/20 text-[var(--color-secondary)]">
                          Score: {job.score}%
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{job.company} · {job.location}</p>
                    <p className="text-xs text-muted-foreground mt-1">Applied: {job.applied_date}</p>
                    {job.reason && <p className="text-xs text-muted-foreground mt-1 italic">{job.reason}</p>}

                    {/* Matched / Missing skills inline */}
                    {(job.matched_skills?.length || job.missing_skills?.length) ? (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {job.matched_skills?.map(s => (
                          <span key={s} className="text-[10px] rounded-full bg-[var(--color-success)]/10 text-[var(--color-success)] px-2 py-0.5 border border-[var(--color-success)]/20">{s}</span>
                        ))}
                        {job.missing_skills?.map(s => (
                          <span key={s} className="text-[10px] rounded-full bg-[var(--color-warning)]/10 text-[var(--color-warning)] px-2 py-0.5 border border-[var(--color-warning)]/20">{s}</span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => setExpandedId(expandedId === job.id ? null : job.id)}
                      className="rounded-lg border border-border px-3 py-2 text-xs font-medium hover:bg-white/5 transition"
                    >
                      {expandedId === job.id ? "Hide" : "Suggestions"}
                    </button>
                  </div>
                </div>

                {/* Expandable suggestions panel */}
                {expandedId === job.id && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4 pt-4 border-t border-border space-y-4">
                    {job.missing_keywords && job.missing_keywords.length > 0 && (
                      <SuggestionBlock title="Missing Keywords" items={job.missing_keywords} color="var(--color-warning)" />
                    )}
                    {job.recommended_projects && job.recommended_projects.length > 0 && (
                      <SuggestionBlock title="Recommended Projects" items={job.recommended_projects} color="var(--color-secondary)" />
                    )}
                    {job.recommended_certs && job.recommended_certs.length > 0 && (
                      <SuggestionBlock title="Recommended Certifications" items={job.recommended_certs} color="var(--color-highlight)" />
                    )}
                    {job.ats_improvements && job.ats_improvements.length > 0 && (
                      <SuggestionBlock title="ATS Improvements" items={job.ats_improvements} color="var(--color-primary)" />
                    )}
                    {job.grammar_suggestions && job.grammar_suggestions.length > 0 && (
                      <SuggestionBlock title="Grammar Suggestions" items={job.grammar_suggestions} color="var(--color-success)" />
                    )}
                    {job.formatting_suggestions && job.formatting_suggestions.length > 0 && (
                      <SuggestionBlock title="Formatting Suggestions" items={job.formatting_suggestions} color="var(--color-error)" />
                    )}
                    {job.recommended_courses && job.recommended_courses.length > 0 && (
                      <SuggestionBlock title="Recommended Courses" items={job.recommended_courses} color="var(--color-secondary)" />
                    )}
                    {(!job.missing_keywords?.length && !job.recommended_projects?.length && !job.ats_improvements?.length && !job.grammar_suggestions?.length && !job.formatting_suggestions?.length) && (
                      <p className="text-xs text-muted-foreground">No suggestions available yet — suggestions will appear after resume analysis.</p>
                    )}
                  </motion.div>
                )}
              </div>
            ))
          )}
        </div>
      </GlassCard>
    </>
  );
}

function SuggestionBlock({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider font-semibold mb-2" style={{ color }}>{title}</div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-muted-foreground flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 rounded-full shrink-0" style={{ background: color }} />
            {item}
          </li>
        ))}
      </ul>
    </div>
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

function JobsSection({ profile, applications }: { profile?: CandidateProfile; applications: Application[] }) {
  const queryClient = useQueryClient();
  const [pendingUploadJobId, setPendingUploadJobId] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(),
    retry: false,
  });

  const appliedJobIds = new Set((applications ?? []).map((app) => app.job_id));

  const applyMutation = useMutation({
    mutationFn: async (jobId: number) => api.createApplication(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-applications"] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      window.alert("Application submitted successfully.");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to apply";
      window.alert(message);
    },
  });

  const uploadAndApply = async (jobId: number, file: File) => {
    setUploadError(null);
    try {
      await api.uploadResume(file);
      await api.createApplication(jobId);
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
      queryClient.invalidateQueries({ queryKey: ["my-applications"] });
      window.alert("Resume uploaded and application submitted successfully.");
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload or apply failed");
    } finally {
      setPendingUploadJobId(null);
    }
  };

  const handleApply = (jobId: number) => {
    if (appliedJobIds.has(jobId)) {
      window.alert("You have already applied to this job.");
      return;
    }

    if (!profile?.resume_path) {
      const shouldUpload = window.confirm("You do not have a resume uploaded. Would you like to upload one now to apply?");
      if (shouldUpload) {
        setPendingUploadJobId(jobId);
        inputRef.current?.click();
      }
      return;
    }

    const useCurrent = window.confirm("Use your current resume for this application? Click OK to use current resume, or Cancel to upload a new one.");
    if (!useCurrent) {
      setPendingUploadJobId(jobId);
      inputRef.current?.click();
      return;
    }

    applyMutation.mutate(jobId);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || pendingUploadJobId === null) return;
    await uploadAndApply(pendingUploadJobId, file);
    e.target.value = "";
  };

  return (
    <GlassCard className="p-6">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        className="hidden"
        onChange={handleFileChange}
      />
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Browse Jobs</h2>
        <span className="text-xs text-muted-foreground">{jobs?.length ?? 0} opportunities</span>
      </div>
      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading jobs…</div>
      ) : error ? (
        <div className="text-sm text-danger">Failed to load jobs.</div>
      ) : jobs && jobs.length > 0 ? (
        <div className="space-y-4">
          {jobs.map((job) => {
            const isApplied = appliedJobIds.has(job.id);
            return (
              <div key={job.id} className="rounded-xl border border-border bg-white/[0.03] p-5 hover:bg-white/[0.06] transition">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">{job.title}</h3>
                      <span className="text-xs font-medium px-2 py-1 rounded-full bg-[var(--color-secondary)]/20 text-[var(--color-secondary)]">
                        {job.status ?? "Active"}
                      </span>
                      {isApplied && (
                        <span className="text-xs font-medium px-2 py-1 rounded-full bg-[var(--color-success)]/20 text-[var(--color-success)]">
                          Applied
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">{job.company} · {job.location ?? "Remote"}</p>
                    {job.salary && <p className="text-sm font-medium text-[var(--color-warning)] mb-2">{job.salary}</p>}
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{job.description ?? "No description available."}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleApply(job.id)}
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
      ) : (
        <div className="text-sm text-muted-foreground">No open jobs found.</div>
      )}
      {uploadError && <div className="mt-4 text-sm text-[var(--color-error)]">{uploadError}</div>}
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
