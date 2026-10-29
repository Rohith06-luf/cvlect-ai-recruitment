import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();

  const from = (location.state as any)?.from?.pathname;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!email || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!', 'You have successfully signed in.');
      
      // Determine redirection target based on role or previous location
      const savedUserStr = localStorage.getItem('user');
      const savedUser = savedUserStr ? JSON.parse(savedUserStr) : null;
      if (from) {
        navigate(from, { replace: true });
      } else if (savedUser?.role === 'recruiter') {
        navigate('/recruiter/dashboard', { replace: true });
      } else {
        navigate('/candidate/dashboard', { replace: true });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Login failed. Please check your credentials.';
      setErrorMsg(msg);
      toast.error('Authentication Failed', msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoCandidate = () => {
    setEmail('candidate@cvlect.ai');
    setPassword('password123');
  };

  const fillDemoRecruiter = () => {
    setEmail('recruiter@cvlect.ai');
    setPassword('password123');
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-[#f8fafc] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-to-tr from-violet-600/20 to-blue-600/20 blur-[120px] pointer-events-none rounded-full" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <Link to="/" className="inline-flex items-center gap-3 group mb-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-blue-500 p-0.5 shadow-xl shadow-violet-600/30 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#0a0e1a] rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-violet-400" />
            </div>
          </div>
          <span className="text-2xl font-black tracking-tight text-white">CVlect AI</span>
        </Link>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">Sign in to your account</h2>
        <p className="mt-2 text-sm text-slate-400">
          Or{' '}
          <Link to="/register" className="font-semibold text-violet-400 hover:text-violet-300 underline">
            create a new account
          </Link>
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4"
      >
        <div className="glass-panel border border-white/10 py-8 px-6 sm:px-10 rounded-3xl shadow-2xl space-y-6">
          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-violet-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div className="pt-4 border-t border-white/10 text-center">
            <p className="text-xs text-slate-400 mb-2 font-medium">Quick Demo Accounts:</p>
            <div className="flex gap-2 justify-center">
              <button
                type="button"
                onClick={fillDemoCandidate}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-[11px] text-slate-300 border border-white/10 transition-colors"
              >
                Candidate Demo
              </button>
              <button
                type="button"
                onClick={fillDemoRecruiter}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-[11px] text-slate-300 border border-white/10 transition-colors"
              >
                Recruiter Demo
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
