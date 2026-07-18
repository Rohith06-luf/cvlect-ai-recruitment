import { Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { useState, type ReactNode } from "react";
import { GlassCard } from "@/components/GlassCard";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen relative flex flex-col">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute top-0 left-0 h-[420px] w-[600px] rounded-full blur-3xl" style={{ background: "radial-gradient(closest-side, rgba(168,182,232,0.15), transparent)" }} />
        <div className="absolute bottom-0 right-0 h-[420px] w-[600px] rounded-full blur-3xl" style={{ background: "radial-gradient(closest-side, rgba(106,124,169,0.18), transparent)" }} />
      </div>

      <nav className="relative z-10 flex items-center justify-between px-6 md:px-10 h-20">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-white/8 border border-white/10 grid place-items-center font-bold">C</div>
          <span className="font-semibold tracking-tight text-lg">CVlect</span>
        </Link>
        <Link to="/" className="text-sm text-muted-foreground hover:text-white transition inline-flex items-center gap-1.5">
          <ArrowLeft className="h-4 w-4" /> Back
        </Link>
      </nav>

      <div className="relative z-10 flex-1 grid place-items-center px-4 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <GlassCard className="p-8">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
            <div className="mt-7">{children}</div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}

export function AuthForm({
  submitLabel,
  onSubmitTo,
  createLabel,
  role,
}: {
  submitLabel: string;
  onSubmitTo: string;
  createLabel: string;
  role: "recruiter" | "candidate";
}) {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      let user;
      if (mode === "signin") {
        user = await login(email, password);
      } else {
        user = await signup({ name, email, password, role });
      }
      // Redirect based on role (compat layer returns lowercase role)
      const dest = user.role === "recruiter" ? "/recruiter/dashboard" : "/candidate/dashboard";
      navigate({ to: dest });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || "Authentication failed. Please check your credentials.");
      } else if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
        setError("Cannot connect to server. Make sure the backend is running on port 8000.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {mode === "signup" && (
        <Field label="Full name">
          <input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full rounded-xl bg-white/5 border border-border px-3.5 py-2.5 text-sm outline-none focus:border-secondary/60 transition"
          />
        </Field>
      )}
      <Field label="Email">
        <input
          type="email"
          placeholder="you@work.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded-xl bg-white/5 border border-border px-3.5 py-2.5 text-sm outline-none focus:border-secondary/60 transition"
        />
      </Field>
      <Field label="Password">
        <input
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
          className="w-full rounded-xl bg-white/5 border border-border px-3.5 py-2.5 text-sm outline-none focus:border-secondary/60 transition"
        />
      </Field>

      {error && (
        <div className="rounded-lg border border-[var(--color-error)]/40 bg-[var(--color-error)]/10 px-3 py-2 text-xs text-[var(--color-error)]">
          {error}
        </div>
      )}

      {mode === "signin" && (
        <div className="flex items-center justify-between text-xs">
          <label className="flex items-center gap-2 text-muted-foreground cursor-pointer">
            <input type="checkbox" className="h-3.5 w-3.5 rounded accent-[var(--color-secondary)]" />
            Remember me
          </label>
          <a className="text-[var(--color-highlight)] hover:underline" href="#">Forgot password?</a>
        </div>
      )}

      <button
        type="submit"
        disabled={busy}
        className="btn-glow w-full inline-flex items-center justify-center rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition disabled:opacity-60"
      >
        {busy ? "Please wait…" : mode === "signin" ? submitLabel : "Create account"}
      </button>

      <div className="pt-2 text-center text-xs text-muted-foreground">
        <button
          type="button"
          onClick={() => {
            setMode(mode === "signin" ? "signup" : "signin");
            setError(null);
          }}
          className="hover:text-white transition"
        >
          {mode === "signin" ? createLabel : "Already have an account? Sign in"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
