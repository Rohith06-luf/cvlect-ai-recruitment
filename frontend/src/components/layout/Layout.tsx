import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Map route to title
  const getPageTitle = (pathname: string): string => {
    if (pathname.includes('/candidate/dashboard')) return 'Candidate Dashboard';
    if (pathname.includes('/candidate/resume')) return 'Resume Intelligence & Extraction';
    if (pathname.includes('/candidate/jobs/')) return 'Job Opportunity Details';
    if (pathname.includes('/candidate/jobs')) return 'Smart Job Explorer';
    if (pathname.includes('/candidate/applications')) return 'Application Tracker';
    if (pathname.includes('/candidate/assistant')) return 'AI Career Copilot';
    if (pathname.includes('/recruiter/dashboard')) return 'Recruiter Talent Dashboard';
    if (pathname.includes('/recruiter/jobs/create')) return 'Post New Job Requisition';
    if (pathname.includes('/recruiter/jobs')) return 'Active Job Postings';
    if (pathname.includes('/recruiter/candidates')) return 'AI Candidate Ranking & Search';
    if (pathname.includes('/recruiter/assistant')) return 'AI Talent Copilot';
    return 'CVlect AI';
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#f8fafc] flex">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <TopBar
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          title={getPageTitle(location.pathname)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
