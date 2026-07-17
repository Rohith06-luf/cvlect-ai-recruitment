import { Link, useRouterState } from "@tanstack/react-router";
import { useState, type ComponentType } from "react";
import { ChevronsLeft, ChevronsRight, LogOut } from "lucide-react";

export type SidebarItem = {
  label: string;
  to: string;
  icon: ComponentType<{ className?: string }>;
};

export function Sidebar({
  items,
  brand = "CVlect",
  footerTo = "/",
}: {
  items: SidebarItem[];
  brand?: string;
  footerTo?: string;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside
      className="hidden md:flex flex-col shrink-0 h-screen sticky top-0 transition-all duration-300 border-r border-border/60"
      style={{
        width: collapsed ? 80 : 250,
        background: "var(--color-sidebar)",
      }}
    >
      <div className="flex items-center justify-between px-5 h-16 border-b border-white/5">
        {!collapsed && (
          <Link to="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-white/10 grid place-items-center font-bold text-white">C</div>
            <span className="font-semibold tracking-tight">{brand}</span>
          </Link>
        )}
        {collapsed && (
          <div className="h-8 w-8 rounded-xl bg-white/10 grid place-items-center font-bold text-white mx-auto">C</div>
        )}
        <button
          onClick={() => setCollapsed((v) => !v)}
          className="text-muted-foreground hover:text-white transition"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {items.map((item) => {
          const active = pathname === item.to || pathname.startsWith(item.to + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-300 ${
                active
                  ? "bg-white/10 text-white"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-white/5">
        <Link
          to={footerTo}
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted-foreground hover:text-white hover:bg-white/5 transition"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Sign out</span>}
        </Link>
      </div>
    </aside>
  );
}
