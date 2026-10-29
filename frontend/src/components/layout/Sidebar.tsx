import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  CheckSquare,
  Bot,
  Users,
  PlusCircle,
  LogOut,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, logout, isCandidate } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const candidateLinks = [
    { to: '/candidate/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/candidate/resume', label: 'My Resume', icon: FileText },
    { to: '/candidate/jobs', label: 'Job Browser', icon: Briefcase },
    { to: '/candidate/applications', label: 'Applications', icon: CheckSquare },
    { to: '/candidate/assistant', label: 'AI Career Copilot', icon: Bot, isSpecial: true },
  ];

  const recruiterLinks = [
    { to: '/recruiter/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/recruiter/jobs', label: 'Job Postings', icon: Briefcase },
    { to: '/recruiter/jobs/create', label: 'Post New Job', icon: PlusCircle },
    { to: '/recruiter/candidates', label: 'Candidate Search', icon: Users },
    { to: '/recruiter/assistant', label: 'AI Talent Assistant', icon: Sparkles, isSpecial: true },
  ];

  const links = isCandidate ? candidateLinks : recruiterLinks;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 glass-panel border-r border-white/10 flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-6 border-b border-white/10">
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-blue-500 p-0.5 shadow-lg shadow-violet-600/30 group-hover:scale-105 transition-transform duration-200">
              <div className="w-full h-full bg-[#0a0e1a] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-violet-400 group-hover:rotate-12 transition-transform duration-300" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-lg font-black tracking-tight text-white">CVlect</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-bold tracking-wider bg-violet-500/20 text-violet-300 border border-violet-500/30">
                  AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Smart Talent Intelligence</p>
            </div>
          </NavLink>
        </div>

        {/* Navigation list */}
        <div className="flex-1 py-6 px-3 overflow-y-auto space-y-1.5">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider uppercase text-slate-400">
            {isCandidate ? 'Candidate Portal' : 'Recruiter Workspace'}
          </div>

          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? 'text-white bg-gradient-to-r from-violet-600/30 to-blue-600/20 border border-violet-500/40 shadow-[0_0_15px_rgba(124,58,237,0.2)]'
                      : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        isActive
                          ? 'text-violet-400'
                          : link.isSpecial
                          ? 'text-violet-400'
                          : 'text-slate-400'
                      }`}
                    />
                    <span className="flex-1 truncate">{link.label}</span>
                    {link.isSpecial && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 animate-pulse">
                        AI
                      </span>
                    )}
                    {isActive && (
                      <motion.div
                        layoutId="activeTabIndicator"
                        className="w-1.5 h-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_#a78bfa]"
                      />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-white/10 bg-slate-900/40">
          <div className="flex items-center gap-3 mb-3 p-2 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-blue-600 flex items-center justify-center font-bold text-white text-sm shadow-md">
              {user?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-slate-400 truncate capitalize">{user?.role || 'Guest'}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-white/5 hover:border-rose-500/20 transition-all duration-200 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
