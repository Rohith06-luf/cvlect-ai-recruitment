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

        <button className="relative rounded-xl border border-border p-2 hover:bg-white/5 transition" aria-label="Notifications">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-[var(--color-secondary)]" />
        </button>
      </div>
    </header>
  );
}
