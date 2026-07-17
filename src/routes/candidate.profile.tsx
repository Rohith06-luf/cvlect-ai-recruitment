import { createFileRoute, Link } from "@tanstack/react-router";
import {
  LayoutDashboard,
  FileText,
  Gauge,
  Briefcase,
  BarChart3,
  Settings,
  Mail,
  Phone,
  MapPin,
  Building2,
  LinkIcon,
  ArrowLeft,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";

export const Route = createFileRoute("/candidate/profile")({
  head: () => ({ meta: [{ title: "My Profile — CVlect" }] }),
  component: CandidateProfile,
});

const items: SidebarItem[] = [
  { label: "Dashboard", to: "/candidate/dashboard", icon: LayoutDashboard },
  { label: "Applications", to: "/candidate/dashboard", icon: Briefcase },
  { label: "Resume", to: "/candidate/dashboard", icon: FileText },
  { label: "AI Resume Score", to: "/candidate/dashboard", icon: Gauge },
  { label: "Skill Gap", to: "/candidate/dashboard", icon: BarChart3 },
  { label: "Settings", to: "/candidate/dashboard", icon: Settings },
];

function CandidateProfile() {
  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar items={items} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/candidate/profile" />

        <main className="p-6 space-y-6">
          <Link
            to="/candidate/dashboard"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-white transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
          </Link>

          <GlassCard className="p-6">
            <div className="flex items-center gap-5">
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-[var(--color-secondary)] to-[var(--color-primary)] grid place-items-center text-2xl font-semibold text-[var(--color-background)]">
                PS
              </div>
              <div>
                <h2 className="text-xl font-semibold">Priya Sharma</h2>
                <p className="text-sm text-muted-foreground">Senior Frontend Engineer</p>
                <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-[var(--color-success)] bg-[var(--color-success)]/15 rounded-full px-2 py-0.5">
                  Verified account
                </div>
              </div>
            </div>
          </GlassCard>

          <div className="grid md:grid-cols-2 gap-4">
            <GlassCard className="p-5">
              <h3 className="text-sm font-semibold mb-4">Contact</h3>
              <div className="space-y-3 text-sm">
                <Row icon={Mail} label="Email" value="priya.sharma@email.com" />
                <Row icon={Phone} label="Phone" value="+91 (98) 234-5678" />
                <Row icon={MapPin} label="Location" value="Bengaluru, India" />
              </div>
            </GlassCard>

            <GlassCard className="p-5">
              <h3 className="text-sm font-semibold mb-4">Professional</h3>
              <div className="space-y-3 text-sm">
                <Row icon={Building2} label="Current" value="Senior Frontend Engineer" />
                <Row icon={Briefcase} label="Experience" value="6 years" />
                <Row icon={LinkIcon} label="Portfolio" value="priya-portfolio.dev" />
              </div>
            </GlassCard>
          </div>

          <GlassCard className="p-5">
            <h3 className="text-sm font-semibold mb-4">About</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Product-focused frontend engineer with deep expertise in React, TypeScript, and design systems.
              Passionate about building accessible, performant user interfaces and mentoring junior engineers.
            </p>
          </GlassCard>

          <GlassCard className="p-5">
            <h3 className="text-sm font-semibold mb-4">Skills</h3>
            <div className="flex flex-wrap gap-2">
              {["React", "TypeScript", "Design Systems", "Accessibility", "Testing", "Performance", "Node.js"].map((skill) => (
                <span key={skill} className="rounded-full bg-white/5 border border-white/5 px-3 py-1.5 text-xs">
                  {skill}
                </span>
              ))}
            </div>
          </GlassCard>

          <div className="flex gap-2">
            <button className="btn-glow rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition">
              Edit profile
            </button>
            <button className="rounded-xl border border-border bg-white/[0.03] px-4 py-2.5 text-sm font-medium hover:bg-white/[0.06] transition">
              Change password
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-8 w-8 rounded-lg border border-border bg-white/[0.03] grid place-items-center">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="text-sm font-medium truncate">{value}</div>
      </div>
    </div>
  );
}
