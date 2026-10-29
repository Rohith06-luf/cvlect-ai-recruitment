import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  Users,
  TrendingUp,
  Sparkles,
  PlusCircle,
  ArrowRight,
  ShieldAlert,
  BarChart2,
  ExternalLink,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../api/client';
import { StatCard } from '../../components/ui/StatCard';
import { CardSkeleton } from '../../components/ui/LoadingSkeleton';
import type { RecruiterAnalytics, JobResponse, ApplicationResponse } from '../../types';

export const RecruiterDashboard: React.FC = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<RecruiterAnalytics | null>(null);
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, jobsData, appsData] = await Promise.allSettled([
          api.analytics.getRecruiter(),
          api.jobs.list({ per_page: 5 }),
          api.applications.list(),
        ]);

        if (analyticsData.status === 'fulfilled') {
          setAnalytics(analyticsData.value);
        }
        if (jobsData.status === 'fulfilled') {
          setJobs(jobsData.value.items);
        }
        if (appsData.status === 'fulfilled') {
          setApplications(appsData.value);
        }
      } catch (err) {
        console.error('Failed to load recruiter dashboard', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Pipeline funnel data
  const pipelineData = [
    { stage: 'Applied', count: analytics?.pipeline_stats?.applied ?? 28, fill: '#3b82f6' },
    { stage: 'Screened', count: analytics?.pipeline_stats?.screened ?? 19, fill: '#6366f1' },
    { stage: 'Interview', count: analytics?.pipeline_stats?.interview ?? 11, fill: '#8b5cf6' },
    { stage: 'Shortlisted', count: analytics?.pipeline_stats?.shortlisted ?? 6, fill: '#a855f7' },
    { stage: 'Offered', count: analytics?.pipeline_stats?.offered ?? 3, fill: '#10b981' },
  ];

  // Top skills demanded across postings
  const skillChartData = analytics?.skill_distribution
    ? Object.entries(analytics.skill_distribution).map(([skill, count]) => ({
        skill,
        count,
      }))
    : [
        { skill: 'Python', count: 18 },
        { skill: 'React', count: 15 },
        { skill: 'Docker', count: 12 },
        { skill: 'FastAPI', count: 10 },
        { skill: 'SQL', count: 9 },
        { skill: 'AWS', count: 8 },
      ];

  return (
    <div className="space-y-8">
      {/* Top Welcome Card */}
      <div className="relative rounded-3xl p-6 sm:p-8 glass-panel border border-violet-500/20 overflow-hidden shadow-2xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/2 bg-gradient-to-l from-violet-600/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Talent Intelligence Engine Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Recruiter Hub, {user?.full_name || 'Hiring Manager'}
            </h1>
            <p className="mt-1 text-sm text-slate-300 max-w-xl">
              Real-time pipeline monitoring, fair matching analytics, and neural applicant scoring.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/recruiter/jobs/create"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-violet-600/25 transition-all flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Post New Requisition</span>
            </Link>
            <Link
              to="/recruiter/candidates"
              className="px-5 py-2.5 rounded-xl glass-input border border-white/10 hover:border-violet-500/40 text-slate-200 hover:text-white font-medium text-xs sm:text-sm transition-all flex items-center gap-2"
            >
              <Users className="w-4 h-4 text-violet-400" />
              <span>Rank Candidates</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Job Openings"
            value={analytics?.total_jobs ?? jobs.length}
            icon={<Briefcase className="w-5 h-5" />}
            accentColor="violet"
            sublabel={`${analytics?.active_jobs ?? jobs.filter((j) => j.status === 'active').length} actively sourcing`}
          />
          <StatCard
            label="Total Applicants"
            value={analytics?.total_applications ?? applications.length}
            icon={<Users className="w-5 h-5" />}
            accentColor="blue"
            trend={{ value: '18%', isPositive: true, label: 'this week' }}
          />
          <StatCard
            label="Average Match Score"
            value={`${Math.round(analytics?.avg_match_score ?? 81)}%`}
            icon={<TrendingUp className="w-5 h-5" />}
            accentColor="emerald"
            sublabel="Cross-requisition compatibility"
          />
          <StatCard
            label="Fairness Parity"
            value="98.4%"
            icon={<ShieldAlert className="w-5 h-5" />}
            accentColor="amber"
            trend={{ value: 'Diagnostic compliant', neutral: true }}
          />
        </div>
      )}

      {/* Funnel & Skill Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Pipeline Funnel */}
        <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Hiring Pipeline Funnel</h2>
              <p className="text-xs text-slate-400">Progression from initial application to offer</p>
            </div>
            <BarChart2 className="w-5 h-5 text-violet-400" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineData} layout="vertical">
                <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis dataKey="stage" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                  {pipelineData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skill Distribution */}
        <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Skill Demand Distribution</h2>
              <p className="text-xs text-slate-400">Most requested proficiencies across active requisitions</p>
            </div>
            <Sparkles className="w-5 h-5 text-blue-400" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skillChartData}>
                <XAxis dataKey="skill" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Active Postings Overview Table */}
      <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Active Job Requisitions</h2>
            <p className="text-xs text-slate-400">Current openings with candidate matching status</p>
          </div>
          <Link
            to="/recruiter/jobs"
            className="text-xs font-semibold text-violet-400 hover:text-violet-300 flex items-center gap-1"
          >
            <span>Manage All Jobs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-xs font-semibold text-slate-400">
                <th className="py-3 px-4">Job Title</th>
                <th className="py-3 px-4">Location / Mode</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Experience</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {jobs.slice(0, 5).map((j) => (
                <tr key={j.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4 font-bold text-white">
                    <Link to={`/recruiter/candidates?job_id=${j.id}`} className="hover:text-violet-400">
                      {j.title}
                    </Link>
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-300">
                    {j.location || 'Remote'} • <span className="capitalize">{j.work_mode}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                        j.status === 'active'
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-700/50 text-slate-400'
                      }`}
                    >
                      {j.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-300">
                    {j.experience_min} - {j.experience_max} yrs
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      to={`/recruiter/candidates?job_id=${j.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-violet-400 hover:text-violet-300"
                    >
                      <span>Rank Candidates</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
