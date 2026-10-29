import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Sparkles,
  FileCheck2,
  Cpu,
  ShieldCheck,
  ArrowRight,
  Briefcase,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Landing: React.FC = () => {
  const { isAuthenticated, isCandidate } = useAuth();

  const primaryDashboardPath = isCandidate ? '/candidate/dashboard' : '/recruiter/dashboard';

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <div className="relative min-h-screen bg-[#0a0e1a] text-[#f8fafc] overflow-hidden selection:bg-purple-600/30">
      {/* Dynamic Background Glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-to-tr from-violet-600/20 to-blue-600/20 blur-[130px] pointer-events-none rounded-full" />
      <div className="absolute top-[600px] left-10 w-[500px] h-[500px] bg-indigo-600/10 blur-[150px] pointer-events-none rounded-full" />
      <div className="absolute top-[800px] right-10 w-[450px] h-[450px] bg-cyan-600/10 blur-[130px] pointer-events-none rounded-full" />

      {/* Header Navigation */}
      <header className="relative z-20 max-w-7xl mx-auto px-6 h-20 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-blue-500 p-0.5 shadow-lg shadow-violet-600/30">
            <div className="w-full h-full bg-[#0a0e1a] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-violet-400" />
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xl font-black tracking-tight text-white">CVlect</span>
            <span className="px-1.5 py-0.2 rounded text-[10px] font-bold tracking-wider bg-violet-500/20 text-violet-300 border border-violet-500/30">
              AI
            </span>
          </div>
        </div>

        <nav className="flex items-center gap-4">
          {isAuthenticated ? (
            <Link
              to={primaryDashboardPath}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-sm font-semibold shadow-lg shadow-violet-600/25 transition-all flex items-center gap-2"
            >
              <span>Go to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-slate-300 hover:text-white px-4 py-2 rounded-xl hover:bg-white/5 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-sm font-semibold shadow-lg shadow-violet-600/25 transition-all flex items-center gap-2"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pt-20 pb-24 text-center">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* Badge */}
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-violet-500/30 text-xs font-medium text-violet-300 shadow-[0_0_20px_rgba(124,58,237,0.2)]">
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            <span>Next-Generation Resume Intelligence & Hiring Fair Match</span>
          </motion.div>

          {/* Heading */}
          <motion.h1
            variants={itemVariants}
            className="text-5xl sm:text-7xl font-extrabold tracking-tight text-white leading-[1.1]"
          >
            AI-Powered Resume <br />
            <span className="text-gradient">Intelligence & Fair Matching</span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            variants={itemVariants}
            className="max-w-2xl mx-auto text-lg text-slate-300 leading-relaxed"
          >
            Unlock deep contextual skill parsing, multi-factor applicant compatibility scores, and unbiased career matching powered by cutting-edge neural algorithms.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={itemVariants}
            className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              to="/register?role=candidate"
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-base font-bold shadow-xl shadow-violet-600/30 hover:shadow-violet-600/50 transition-all flex items-center justify-center gap-2.5 transform hover:-translate-y-0.5"
            >
              <FileCheck2 className="w-5 h-5" />
              <span>For Candidates — Analyze Resume</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>

            <Link
              to="/register?role=recruiter"
              className="w-full sm:w-auto px-8 py-4 rounded-2xl glass-panel hover:bg-white/10 text-white text-base font-semibold border border-white/10 hover:border-violet-500/40 transition-all flex items-center justify-center gap-2.5"
            >
              <Briefcase className="w-5 h-5 text-blue-400" />
              <span>For Recruiters — Post & Rank</span>
            </Link>
          </motion.div>

          {/* Trust stats pill */}
          <motion.div
            variants={itemVariants}
            className="pt-10 flex flex-wrap items-center justify-center gap-8 text-xs text-slate-400"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Contextual NLP Extraction</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Explainable Skill Vectors</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Algorithmic Fairness Audits</span>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Feature Cards Grid */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Engineered for Modern Talent Architecture
          </h2>
          <p className="mt-3 text-slate-400 text-base max-w-xl mx-auto">
            Traditional ATS filters drop top talent due to rigid keyword matching. CVlect AI reads context, experience trajectories, and project depth.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1 */}
          <motion.div
            whileHover={{ y: -6 }}
            className="p-7 rounded-3xl glass-panel border border-white/10 relative overflow-hidden group"
          >
            <div className="w-12 h-12 rounded-2xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 mb-6 group-hover:scale-110 transition-transform">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Resume Intelligence</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Automated PDF & DOCX extraction identifying hard skills, domain depth, experience metrics, and missing profile elements.
            </p>
          </motion.div>

          {/* Card 2 */}
          <motion.div
            whileHover={{ y: -6 }}
            className="p-7 rounded-3xl glass-panel border border-white/10 relative overflow-hidden group"
          >
            <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Multi-Factor Matching</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Weighted scoring breakdown evaluating skills, project relevance, career seniority, and education alignment with explainable confidence.
            </p>
          </motion.div>

          {/* Card 3 */}
          <motion.div
            whileHover={{ y: -6 }}
            className="p-7 rounded-3xl glass-panel border border-white/10 relative overflow-hidden group"
          >
            <div className="w-12 h-12 rounded-2xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Fairness & Bias Audits</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Built-in diagnostic disparity metrics and transparency reports designed to combat systemic hiring bias and support objective evaluations.
            </p>
          </motion.div>

          {/* Card 4 */}
          <motion.div
            whileHover={{ y: -6 }}
            className="p-7 rounded-3xl glass-panel border border-white/10 relative overflow-hidden group"
          >
            <div className="w-12 h-12 rounded-2xl bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-6 group-hover:scale-110 transition-transform">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">AI Career Copilot</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Interactive chat assistant to diagnose skill gaps, optimize resumes for specific job requisitions, and answer career queries in real time.
            </p>
          </motion.div>
        </div>
      </section>

      {/* How it works section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20 border-t border-white/5">
        <div className="text-center mb-16">
          <span className="text-xs font-bold tracking-widest text-violet-400 uppercase">Seamless Workflow</span>
          <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-white tracking-tight">
            How CVlect AI Powers The Matching Loop
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <div className="p-8 rounded-3xl glass-panel border border-white/10 relative">
            <div className="w-10 h-10 rounded-xl bg-violet-600 text-white font-black text-sm flex items-center justify-center mb-6 shadow-md shadow-violet-600/40">
              01
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Upload or Post</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Candidates upload resumes in PDF/Word format. Recruiters post structured job descriptions with required skills and qualifications.
            </p>
          </div>

          <div className="p-8 rounded-3xl glass-panel border border-white/10 relative">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-black text-sm flex items-center justify-center mb-6 shadow-md shadow-indigo-600/40">
              02
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Neural Analysis</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              The AI engine normalizes entities, parses technical capabilities, calculates confidence scores, and constructs a holistic vector profile.
            </p>
          </div>

          <div className="p-8 rounded-3xl glass-panel border border-white/10 relative">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white font-black text-sm flex items-center justify-center mb-6 shadow-md shadow-blue-600/40">
              03
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Transparent Matching</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Candidates see matching jobs with missing skill gaps; recruiters receive ranked candidate shortlists with complete algorithmic explanations.
            </p>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 py-20">
        <div className="rounded-3xl p-10 sm:p-14 glass-panel border border-violet-500/30 text-center relative overflow-hidden shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-600/10 via-indigo-600/10 to-blue-600/10 pointer-events-none" />
          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            Ready to upgrade your talent matching?
          </h2>
          <p className="text-base text-slate-300 max-w-xl mx-auto mb-8">
            Experience next-level resume analytics, unbiased hiring workflows, and instant candidate compatibility insights today.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-bold text-sm shadow-lg shadow-violet-600/30 hover:scale-105 transition-all"
            >
              Create Free Account
            </Link>
            <Link
              to="/login"
              className="px-8 py-3.5 rounded-xl glass-input text-slate-300 hover:text-white font-semibold text-sm transition-colors border border-white/10"
            >
              Sign In to Existing Account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-12 px-6 max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="font-semibold text-white">CVlect AI</span>
          <span>— Intelligent Resume Intelligence & Fair Recruitment</span>
        </div>
        <p className="text-slate-400">
          Powered by Explainable NLP & Demographic Parity Diagnostics
        </p>
      </footer>
    </div>
  );
};
