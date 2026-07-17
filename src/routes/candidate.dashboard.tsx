import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  LayoutDashboard,
  FileText,
  Gauge,
  GraduationCap,
  Briefcase,
  MessageSquare,
  BarChart3,
  Settings,
  Upload,
  Send,
  Sparkles,
  Bookmark,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { ProgressRing } from "@/components/ProgressRing";

export const Route = createFileRoute("/candidate/dashboard")({
  head: () => ({ meta: [{ title: "Candidate Dashboard — CVlect" }] }),
  component: CandidateDashboard,
});

const items: SidebarItem[] = [
  { label: "Dashboard", to: "/candidate/dashboard", icon: LayoutDashboard },
  { label: "Applications", to: "/candidate/dashboard", icon: Briefcase },
  { label: "Resume", to: "/candidate/dashboard", icon: FileText },
  { label: "AI Resume Score", to: "/candidate/dashboard", icon: Gauge },
  { label: "Skill Gap", to: "/candidate/dashboard", icon: BarChart3 },
  { label: "Recommended Jobs", to: "/candidate/dashboard", icon: Sparkles },
  { label: "Interview Prep", to: "/candidate/dashboard", icon: MessageSquare },
  { label: "Career Insights", to: "/candidate/dashboard", icon: GraduationCap },
  { label: "Settings", to: "/candidate/dashboard", icon: Settings },
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
  const [chat, setChat] = useState("");

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar items={items} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="Candidate Dashboard" subtitle="Your applications, insights and career health" />

        <main className="p-6 space-y-6 pb-32">
          {/* Hero */}
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            <GlassCard className="p-8 relative overflow-hidden">
              <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full blur-3xl opacity-40" style={{ background: "radial-gradient(closest-side, rgba(168,182,232,0.4), transparent)" }} />
              <div className="relative flex items-center justify-between gap-6 flex-wrap">
                <div className="min-w-0">
                  <div className="text-xs uppercase tracking-wider text-muted-foreground">Welcome back</div>
                  <h2 className="mt-1 text-3xl font-semibold tracking-tight">Priya Sharma</h2>
                  <p className="mt-2 text-sm text-muted-foreground max-w-md">
                    Your career health is trending up. Three new roles matched your profile this week.
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <ProgressRing value={92} size={92} label="Career" />
                  <div className="text-xs text-muted-foreground max-w-[140px]">
                    Career Health Score<br />
                    <span className="text-white font-semibold text-sm">92/100</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          </motion.div>

          {/* Statistics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Resume Score", value: 88 },
              { label: "Applications", value: 24 },
              { label: "Shortlisted", value: 7 },
              { label: "Interviews", value: 3 },
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

          {/* Two column: Upload + AI Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            <GlassCard className="p-6 lg:col-span-2">
              <div className="text-sm font-semibold">Upload Resume</div>
              <div className="mt-4 rounded-xl border border-dashed border-border bg-white/[0.02] p-8 text-center">
                <div className="mx-auto h-11 w-11 rounded-xl bg-white/5 grid place-items-center">
                  <Upload className="h-5 w-5 text-[var(--color-secondary)]" />
                </div>
                <div className="mt-3 text-sm">Drag & drop your resume</div>
                <div className="mt-1 text-xs text-muted-foreground">PDF or DOCX · up to 5MB</div>
                <button className="btn-glow mt-4 rounded-xl bg-[var(--color-primary)] px-4 py-2 text-xs font-medium">
                  Choose file
                </button>
              </div>

              <div className="mt-4 rounded-xl border border-border bg-white/[0.03] p-4 flex items-center gap-3">
                <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">Priya_Sharma_Resume.pdf</div>
                  <div className="text-[11px] text-muted-foreground">Uploaded 2 days ago · AI score 88</div>
                  <div className="mt-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: "88%", background: "var(--color-secondary)" }} />
                  </div>
                </div>
              </div>
            </GlassCard>

            <GlassCard className="p-6 lg:col-span-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold">AI Resume Analysis</div>
                <button className="text-xs text-[var(--color-highlight)] hover:underline">Improve resume →</button>
              </div>
              <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-5">
                <MetricRing label="Overall" value={88} />
                <MetricRing label="ATS" value={92} />
                <MetricRing label="Keywords" value={81} />
              </div>

              <div className="mt-5 space-y-3">
                {[
                  { label: "Experience Match", value: 90 },
                  { label: "Projects", value: 84 },
                  { label: "Education", value: 78 },
                  { label: "Achievements", value: 72 },
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

          {/* Recommended Jobs + Skill Gap */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <GlassCard className="p-6">
              <div className="text-sm font-semibold">Recommended Jobs</div>
              <div className="mt-4 space-y-3">
                {jobs.map((j) => (
                  <div key={j.company + j.role} className="rounded-xl border border-border bg-white/[0.03] p-4 flex items-center gap-4 hover:bg-white/[0.06] transition">
                    <div className="h-10 w-10 rounded-xl bg-white/8 grid place-items-center text-xs font-semibold">
                      {j.company[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{j.role}</div>
                      <div className="text-xs text-muted-foreground truncate">{j.company} · {j.location}</div>
                    </div>
                    <div className="text-xs font-medium text-[var(--color-success)]">{j.match}% match</div>
                    <div className="flex items-center gap-1.5">
                      <button className="rounded-lg border border-border p-2 hover:bg-white/5">
                        <Bookmark className="h-3.5 w-3.5" />
                      </button>
                      <button className="btn-glow rounded-lg bg-[var(--color-primary)] px-3 py-1.5 text-xs font-medium">
                        Apply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard className="p-6">
              <div className="text-sm font-semibold">Skill Gap</div>
              <div className="mt-4">
                <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Current Skills</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {["React", "TypeScript", "Node.js", "Testing", "Design Systems"].map((s) => (
                    <span key={s} className="rounded-full px-2.5 py-1 text-[11px] bg-white/5 border border-white/5">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
              <div className="mt-4">
                <div className="text-[11px] uppercase tracking-wider text-muted-foreground">Missing Skills</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {["GraphQL", "Rust", "System Design"].map((s) => (
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
          </div>

          {/* Application Timeline */}
          <GlassCard className="p-6">
            <div className="text-sm font-semibold">Application Tracker</div>
            <div className="mt-6 flex items-center gap-3 overflow-x-auto">
              {timeline.map((t, i) => (
                <div key={t.label} className="flex items-center gap-3 shrink-0">
                  <div className="flex flex-col items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{
                        background:
                          t.tone === "active"
                            ? "var(--color-secondary)"
                            : t.tone === "muted"
                            ? "var(--color-success)"
                            : "rgba(255,255,255,0.15)",
                        boxShadow: t.tone === "active" ? "0 0 0 4px rgba(168,182,232,0.2)" : undefined,
                      }}
                    />
                    <span className="text-[11px] text-muted-foreground whitespace-nowrap">{t.label}</span>
                  </div>
                  {i < timeline.length - 1 && <div className="w-16 h-px bg-border" />}
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Career Health Score detailed */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">Career Health Score</div>
                <div className="text-xs text-muted-foreground">A composite view of your hire-readiness</div>
              </div>
              <ProgressRing value={92} size={72} />
            </div>
            <div className="mt-5 grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: "ATS Compatibility", value: 92 },
                { label: "Resume Strength", value: 88 },
                { label: "Skill Match", value: 84 },
                { label: "Project Strength", value: 79 },
                { label: "Interview Readiness", value: 70 },
                { label: "Recruiter Visibility", value: 86 },
              ].map((m) => (
                <div key={m.label}>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{m.label}</span>
                    <span>{m.value}</span>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${m.value}%`, background: "var(--color-secondary)" }} />
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </main>

        {/* AI Career Assistant */}
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-[min(720px,calc(100%-2rem))]">
          <div className="glass-strong rounded-2xl p-3">
            <div className="flex flex-wrap gap-1.5 px-2 pb-2 text-[11px] text-muted-foreground">
              {["Resume Review", "Interview Questions", "Career Advice", "Salary Insights", "Learning Roadmap"].map((s) => (
                <button key={s} className="rounded-full border border-border px-2.5 py-1 hover:bg-white/5 hover:text-white transition">
                  {s}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-border bg-white/[0.03] px-3 py-2">
              <Sparkles className="h-4 w-4 text-[var(--color-secondary)]" />
              <input
                value={chat}
                onChange={(e) => setChat(e.target.value)}
                placeholder="Ask AI about your career…"
                className="bg-transparent outline-none text-sm flex-1"
              />
              <button className="btn-glow rounded-lg bg-[var(--color-primary)] p-2 text-white">
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
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
