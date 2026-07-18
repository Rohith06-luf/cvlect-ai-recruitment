import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  EyeOff,
  Activity,
  UserRound,
  Check,
  X,
  Sparkles,
  MapPin,
  Briefcase,
  Star,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Clock,
  Mail,
  Phone,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { ProgressRing } from "@/components/ProgressRing";
import { api, type PipelineEntry, type Stats } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/recruiter/dashboard")({
  head: () => ({ meta: [{ title: "Recruiter Dashboard — CVlect" }] }),
  component: RecruiterDashboard,
});

type SectionId = "dashboard" | "resumes" | "blind" | "activities";

const PAGE_SIZE = 3;

function RecruiterDashboard() {
  const { user } = useAuth();
  const recruiterId = user?.id ?? 1;
  
  const [section, setSection] = useState<SectionId>("dashboard");
  const [selected, setSelected] = useState<number[]>([]);
  const [openReason, setOpenReason] = useState<PipelineEntry | null>(null);
  const [openResume, setOpenResume] = useState<PipelineEntry | null>(null);
  const [blind, setBlind] = useState(false);
  const [page, setPage] = useState(1);

  // Fetch stats for the dashboard
  const { data: stats } = useQuery({
    queryKey: ["stats", "recruiter", recruiterId],
    queryFn: () => api.getStats({ recruiterId }),
    refetchInterval: 3000,
  });

  // Fetch pipeline candidates (paginated)
  const { data: pipelineData } = useQuery({
    queryKey: ["pipeline", recruiterId, page, PAGE_SIZE],
    queryFn: () => api.listPipeline({ recruiterId, page, pageSize: PAGE_SIZE }),
    refetchInterval: 3000,
  });

  // Fetch total count for pagination
  const { data: pipelineCount } = useQuery({
    queryKey: ["pipeline-count", recruiterId],
    queryFn: () => api.countPipeline({ recruiterId }),
    refetchInterval: 3000,
  });

  // Fetch activities
  const { data: activities } = useQuery({
    queryKey: ["activities", recruiterId],
    queryFn: () => api.listActivities(recruiterId, 20),
    refetchInterval: 3000,
  });

  const [resumeFiles, setResumeFiles] = useState<Array<{ name: string; path: string }>>([]);

  useEffect(() => {
    const basePath = (window as Window & { __VITE_DEV_SERVER__?: unknown }).location?.origin ?? "";
    void fetch(`${basePath}/Resume`).then(async (resp) => {
      if (!resp.ok) return;
      const text = await resp.text();
      const names = text.match(/href="([^"]+)"/g) ?? [];
      const files = names
        .map((entry) => entry.replace(/href="|"/g, ""))
        .filter((entry) => entry.toLowerCase().endsWith(".pdf"))
        .map((entry) => ({ name: entry.split("/").pop() ?? entry, path: entry }));
      setResumeFiles(files);
    }).catch(() => undefined);
  }, []);

  const totalPages = Math.ceil((pipelineCount?.total ?? 0) / PAGE_SIZE);
  const candidates = pipelineData ?? [];
  const resumeList = useMemo(() => (resumeFiles.length > 0 ? resumeFiles : []), [resumeFiles]);

  const items: SidebarItem[] = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "resumes", label: "Resumes", icon: FileText },
    { id: "blind", label: "Blind Hiring", icon: EyeOff },
    { id: "activities", label: "Activities", icon: Activity },
    { label: "My Profile", to: "/recruiter/profile", icon: UserRound },
  ];

  const subtitle: Record<SectionId, string> = {
    dashboard: user?.name ? `Screening pipeline · ${user.name}` : "Screening pipeline",
    resumes: "All resumes in the pipeline",
    blind: "Bias-aware anonymous screening",
    activities: "Recent hiring activity",
  };

  const titles: Record<SectionId, string> = {
    dashboard: "HR Dashboard",
    resumes: "Resumes",
    blind: "Blind Hiring",
    activities: "Activities",
  };

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar
        items={items}
        activeId={section}
        onSelect={(id) => setSection(id as SectionId)}
      />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title={titles[section]} subtitle={subtitle[section]} profileTo="/recruiter/profile" />

        <main className="p-6 space-y-6">
          <motion.div
            key={section}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {section === "dashboard" && (
              <DashboardSection
                blind={blind}
                setBlind={setBlind}
                onOpenResumes={() => setSection("resumes")}
                stats={stats}
              />
            )}

            {section === "resumes" && (
              <ResumesSection
                candidates={candidates}
                total={pipelineCount?.total ?? 0}
                selected={selected}
                setSelected={setSelected}
                blind={blind}
                onOpenReason={setOpenReason}
                onOpenResume={setOpenResume}
                page={page}
                totalPages={totalPages}
                setPage={setPage}
                resumeFiles={resumeList}
              />
            )}

            {section === "blind" && <BlindSection blind={blind} setBlind={setBlind} />}
            {section === "activities" && <ActivitiesSection activities={activities ?? []} />}
          </motion.div>
        </main>
      </div>

      {/* Explainable AI modal */}
      {openReason && (
        <ReasonModal candidate={openReason} onClose={() => setOpenReason(null)} />
      )}

      {/* Resume viewer modal */}
      {openResume && (
        <ResumeViewer candidate={openResume} onClose={() => setOpenResume(null)} blind={blind} />
      )}
    </div>
  );
}

