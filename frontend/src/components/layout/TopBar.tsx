import React from 'react';
import { Menu, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface TopBarProps {
  onToggleSidebar: () => void;
  title?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar, title }) => {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 h-16 glass-panel border-b border-white/10 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/5 transition-colors"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {title && (
          <h1 className="text-lg font-bold text-white tracking-tight hidden sm:block">
            {title}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        {/* AI Engine Status Pill */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-violet-950/40 border border-violet-500/20 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] animate-pulse" />
          <span className="text-slate-300 font-medium">CVlect Engine v2.4</span>
          <span className="text-[10px] text-violet-300 bg-violet-500/20 px-1.5 py-0.5 rounded font-mono">
            Hybrid Match
          </span>
        </div>

        {/* Fairness verified badge */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-950/30 border border-blue-500/20 text-xs text-blue-300">
          <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
          <span>Fair Match Active</span>
        </div>

        {/* User initials bubble */}
        <div className="flex items-center gap-2 pl-2 border-l border-white/10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-blue-500 flex items-center justify-center text-white text-xs font-bold shadow-md">
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold text-white leading-none">{user?.full_name}</p>
            <p className="text-[10px] text-slate-400 leading-tight capitalize mt-0.5">
              {user?.role}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};
