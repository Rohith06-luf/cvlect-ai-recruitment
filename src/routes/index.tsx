import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Users, UserRound, Sparkles, Shield, LineChart } from "lucide-react";
import { GlassCard } from "@/components/GlassCard";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CVlect — AI Recruitment Platform" },
      { name: "description", content: "AI-powered recruitment platform that delivers transparent, explainable and fair hiring experiences." },
      { property: "og:title", content: "CVlect — AI Recruitment Platform" },
      { property: "og:description", content: "Transparent, explainable, fair hiring — powered by AI." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* ambient */}
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[520px] w-[900px] rounded-full blur-3xl" style={{ background: "radial-gradient(closest-side, rgba(168,182,232,0.18), transparent)" }} />
        <div className="absolute bottom-0 right-0 h-[400px] w-[500px] rounded-full blur-3xl" style={{ background: "radial-gradient(closest-side, rgba(106,124,169,0.20), transparent)" }} />
      </div>

      <nav className="relative z-10 flex items-center justify-between px-6 md:px-10 h-20">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-white/8 border border-white/10 grid place-items-center font-bold">C</div>
          <span className="font-semibold tracking-tight text-lg">CVlect</span>
        </Link>
        <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#about" className="hover:text-white transition">About</a>
          <a href="#features" className="hover:text-white transition">Features</a>
          <a href="#contact" className="hover:text-white transition">Contact</a>
        </div>
        <Link
          to="/recruiter/auth"
          className="btn-glow inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium hover:bg-white/10"
        >
          Get Started <ArrowRight className="h-4 w-4" />
        </Link>
      </nav>

      <section className="relative z-10 max-w-6xl mx-auto px-6 pt-16 pb-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-muted-foreground"
        >
          <Sparkles className="h-3.5 w-3.5 text-[var(--color-secondary)]" />
          Explainable AI hiring, built for teams
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.05 }}
          className="mt-6 text-5xl md:text-7xl font-semibold tracking-tight leading-[1.05]"
        >
          Welcome to <span className="text-[var(--color-highlight)]">CVlect</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="mt-5 max-w-2xl mx-auto text-base md:text-lg text-muted-foreground"
        >
          AI-powered recruitment platform that delivers transparent, explainable and fair
          hiring experiences.
        </motion.p>

        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl mx-auto text-left">
          <RoleCard
            to="/recruiter/auth"
            icon={<Users className="h-5 w-5" />}
            title="Recruiter"
            description="Screen, rank and shortlist candidates with explainable AI insights and blind hiring."
          />
          <RoleCard
            to="/candidate/auth"
            icon={<UserRound className="h-5 w-5" />}
            title="Candidate"
            description="Track applications, improve your resume and get matched to roles that fit your skills."
          />
        </div>

        <div id="features" className="mt-28 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Sparkles, title: "Explainable AI", body: "Every rank comes with reasons — matched skills, gaps and fit signals." },
            { icon: Shield, title: "Blind Hiring", body: "Reduce bias with one toggle. Focus on skills, not identities." },
            { icon: LineChart, title: "Enterprise ready", body: "Analytics, roles, audit-friendly workflows out of the box." },
          ].map(({ icon: Icon, title, body }) => (
            <GlassCard key={title} hover className="p-6">
              <Icon className="h-5 w-5 text-[var(--color-secondary)]" />
              <div className="mt-4 font-semibold">{title}</div>
              <p className="mt-1.5 text-sm text-muted-foreground">{body}</p>
            </GlassCard>
          ))}
        </div>
      </section>

      <footer id="contact" className="relative z-10 border-t border-border/60 py-8 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} CVlect. Crafted for modern hiring teams.
      </footer>
    </div>
  );
}

function RoleCard({
  to,
  icon,
  title,
  description,
}: {
  to: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <motion.div whileHover={{ y: -3 }} transition={{ duration: 0.3 }}>
      <GlassCard className="p-7 h-full flex flex-col">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-white/8 border border-white/10 grid place-items-center text-[var(--color-secondary)]">
            {icon}
          </div>
          <h3 className="text-xl font-semibold">{title}</h3>
        </div>
        <p className="mt-4 text-sm text-muted-foreground flex-1">{description}</p>
        <Link
          to={to}
          className="btn-glow mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium text-white hover:brightness-110"
        >
          Continue <ArrowRight className="h-4 w-4" />
        </Link>
      </GlassCard>
    </motion.div>
  );
}