/* ---------- Sections ---------- */

function DashboardSection({
  blind,
  setBlind,
  onOpenResumes,
  stats,
}: {
  blind: boolean;
  setBlind: (v: boolean) => void;
  onOpenResumes: () => void;
  stats?: Stats;
}) {
  return (
    <>
      <GlassCard className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Job Description</div>
            <textarea
              placeholder="Add or update a job description for this screening session."
              className="mt-2 w-full bg-transparent outline-none resize-none text-sm leading-relaxed"
              rows={2}
            />
          </div>
          <label className="flex items-center gap-3 text-sm shrink-0">
            <span className="text-muted-foreground">Blind Hiring</span>
            <button
              onClick={() => setBlind(!blind)}
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {(stats ? [
          { label: "Total Resumes", value: stats.total_resumes, hint: "", icon: FileText },
          { label: "Shortlisted", value: stats.shortlisted, hint: "", icon: Star },
          { label: "Selected", value: stats.selected, hint: "", icon: Check },
          { label: "Rejected", value: stats.rejected, hint: "", icon: X },
        ] : [
          { label: "Total Resumes", value: 0, hint: "", icon: FileText },
          { label: "Shortlisted", value: 0, hint: "", icon: Star },
          { label: "Selected", value: 0, hint: "", icon: Check },
          { label: "Rejected", value: 0, hint: "", icon: X },
        ]).map(({ label, value, hint, icon: Icon }) => (
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


      <GlassCard className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Latest Resumes</h3>
            <p className="text-xs text-muted-foreground">Head to Resumes for the full pipeline.</p>
          </div>
          <button
            onClick={onOpenResumes}
            className="rounded-xl border border-border bg-white/[0.03] px-3 py-2 text-xs font-medium hover:bg-white/[0.06] transition"
          >
            View all resumes
          </button>
        </div>
      </GlassCard>
    </>
  );
}

function ResumesSection({
  candidates,
  total,
  selected,
  setSelected,
  blind,
  onOpenReason,
  onOpenResume,
  page,
  totalPages,
  setPage,
  resumeFiles,
}: {
  candidates: PipelineEntry[];
  total: number;
  selected: number[];
  setSelected: (fn: (s: number[]) => number[]) => void;
  blind: boolean;
  onOpenReason: (c: PipelineEntry) => void;
  onOpenResume: (c: PipelineEntry) => void;
  page: number;
  totalPages: number;
  setPage: (n: number) => void;
  resumeFiles: Array<{ name: string; path: string }>;
}) {
  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">
          Candidates <span className="text-muted-foreground font-normal">· {total}</span>
        </h2>
        <button
          disabled={selected.length < 2}
          className="rounded-xl border border-border bg-white/[0.03] px-3 py-2 text-xs font-medium hover:bg-white/[0.06] disabled:opacity-40"
        >
          Compare Selected ({selected.length})
        </button>
      </div>

      <div className="space-y-4">
        {resumeFiles.length > 0 && (
          <GlassCard hover className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold">Resume Folder</h3>
                <p className="text-xs text-muted-foreground">Files already available in the Resume directory</p>
              </div>
            </div>
            <div className="mt-3 space-y-2">
              {resumeFiles.map((file) => (
                <div key={file.path} className="flex items-center justify-between rounded-lg border border-border bg-white/[0.03] px-3 py-2 text-sm">
                  <span className="truncate">{file.name}</span>
                  <span className="text-[11px] text-muted-foreground">Stored</span>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

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
                      {blind ? "•" : c.name?.split(" ").map((n) => n[0]).join("")}
                    </div>
                    <div className="min-w-0">
                      <div className="font-semibold truncate">{blind ? `Candidate #${c.rank}` : c.name}</div>
                      {blind && (
                        <div className="text-[10px] text-muted-foreground mt-0.5">ID: {c.candidate_id ?? c.id}</div>
                      )}
                      <div className="text-xs text-muted-foreground flex items-center gap-3 mt-1">
                        <span className="inline-flex items-center gap-1"><Briefcase className="h-3 w-3" />{c.role}</span>
                        <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{blind ? "—" : c.location}</span>
                        <span>{c.experience}</span>
                      </div>
                      <div className="text-xs text-muted-foreground flex flex-wrap gap-x-4 gap-y-1.5 mt-2">
                        {!blind && c.email && <span className="inline-flex items-center gap-1"><Mail className="h-3.5 w-3.5" />{c.email}</span>}
                        {!blind && c.phone && <span className="inline-flex items-center gap-1"><Phone className="h-3.5 w-3.5" />{c.phone}</span>}
                        {c.filename && <span className="inline-flex items-center gap-1"><FileText className="h-3.5 w-3.5" />{c.filename}</span>}
                        {c.uploaded_at && <span className="inline-flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{new Date(c.uploaded_at).toLocaleDateString()}</span>}
                        <span className="inline-flex items-center gap-1">Status: <span className="text-[var(--color-secondary)] uppercase text-[10px] font-semibold">{c.status}</span></span>
                      </div>
                      {c.education && (
                        <div className="text-xs text-muted-foreground mt-2 font-medium">
                          Education: <span className="font-normal text-muted-foreground/80">{blind ? c.education.replace(/[A-Za-z0-9\s]+ (University|College|Institute|School|IIT|BITS)/gi, "[Redacted Institution]") : c.education}</span>
                        </div>
                      )}
                      {(c.matched.length > 0 || c.missing.length > 0) && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {c.matched.map(s => (
                            <span key={s} className="text-[10px] rounded-full bg-[var(--color-success)]/10 text-[var(--color-success)] px-2 py-0.5 border border-[var(--color-success)]/20">{s}</span>
                          ))}
                          {c.missing.map(s => (
                            <span key={s} className="text-[10px] rounded-full bg-[var(--color-warning)]/10 text-[var(--color-warning)] px-2 py-0.5 border border-[var(--color-warning)]/20">{s}</span>
                          ))}
                        </div>
                      )}
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
                    onClick={() => onOpenReason(c)}
                    className="mt-3 inline-flex items-center gap-1.5 text-xs text-[var(--color-highlight)] hover:underline"
                  >
                    <Sparkles className="h-3.5 w-3.5" /> {"Why this candidate?"} <ChevronRight className="h-3 w-3" />
                  </button>
                </div>

                <div className="flex flex-col gap-2 w-40 shrink-0">
                  <button
                    onClick={() => onOpenResume(c)}
                    className="rounded-xl border border-border bg-white/[0.03] px-3 py-2 text-xs font-medium hover:bg-white/[0.06] transition"
                  >
                    View Resume
                  </button>
                  <button
                    onClick={() => api.updatePipelineStatus(c.id, "shortlisted").then(() => window.location.reload())}
                    className="btn-glow rounded-xl bg-[var(--color-primary)] px-3 py-2 text-xs font-medium hover:brightness-110 transition"
                  >
                    Select
                  </button>
                  <button
                    onClick={() => api.updatePipelineStatus(c.id, "rejected").then(() => window.location.reload())}
                    className="rounded-xl border border-[var(--color-error)]/60 text-[var(--color-error)] px-3 py-2 text-xs font-medium hover:bg-[var(--color-error)]/10 transition"
                  >
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
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page === 1}
          className="h-8 px-2 rounded-lg text-xs transition text-muted-foreground hover:bg-white/5 disabled:opacity-40 disabled:hover:bg-transparent"
        >
          Prev
        </button>
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
          <button
            key={p}
            onClick={() => setPage(p)}
            className={`h-8 w-8 rounded-lg text-xs transition ${
              p === page ? "bg-white/10 text-white" : "text-muted-foreground hover:bg-white/5"
            }`}
          >
            {p}
          </button>
        ))}
        <button
          onClick={() => setPage(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className="h-8 px-2 rounded-lg text-xs transition text-muted-foreground hover:bg-white/5 disabled:opacity-40 disabled:hover:bg-transparent"
        >
          Next
        </button>
      </div>
    </>
  );
}

function BlindSection({ blind, setBlind }: { blind: boolean; setBlind: (v: boolean) => void }) {
  return (
    <GlassCard className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Blind Hiring</h3>
          <p className="mt-1.5 text-sm text-muted-foreground max-w-lg">
            Anonymize names, photos and locations across all resume views to reduce bias
            during initial screening.
          </p>
        </div>
        <button
          onClick={() => setBlind(!blind)}
          className={`relative h-6 w-11 rounded-full transition ${blind ? "bg-[var(--color-secondary)]" : "bg-white/10"}`}
        >
          <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${blind ? "left-5" : "left-0.5"}`} />
        </button>
      </div>
    </GlassCard>
  );
}

function ActivitiesSection({ activities }: { activities: Activity[] }) {
  return (
    <GlassCard className="p-5">
      <h3 className="text-sm font-semibold mb-4">Recent activity</h3>
      <ul className="space-y-3">
        {activities.map((e, i) => (
          <li key={i} className="flex items-start gap-3 text-sm">
            <div className="h-8 w-8 rounded-lg border border-border bg-white/[0.03] grid place-items-center shrink-0">
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div>{e.text}</div>
              <div className="text-[11px] text-muted-foreground">{new Date(e.created_at).toLocaleString()}</div>
            </div>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}

/* ---------- Modals ---------- */

function ReasonModal({ candidate, onClose }: { candidate: PipelineEntry; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
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
          <button onClick={onClose} className="text-muted-foreground hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-4 text-sm text-muted-foreground">{candidate.reason}</p>

        <div className="mt-5 space-y-4 text-sm">
          <Section label="Matched Skills">
            <ChipRow items={candidate.matched} tone="success" />
          </Section>
          <Section label="Missing Skills">
            <ChipRow items={candidate.missing} tone="warning" />
          </Section>
          <div className="grid grid-cols-2 gap-3">
            <Meta label="Experience Match" value="Strong" />
            <Meta label="Education Match" value="Good" />
            <Meta label="Project Match" value="Strong" />
            <Meta label="Recommendation" value="Advance to interview" tone="success" />
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function ResumeViewer({
  candidate,
  onClose,
  blind,
}: {
  candidate: PipelineEntry;
  onClose: () => void;
  blind: boolean;
}) {
  const [scale, setScale] = useState(1);
  const displayName = blind ? `Candidate #${candidate.rank}` : (candidate.name ?? "Candidate");

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm overflow-hidden"
      onClick={onClose}
    >
      {/* Toolbar */}
      <div
        className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 rounded-xl border border-border bg-background/80 backdrop-blur px-3 py-2"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="text-xs text-muted-foreground mr-2">{displayName} · Resume</span>
        <button
          onClick={() => setScale((s) => Math.max(0.4, s - 0.1))}
          className="h-7 w-7 rounded-lg border border-border grid place-items-center hover:bg-white/5"
          aria-label="Zoom out"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </button>
        <span className="text-xs tabular-nums w-10 text-center">{Math.round(scale * 100)}%</span>
        <button
          onClick={() => setScale((s) => Math.min(3, s + 0.1))}
          className="h-7 w-7 rounded-lg border border-border grid place-items-center hover:bg-white/5"
          aria-label="Zoom in"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => setScale(1)}
          className="h-7 w-7 rounded-lg border border-border grid place-items-center hover:bg-white/5"
          aria-label="Reset"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
        <div className="w-px h-5 bg-border mx-1" />
        <span className="text-[10px] text-muted-foreground">Drag to move</span>
        <button
          onClick={onClose}
          className="ml-2 h-7 w-7 rounded-lg border border-border grid place-items-center hover:bg-white/5"
          aria-label="Close"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Draggable resume */}
      <div
        className="absolute inset-0 grid place-items-center"
        onClick={(e) => e.stopPropagation()}
      >
        <motion.div
          drag
          dragMomentum={false}
          className="cursor-grab active:cursor-grabbing"
          style={{ scale }}
        >
          <ResumeSheet name={displayName} candidate={candidate} blind={blind} />
        </motion.div>
      </div>
    </div>
  );
}

function ResumeSheet({ name, candidate, blind }: { name: string; candidate: PipelineEntry; blind: boolean }) {
  const displayLocation = blind ? "[Redacted Location]" : (candidate.location ?? "—");
  const displayEdu = blind 
    ? (candidate.education ? candidate.education.replace(/[A-Za-z0-9\s]+ (University|College|Institute|School|IIT|BITS)/gi, "[Redacted Institution]") : "Resume education will be shown after parsing")
    : (candidate.education ?? (candidate.experience ? "Resume education will be shown after parsing" : "No education details captured yet"));

  return (
    <div
      className="bg-white text-neutral-900 rounded-md shadow-2xl select-none"
      style={{ width: 620, minHeight: 820, padding: 44 }}
    >
      <div className="border-b border-neutral-200 pb-5">
        <h1 className="text-2xl font-semibold tracking-tight">{name}</h1>
        <p className="text-sm text-neutral-600 mt-1">{candidate.role} · {displayLocation}</p>
        <p className="text-xs text-neutral-500 mt-1">{candidate.experience} experience</p>
        {!blind && (
          <p className="text-xs text-neutral-400 mt-1">
            Email: {candidate.email ?? "—"} | Phone: {candidate.phone ?? "—"}
          </p>
        )}
        {blind && (
          <p className="text-xs text-neutral-400 mt-1">
            Candidate ID: {candidate.candidate_id ?? candidate.id}
          </p>
        )}
      </div>

      <section className="mt-5">
        <h2 className="text-[11px] uppercase tracking-wider text-neutral-500 font-bold">Summary</h2>
        <p className="mt-2 text-sm leading-relaxed">{candidate.summary}</p>
      </section>

      <section className="mt-5">
        <h2 className="text-[11px] uppercase tracking-wider text-neutral-500 font-bold">Skills</h2>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {[...candidate.matched, ...candidate.missing].map((s) => (
            <span key={s} className="text-[11px] rounded-full bg-neutral-100 px-2 py-0.5">{s}</span>
          ))}
        </div>
      </section>

      <section className="mt-5">
        <h2 className="text-[11px] uppercase tracking-wider text-neutral-500 font-bold">Experience</h2>
        <div className="mt-2 space-y-3 text-sm">
          <div>
            <div className="font-medium">{candidate.role ?? "Experience details pending"}</div>
            <div className="text-xs text-neutral-500">{candidate.experience ?? "Experience details pending"}</div>
            <p className="mt-1 text-neutral-700">{candidate.summary ?? "Resume details will appear after analysis."}</p>
          </div>
        </div>
      </section>

      <section className="mt-5">
        <h2 className="text-[11px] uppercase tracking-wider text-neutral-500 font-bold">Education</h2>
        <p className="mt-2 text-sm">{displayEdu}</p>
      </section>
    </div>
  );
}

/* ---------- Small helpers ---------- */

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

function Meta({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div className="rounded-xl border border-border bg-white/[0.03] p-3">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-1 text-sm font-medium ${tone === "success" ? "text-[var(--color-success)]" : ""}`}>{value}</div>
    </div>
  );
}

