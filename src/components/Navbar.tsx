import { Link } from "@tanstack/react-router";
import { Bell } from "lucide-react";

export function Navbar({
  title,
  subtitle,
  profileTo = "/recruiter/profile",
}: {
  title: string;
  subtitle?: string;
  profileTo?: string;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-border/60 backdrop-blur-xl bg-background/70">
      <div className="flex items-center gap-4 px-6 h-16">
        <div className="min-w-0 flex-1">
          <h1 className="text-base font-semibold tracking-tight truncate">{title}</h1>
          {subtitle && <p className="text-xs text-muted-foreground truncate">{subtitle}</p>}
        </div>

        <button className="relative rounded-xl border border-border p-2 hover:bg-white/5 transition">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-[var(--color-secondary)]" />
        </button>

        <Link
          to={profileTo}
          className="flex items-center gap-3 rounded-xl border border-border pl-1 pr-3 py-1 hover:bg-white/5 transition"
        >
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-[var(--color-secondary)] to-[var(--color-primary)] grid place-items-center text-[11px] font-semibold text-[var(--color-background)]">
            AR
          </div>
          <div className="hidden sm:block text-xs">
            <div className="font-medium leading-tight">Alex Reed</div>
            <div className="text-muted-foreground leading-tight">Recruiter</div>
          </div>
        </Link>
      </div>
    </header>
  );
}
