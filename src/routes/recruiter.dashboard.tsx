import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import {
  LayoutDashboard,
  FileText,
  EyeOff,
  Activity,
  UserRound,
  Settings,
  Check,
  X,
  Sparkles,
  MapPin,
  Briefcase,
  Star,
  ChevronRight,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { ProgressRing } from "@/components/ProgressRing";

export const Route = createFileRoute("/recruiter/dashboard")({
  head: () => ({ meta: [{ title: "Recruiter Dashboard — CVlect" }] }),
  component: RecruiterDashboard,
});

const items: SidebarItem[] = [
  { label: "Dashboard", to: "/recruiter/dashboard", icon: LayoutDashboard },
  { label: "Resumes", to: "/recruiter/dashboard", icon: FileText },
  { label: "Blind Hiring", to: "/recruiter/dashboard", icon: EyeOff },
  { label: "Activities", to: "/recruiter/dashboard", icon: Activity },
  { label: "My Profile", to: "/recruiter/dashboard", icon: UserRound },
  { label: "Settings", to: "/recruiter/dashboard", icon: Settings },
];

const stats = [
  { label: "Total Resumes", value: 248, hint: "+12 this week", icon: FileText },
  { label: "Shortlisted", value: 42, hint: "17% of pool", icon: Star },
  { label: "Selected", value: 9, hint: "3 offers out", icon: Check },
  { label: "Rejected", value: 61, hint: "Auto-filtered", icon: X },
];

type Candidate = {
  id: number;
  name: string;
  role: string;
  location: string;
  experience: string;
  score: number;
  rank: number;
  topMatch?: boolean;
  summary: string;
  reason: string;
  matched: string[];
  missing: string[];
};

const candidates: Candidate[] = [
  {
    id: 1,
    name: "Priya Sharma",
    role: "Senior Frontend Engineer",
    location: "Bengaluru, IN",
    experience: "6 yrs",
    score: 94,
    rank: 1,
    topMatch: true,
    summary: "Product-focused engineer with deep React + design systems experience across two YC startups.",
    reason: "Strong React, TypeScript, design system authorship; ships accessible, tested UI.",
    matched: ["React", "TypeScript", "Design Systems", "Accessibility"],
    missing: ["GraphQL"],
  },
  {
    id: 2,
    name: "Marcus Weiss",
    role: "Frontend Engineer",
    location: "Berlin, DE",
    experience: "4 yrs",
    score: 88,
    rank: 2,
    summary: "Performance-obsessed engineer, contributed to core web vitals improvements at a fintech.",
    reason: "Solid React, strong performance work, modest testing coverage on prior repos.",
    matched: ["React", "TypeScript", "Performance"],
    missing: ["Design Systems", "Testing"],
  },
  {
    id: 3,
    name: "Amelia Chen",
    role: "Full-stack Engineer",
    location: "Toronto, CA",
    experience: "5 yrs",
    score: 82,
    rank: 3,
    summary: "Full-stack engineer with Node + React, led a small platform team of three.",
    reason: "Good breadth; frontend depth is lighter than the top match.",
    matched: ["React", "Node.js", "TypeScript"],
    missing: ["Design Systems", "Accessibility"],
  },
];

function RecruiterDashboard() {
  const [selected, setSelected] = useState<number[]>([]);
  const [openReason, setOpenReason] = useState<Candidate | null>(null);
  const [blind, setBlind] = useState(false);

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar items={items} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="HR Dashboard" subtitle="Screening pipeline · Senior Frontend Engineer" />

        <main className="p-6 space-y-6">
          {/* JD + Blind Hiring */}
          <GlassCard className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Job Description</div>
                <textarea
                  defaultValue="Senior Frontend Engineer — React, TypeScript, design systems, accessibility. Ship product surfaces with a small, senior team."
                  className="mt-2 w-full bg-transparent outline-none resize-none text-sm leading-relaxed"
                  rows={2}
                />
              </div>
              <label className="flex items-center gap-3 text-sm shrink-0">
                <span className="text-muted-foreground">Blind Hiring</span>
                <button
                  onClick={() => setBlind((v) => !v)}
                  className={`relative h-6 w-11 rounded-full transition ${blind ? "bg-[var(--color-secondary)]" : "bg-white/10"}`}
                  aria-label="Toggle blind hiring"
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${blind ? "left-5" : "left-0.5"}`}
                  />
                </button>
              </label>
            </div>
          </GlassCard>

          {/* Analytics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map(({ label, value, hint, icon: Icon }) => (
              <GlassCard key={label} hover className="p-5">
                <div className="flex items-center justify-between">
                  <Icon className="h-4 w-4 text-[var(--color-secondary)]" />
                  <span className="text-[10px] text-muted-foreground">{hint}</span>
                </div>
                <div className="mt-3 text-3xl font-semibold tracking-tight">{value}</div>
                <div className="mt-1 text-xs text-muted-foreground">{label}</div>
              </GlassCard>
            ))}
          </div>

          {/* Resume list header */}
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Candidates <span className="text-muted-foreground font-normal">· {candidates.length}</span></h2>
            <button
              disabled={selected.length < 2}
              className="rounded-xl border border-border bg-white/[0.03] px-3 py-2 text-xs font-medium hover:bg-white/[0.06] disabled:opacity-40"
            >
              Compare Selected ({selected.length})
            </button>
          </div>

          {/* Candidate cards */}
          <div className="space-y-4">
            {candidates.map((c) => (
              <motion.div key={c.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                <GlassCard hover className="p-5">
                  <div className="grid grid-cols-[auto_auto_1fr_auto] gap-5 items-start">
                    <input
                      type="checkbox"
                      className="mt-2 h-4 w-4 rounded accent-[var(--color-secondary)]"
                      checked={selected.includes(c.id)}
                      onChange={(e) =>
                        setSelected((s) => (e.target.checked ? [...s, c.id] : s.filter((x) => x !== c.id)))
                      }
                    />

                    <ProgressRing value={c.score} size={72} label="AI" />

                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[var(--color-secondary)] to-[var(--color-primary)] grid place-items-center text-xs font-semibold text-[var(--color-background)]">
                          {blind ? "•" : c.name.split(" ").map((n) => n[0]).join("")}
                        </div>
                        <div className="min-w-0">
                          <div className="font-semibold truncate">{blind ? `Candidate #${c.rank}` : c.name}</div>
                          <div className="text-xs text-muted-foreground flex items-center gap-3">
                            <span className="inline-flex items-center gap-1"><Briefcase className="h-3 w-3" />{c.role}</span>
                            <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{blind ? "—" : c.location}</span>
                            <span>{c.experience}</span>
                          </div>
                        </div>
                        {c.topMatch && (
                          <span className="ml-2 rounded-full bg-[var(--color-success)]/15 text-[var(--color-success)] px-2 py-0.5 text-[10px] font-medium">
                            Top Match
                          </span>
                        )}
                        <span className="ml-auto text-[10px] text-muted-foreground">Rank #{c.rank}</span>
                      </div>

                      <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{c.summary}</p>

                      <button
                        onClick={() => setOpenReason(c)}
                        className="mt-3 inline-flex items-center gap-1.5 text-xs text-[var(--color-highlight)] hover:underline"
                      >
                        <Sparkles className="h-3.5 w-3.5" /> Why this candidate? <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>

                    <div className="flex flex-col gap-2 w-40 shrink-0">
                      <ActionBtn>View Resume</ActionBtn>
                      <ActionBtn>AI Analysis</ActionBtn>
                      <ActionBtn>Feedback</ActionBtn>
                      <ActionBtn>Shortlist</ActionBtn>
                      <button className="btn-glow rounded-xl bg-[var(--color-primary)] px-3 py-2 text-xs font-medium hover:brightness-110 transition">
                        Select
                      </button>
                      <button className="rounded-xl border border-[var(--color-error)]/60 text-[var(--color-error)] px-3 py-2 text-xs font-medium hover:bg-[var(--color-error)]/10 transition">
                        Reject
                      </button>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-1 pt-2">
            {[1, 2, 3, 4].map((p) => (
              <button
                key={p}
                className={`h-8 w-8 rounded-lg text-xs transition ${p === 1 ? "bg-white/10 text-white" : "text-muted-foreground hover:bg-white/5"}`}
              >
                {p}
              </button>
            ))}
          </div>
        </main>
      </div>

      {/* Explainable AI modal */}
      {openReason && (
        <div className="fixed inset-0 z-50 grid place-items-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setOpenReason(null)}>
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.25 }}
            className="glass-strong rounded-2xl w-full max-w-lg p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Explainable AI</div>
                <h3 className="mt-1 text-lg font-semibold">Why this candidate?</h3>
              </div>
              <button onClick={() => setOpenReason(null)} className="text-muted-foreground hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">{openReason.reason}</p>

            <div className="mt-5 space-y-4 text-sm">
              <Section label="Matched Skills">
                <ChipRow items={openReason.matched} tone="success" />
              </Section>
              <Section label="Missing Skills">
                <ChipRow items={openReason.missing} tone="warning" />
              </Section>
              <Grid>
                <Meta label="Experience Match" value="Strong" />
                <Meta label="Education Match" value="Good" />
                <Meta label="Project Match" value="Strong" />
                <Meta label="Recommendation" value="Advance to interview" tone="success" />
              </Grid>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}

function ActionBtn({ children }: { children: React.ReactNode }) {
  return (
    <button className="rounded-xl border border-border bg-white/[0.03] px-3 py-2 text-xs font-medium hover:bg-white/[0.06] transition">
      {children}
    </button>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">{label}</div>
      {children}
    </div>
  );
}

function ChipRow({ items, tone }: { items: string[]; tone: "success" | "warning" }) {
  const color = tone === "success" ? "var(--color-success)" : "var(--color-warning)";
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((i) => (
        <span
          key={i}
          className="rounded-full px-2.5 py-1 text-[11px]"
          style={{ background: `color-mix(in oklab, ${color} 15%, transparent)`, color }}
        >
          {i}
        </span>
      ))}
    </div>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 gap-3">{children}</div>;
}

function Meta({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div className="rounded-xl border border-border bg-white/[0.03] p-3">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-1 text-sm font-medium ${tone === "success" ? "text-[var(--color-success)]" : ""}`}>{value}</div>
    </div>
  );
}
